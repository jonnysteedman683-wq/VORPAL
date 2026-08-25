"""
OMNICORE Event Bus v1.0 — Typed Emission Engine
Decoupled publish/subscribe bus with schema-enforced typed events and
per-handler error isolation.

Stolen from:
  - OMNICORE-A1/src/lib/event_bus.ts (typed event dispatch with error isolation)
  - markus_mesh.py (bounded audit log, port-free in-process fan-out)
  - hive_swarm_adapter.ts (wildcard subscription fan-out)
  - p2p_state_registry.py (dataclass envelope + SHA integrity signature)

Features:
  - Schema-registered event types: every emit is validated against a declared
    payload schema (field -> type). Malformed emissions are isolated, never
    silently dropped or allowed to crash the bus.
  - Error isolation: a handler that raises is caught, recorded, and does NOT
    prevent sibling handlers or the emitting caller from completing.
  - Wildcard ("*") subscriptions receive every typed event.
  - Bounded audit log (default 500) for replay/forensics.
  - Thread-safe dispatch via a re-entrant lock.

Zero-dependency Python stdlib implementation.
"""
import time
import uuid
import hashlib
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class EventEnvelope:
    """Wire format for every emitted event.

    Stolen from: event_bus.ts — TypedEvent envelope + p2p_state_registry.StateDelta
    (delta_id / signature integrity pattern).
    """
    event_id: str
    event_type: str
    source: str
    timestamp: float
    payload: Dict[str, Any]
    schema_version: int = 1
    signature: str = ""  # SHA-256[:16] over (event_type|source|payload)

    def signed(self) -> "EventEnvelope":
        raw = f"{self.event_type}|{self.source}|{self.timestamp}|{self.payload!r}"
        self.signature = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self


@dataclass
class HandlerResult:
    """Outcome of a single handler invocation for one emission."""
    handler_name: str
    ok: bool
    error: Optional[str] = None


@dataclass
class EmitResult:
    """Aggregate result of an emit() call across all matched handlers."""
    event_id: str
    event_type: str
    delivered: int             # handlers that ran without raising
    errored: int               # handlers that raised (isolated)
    isolated_errors: List[HandlerResult] = field(default_factory=list)
    skipped: bool = False      # True when schema validation failed (no dispatch)
    validation_error: Optional[str] = None


class EventBus:
    """
    Typed, isolation-safe in-process event bus.

    STOLE FROM: event_bus.ts — register/emit/on with typed payloads
    STOLE FROM: p2p_state_registry.py — bounded log + dataclass envelopes
    STOLE FROM: safety_gate.ts — fail-closed validation (invalid => rejected)
    """

    def __init__(self, source: str = "event_bus", max_log: int = 500):
        self._source = source
        self._schemas: Dict[str, Dict[str, type]] = {}
        self._required: Dict[str, Set[str]] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._log: List[EventEnvelope] = []
        self._max_log = max(10, max_log)
        self._lock = threading.RLock()

    # ---- schema registry -------------------------------------------------

    def register_type(self, event_type: str, fields: Dict[str, type],
                      required: Optional[List[str]] = None) -> None:
        """Declare a typed event. `fields` maps payload key -> allowed type.

        A payload validates iff every key is present in `fields`, every value
        matches the declared type, and all `required` keys are present.
        """
        if not event_type or not isinstance(event_type, str):
            raise ValueError("event_type must be a non-empty string")
        if not fields:
            raise ValueError("fields schema must declare at least one key")
        for key, t in fields.items():
            if not isinstance(t, type):
                raise ValueError(f"field {key!r} must map to a type, got {t!r}")
        with self._lock:
            self._schemas[event_type] = dict(fields)
            self._required[event_type] = set(required or [])

    def type_registered(self, event_type: str) -> bool:
        with self._lock:
            return event_type in self._schemas

    # ---- subscription -----------------------------------------------------

    def subscribe(self, event_type: str, handler: Callable,
                  name: Optional[str] = None) -> str:
        """Subscribe `handler` to `event_type` (or "*" for all types).

        Returns a stable subscription id (handler __name__ or provided name).
        """
        if not callable(handler):
            raise ValueError("handler must be callable")
        sid = name or getattr(handler, "__name__", "handler")
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(handler)
        return sid

    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        with self._lock:
            subs = self._subscribers.get(event_type)
            if not subs:
                return False
            before = len(subs)
            self._subscribers[event_type] = [h for h in subs if h is not handler]
            return len(self._subscribers[event_type]) < before

    def subscriber_count(self, event_type: str) -> int:
        with self._lock:
            return len(self._subscribers.get(event_type, []))

    # ---- validation -------------------------------------------------------

    def validate_payload(self, event_type: str,
                         payload: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Return (ok, error). Pure: never dispatches."""
        if not isinstance(payload, dict):
            return False, f"payload must be a dict, got {type(payload).__name__}"
        with self._lock:
            schema = self._schemas.get(event_type)
        if schema is None:
            return False, f"unregistered event type {event_type!r}"
        required = self._required.get(event_type, set())
        for key in required:
            if key not in payload:
                return False, f"missing required field {key!r}"
        for key, value in payload.items():
            if key not in schema:
                return False, f"unknown field {key!r} for type {event_type!r}"
            expected = schema[key]
            # Container/Union tolerance: accept subtypes and None where allowed.
            if value is None and expected is not type(None):
                return False, f"field {key!r} is None but type {expected.__name__} required"
            if not isinstance(value, expected):
                return False, (
                    f"field {key!r} expected {expected.__name__}, "
                    f"got {type(value).__name__}"
                )
        return True, None

    # ---- emission ---------------------------------------------------------

    def emit(self, event_type: str, payload: Dict[str, Any],
             source: Optional[str] = None, *,
             raise_on_invalid: bool = False) -> EmitResult:
        """Validate, log, and fan-out an event to all matched handlers.

        Error isolation: each handler is invoked inside its own try/except. A
        raising handler is recorded in `isolated_errors` and does NOT stop
        sibling handlers or propagate to the caller.

        If validation fails: when `raise_on_invalid` is True the caller gets a
        ValueError; otherwise the event is skipped (not dispatched) and a
        skipped EmitResult is returned.
        """
        ok, err = self.validate_payload(event_type, payload)
        env = EventEnvelope(
            event_id=f"EV-{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            source=source or self._source,
            timestamp=time.time(),
            payload=dict(payload),
        ).signed()

        if not ok:
            if raise_on_invalid:
                raise ValueError(f"event {event_type!r} rejected: {err}")
            return EmitResult(
                event_id=env.event_id, event_type=event_type,
                delivered=0, errored=0, skipped=True, validation_error=err,
            )

        with self._lock:
            self._log.append(env)
            if len(self._log) > self._max_log:
                self._log = self._log[-self._max_log:]
            handlers = list(self._subscribers.get(event_type, []))
            handlers += list(self._subscribers.get("*", []))

        delivered = 0
        isolated: List[HandlerResult] = []
        for h in handlers:
            hname = getattr(h, "__name__", "handler")
            try:
                h(env)
                delivered += 1
            except Exception as exc:  # isolation boundary
                isolated.append(HandlerResult(handler_name=hname, ok=False,
                                             error=f"{type(exc).__name__}: {exc}"))

        return EmitResult(
            event_id=env.event_id, event_type=event_type,
            delivered=delivered, errored=len(isolated),
            isolated_errors=isolated, skipped=False,
        )

    # ---- introspection ----------------------------------------------------

    def replay(self, event_type: Optional[str] = None,
               limit: Optional[int] = None) -> List[EventEnvelope]:
        """Return a read-only copy of the audit log (most-recent last)."""
        with self._lock:
            items = list(self._log)
        if event_type is not None:
            items = [e for e in items if e.event_type == event_type]
        if limit is not None:
            items = items[-limit:]
        return items

    def audit_log(self) -> Dict[str, Any]:
        with self._lock:
            types_seen: Dict[str, int] = {}
            for e in self._log:
                types_seen[e.event_type] = types_seen.get(e.event_type, 0) + 1
            return {
                "source": self._source,
                "logged_events": len(self._log),
                "max_log": self._max_log,
                "registered_types": sorted(self._schemas.keys()),
                "subscribed_types": sorted(self._subscribers.keys()),
                "events_by_type": types_seen,
            }

    def clear(self) -> None:
        with self._lock:
            self._log.clear()
            self._subscribers.clear()
            self._schemas.clear()
            self._required.clear()


# Convenience factory matching house style (mirrors PeerRegistry entrypoint).
def create_event_bus(source: str = "event_bus", max_log: int = 500) -> EventBus:
    return EventBus(source=source, max_log=max_log)
