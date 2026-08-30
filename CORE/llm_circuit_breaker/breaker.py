"""Circuit breaker state machine for LLM API calls.

[◈VORPAL◈] Adapted from MukundaKatta/llm-circuit-breaker-py (MIT).
Thread-safe Closed/Open/HalfOpen state machine for provider-aware routing.

Retry libraries handle individual transient failures. This handles the
case where the provider is clearly down for everyone: stop calling for a
window, let one probe through, and re-close on success.

    from llm_circuit_breaker import CircuitBreaker, BreakerConfig, CircuitOpenError

    cb = CircuitBreaker(BreakerConfig(failure_threshold=5, recovery_timeout_s=30.0))

State machine:
    * Closed - calls pass through, failures are counted.
    * Open - after `failure_threshold` consecutive counted failures, all
      calls reject with `CircuitOpenError` until `recovery_timeout_s`
      elapses.
    * HalfOpen - one probe call is allowed through. Success closes the
      breaker; failure re-opens it for another window.

`AsyncCircuitBreaker` mirrors the sync API for asyncio code paths.

Sibling to the Rust crate `llm-circuit-breaker`.
"""

from __future__ import annotations

import asyncio
import inspect
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

T = TypeVar("T")


class BreakerState(str, Enum):
    """Observable state of the breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised by `call` when the breaker is Open and short-circuits the call."""

    def __init__(self, opened_at: float | None = None, recovery_timeout_s: float | None = None):
        self.opened_at = opened_at
        self.recovery_timeout_s = recovery_timeout_s
        if opened_at is not None and recovery_timeout_s is not None:
            remaining = max(0.0, (opened_at + recovery_timeout_s) - time.monotonic())
            super().__init__(f"circuit breaker is open; retry in ~{remaining:.2f}s")
        else:
            super().__init__("circuit breaker is open; call short-circuited")


@dataclass(frozen=True)
class BreakerConfig:
    """Configuration for a `CircuitBreaker` or `AsyncCircuitBreaker`.

    Attributes:
        failure_threshold: consecutive counted failures before the breaker
            opens. Defaults to 5.
        recovery_timeout_s: how long to stay in Open before allowing a probe
            into HalfOpen. Defaults to 30.0 seconds.
        half_open_max_calls: max concurrent probe calls in HalfOpen.
            Defaults to 1.
    """

    failure_threshold: int = 5
    recovery_timeout_s: float = 30.0
    half_open_max_calls: int = 1

    def __post_init__(self) -> None:
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if self.recovery_timeout_s < 0:
            raise ValueError("recovery_timeout_s must be >= 0")
        if self.half_open_max_calls < 1:
            raise ValueError("half_open_max_calls must be >= 1")


@dataclass(frozen=True)
class BreakerStats:
    """Point-in-time snapshot of breaker counters."""

    state: BreakerState
    failure_count: int
    opened_at: float | None
    total_calls: int
    total_successes: int
    total_failures: int
    total_short_circuits: int


def _count_everything(_err: BaseException) -> bool:
    """Default `should_count`: every error counts as a service failure."""
    return True


@dataclass
class _Inner:
    """Mutable breaker state. Guarded by the caller's lock."""

    state: BreakerState = BreakerState.CLOSED
    failure_count: int = 0
    opened_at: float | None = None
    half_open_in_flight: int = 0
    # observability counters
    total_calls: int = 0
    total_successes: int = 0
    total_failures: int = 0
    total_short_circuits: int = 0


class CircuitBreaker:
    """Thread-safe circuit breaker.

    Wraps a configurable failure threshold and recovery timeout. Use
    `CircuitBreaker.call` to wrap any callable; success in any state
    closes the breaker, counted failures in Closed (after threshold) or
    HalfOpen flip it to Open.

    Thread safety: state transitions are guarded by `threading.RLock`.
    The wrapped function itself runs OUTSIDE the lock so a slow call
    never blocks other threads' breaker decisions.
    """

    def __init__(self, config: BreakerConfig | None = None) -> None:
        self._config = config or BreakerConfig()
        self._inner = _Inner()
        self._lock = threading.RLock()

    # ---- public read-only views ----

    @property
    def config(self) -> BreakerConfig:
        """Return the breaker's config."""
        return self._config

    @property
    def state(self) -> BreakerState:
        """Current state. Triggers an Open -> HalfOpen check if the
        recovery window has elapsed."""
        with self._lock:
            self._maybe_half_open()
            return self._inner.state

    @property
    def failure_count(self) -> int:
        """Current consecutive counted failure count."""
        with self._lock:
            return self._inner.failure_count

    def stats(self) -> BreakerStats:
        """Snapshot of current state + observability counters."""
        with self._lock:
            self._maybe_half_open()
            return BreakerStats(
                state=self._inner.state,
                failure_count=self._inner.failure_count,
                opened_at=self._inner.opened_at,
                total_calls=self._inner.total_calls,
                total_successes=self._inner.total_successes,
                total_failures=self._inner.total_failures,
                total_short_circuits=self._inner.total_short_circuits,
            )

    # ---- mutators ----

    def reset(self) -> None:
        """Force the breaker back to Closed and clear the failure count.
        Observability counters are NOT cleared."""
        with self._lock:
            self._inner.state = BreakerState.CLOSED
            self._inner.failure_count = 0
            self._inner.opened_at = None
            self._inner.half_open_in_flight = 0

    def call(
        self,
        fn: Callable[..., T],
        *args: Any,
        should_count: Callable[[BaseException], bool] | None = None,
        **kwargs: Any,
    ) -> T:
        """Run `fn(*args, **kwargs)` under the breaker.

        Raises `CircuitOpenError` if the breaker is Open (or HalfOpen
        and the probe budget is full). Otherwise the inner call's return
        value or exception propagates.

        `should_count(exc) -> bool` decides whether a raised exception
        counts as a service failure. Default counts everything. Narrow it
        to provider-side failures so caller bugs don't poison the
        breaker.
        """
        check = should_count or _count_everything
        self._before_call()
        try:
            result = fn(*args, **kwargs)
        except BaseException as exc:
            self._on_failure(exc, check)
            raise
        self._on_success()
        return result

    # ---- internals ----

    def _before_call(self) -> None:
        """Admission check. Raises CircuitOpenError if blocked."""
        with self._lock:
            self._maybe_half_open()
            self._inner.total_calls += 1
            if self._inner.state == BreakerState.OPEN:
                self._inner.total_short_circuits += 1
                raise CircuitOpenError(
                    opened_at=self._inner.opened_at,
                    recovery_timeout_s=self._config.recovery_timeout_s,
                )
            if self._inner.state == BreakerState.HALF_OPEN:
                if self._inner.half_open_in_flight >= self._config.half_open_max_calls:
                    self._inner.total_short_circuits += 1
                    raise CircuitOpenError(
                        opened_at=self._inner.opened_at,
                        recovery_timeout_s=self._config.recovery_timeout_s,
                    )
                self._inner.half_open_in_flight += 1

    def _on_success(self) -> None:
        with self._lock:
            self._inner.total_successes += 1
            if self._inner.state == BreakerState.HALF_OPEN:
                self._inner.half_open_in_flight = max(0, self._inner.half_open_in_flight - 1)
            # any success closes the breaker
            self._inner.state = BreakerState.CLOSED
            self._inner.failure_count = 0
            self._inner.opened_at = None

    def _on_failure(
        self, exc: BaseException, should_count: Callable[[BaseException], bool]
    ) -> None:
        with self._lock:
            self._inner.total_failures += 1
            was_half_open = self._inner.state == BreakerState.HALF_OPEN
            if was_half_open:
                self._inner.half_open_in_flight = max(0, self._inner.half_open_in_flight - 1)
            if not should_count(exc):
                # uncounted error: leave failure_count alone, stay in
                # current state (HalfOpen probes don't re-open on
                # uncounted failures either)
                return
            self._inner.failure_count += 1
            if was_half_open or self._inner.failure_count >= self._config.failure_threshold:
                self._inner.state = BreakerState.OPEN
                self._inner.opened_at = time.monotonic()

    def _maybe_half_open(self) -> None:
        """Caller must hold the lock. Promote Open -> HalfOpen if the
        recovery window has elapsed."""
        if self._inner.state != BreakerState.OPEN:
            return
        if self._inner.opened_at is None:
            return
        if (time.monotonic() - self._inner.opened_at) >= self._config.recovery_timeout_s:
            self._inner.state = BreakerState.HALF_OPEN
            self._inner.half_open_in_flight = 0


class AsyncCircuitBreaker:
    """Asyncio-friendly circuit breaker.

    Same semantics as `CircuitBreaker` but the critical section uses
    `asyncio.Lock`. `call` accepts either an async or a sync callable;
    sync callables are invoked directly (not run in a thread).
    """

    def __init__(self, config: BreakerConfig | None = None) -> None:
        self._config = config or BreakerConfig()
        self._inner = _Inner()
        self._lock = asyncio.Lock()

    @property
    def config(self) -> BreakerConfig:
        """Return the breaker's config."""
        return self._config

    async def get_state(self) -> BreakerState:
        """Current state. Triggers an Open -> HalfOpen check if the
        recovery window has elapsed."""
        async with self._lock:
            self._maybe_half_open()
            return self._inner.state

    async def get_failure_count(self) -> int:
        """Current consecutive counted failure count."""
        async with self._lock:
            return self._inner.failure_count

    async def stats(self) -> BreakerStats:
        """Snapshot of current state + observability counters."""
        async with self._lock:
            self._maybe_half_open()
            return BreakerStats(
                state=self._inner.state,
                failure_count=self._inner.failure_count,
                opened_at=self._inner.opened_at,
                total_calls=self._inner.total_calls,
                total_successes=self._inner.total_successes,
                total_failures=self._inner.total_failures,
                total_short_circuits=self._inner.total_short_circuits,
            )

    async def reset(self) -> None:
        """Force the breaker back to Closed and clear the failure count.
        Observability counters are NOT cleared."""
        async with self._lock:
            self._inner.state = BreakerState.CLOSED
            self._inner.failure_count = 0
            self._inner.opened_at = None
            self._inner.half_open_in_flight = 0

    async def call(
        self,
        fn: Callable[..., T | Awaitable[T]],
        *args: Any,
        should_count: Callable[[BaseException], bool] | None = None,
        **kwargs: Any,
    ) -> T:
        """Run `fn(*args, **kwargs)` under the breaker.

        If `fn` returns an awaitable it is awaited. Sync callables are
        invoked directly.

        Raises `CircuitOpenError` if the breaker is Open or the HalfOpen
        probe budget is full.
        """
        check = should_count or _count_everything
        await self._before_call()
        try:
            result = fn(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
        except BaseException as exc:
            await self._on_failure(exc, check)
            raise
        await self._on_success()
        return result  # type: ignore[return-value]

    # ---- internals (mirror sync, async lock) ----

    async def _before_call(self) -> None:
        async with self._lock:
            self._maybe_half_open()
            self._inner.total_calls += 1
            if self._inner.state == BreakerState.OPEN:
                self._inner.total_short_circuits += 1
                raise CircuitOpenError(
                    opened_at=self._inner.opened_at,
                    recovery_timeout_s=self._config.recovery_timeout_s,
                )
            if self._inner.state == BreakerState.HALF_OPEN:
                if self._inner.half_open_in_flight >= self._config.half_open_max_calls:
                    self._inner.total_short_circuits += 1
                    raise CircuitOpenError(
                        opened_at=self._inner.opened_at,
                        recovery_timeout_s=self._config.recovery_timeout_s,
                    )
                self._inner.half_open_in_flight += 1

    async def _on_success(self) -> None:
        async with self._lock:
            self._inner.total_successes += 1
            if self._inner.state == BreakerState.HALF_OPEN:
                self._inner.half_open_in_flight = max(0, self._inner.half_open_in_flight - 1)
            self._inner.state = BreakerState.CLOSED
            self._inner.failure_count = 0
            self._inner.opened_at = None

    async def _on_failure(
        self, exc: BaseException, should_count: Callable[[BaseException], bool]
    ) -> None:
        async with self._lock:
            self._inner.total_failures += 1
            was_half_open = self._inner.state == BreakerState.HALF_OPEN
            if was_half_open:
                self._inner.half_open_in_flight = max(0, self._inner.half_open_in_flight - 1)
            if not should_count(exc):
                return
            self._inner.failure_count += 1
            if was_half_open or self._inner.failure_count >= self._config.failure_threshold:
                self._inner.state = BreakerState.OPEN
                self._inner.opened_at = time.monotonic()

    def _maybe_half_open(self) -> None:
        """Caller must hold the lock."""
        if self._inner.state != BreakerState.OPEN:
            return
        if self._inner.opened_at is None:
            return
        if (time.monotonic() - self._inner.opened_at) >= self._config.recovery_timeout_s:
            self._inner.state = BreakerState.HALF_OPEN
            self._inner.half_open_in_flight = 0


def guard(
    breaker: CircuitBreaker | AsyncCircuitBreaker,
    *,
    should_count: Callable[[BaseException], bool] | None = None,
):
    """Decorator form of `breaker.call`.

    Wrap a function so every call goes through the breaker without
    sprinkling `breaker.call(fn, ...)` at the call site:

        cb = CircuitBreaker()

        @guard(cb, should_count=predicates.anthropic)
        def chat(prompt):
            return client.messages.create(...)

        chat("hello")  # short-circuits with CircuitOpenError if cb is open

    Works with both `CircuitBreaker` and `AsyncCircuitBreaker`; for the
    async breaker the wrapped function is awaited.  Sync callables wrapped
    on an `AsyncCircuitBreaker` decorator return a coroutine (matching the
    async breaker's `.call` semantics).
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if isinstance(breaker, AsyncCircuitBreaker):
            async def async_wrapper(*args: Any, **kwargs: Any):
                return await breaker.call(fn, *args, should_count=should_count, **kwargs)

            async_wrapper.__wrapped__ = fn  # type: ignore[attr-defined]
            async_wrapper.__name__ = getattr(fn, "__name__", "guarded")
            async_wrapper.__doc__ = fn.__doc__
            return async_wrapper

        def sync_wrapper(*args: Any, **kwargs: Any):
            return breaker.call(fn, *args, should_count=should_count, **kwargs)

        sync_wrapper.__wrapped__ = fn  # type: ignore[attr-defined]
        sync_wrapper.__name__ = getattr(fn, "__name__", "guarded")
        sync_wrapper.__doc__ = fn.__doc__
        return sync_wrapper

    return decorator


__all__ = [
    "AsyncCircuitBreaker",
    "BreakerConfig",
    "BreakerState",
    "BreakerStats",
    "CircuitBreaker",
    "CircuitOpenError",
    "guard",
]
