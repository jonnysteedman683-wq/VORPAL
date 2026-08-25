#!/usr/bin/env python3
"""ARK Cost Ledger — adapted from OMNICORE hive-core/src/lib/cost_ledger.py

Borrowed concepts:
- Per-tier budget quotas
- Multi-dimensional cost vector
- EMA trend detection
- Alarm escalation: NORMAL → SOFT_WARNING → HARD_WARNING → EXCEEDED
- Cross-tier borrowing with authority weights

ARK mapping:
- OMNICORE A1/A2/A3/A4 → ARK tier_0_apex / tier_1_active / tier_2_stagnant / tier_3_archived
"""

from __future__ import annotations

import math
import time
import json
import os
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from collections import deque


class LedgerCorruptionError(Exception):
    """Raised when persisted ledger state cannot be safely recovered."""


class AlarmLevel(Enum):
    NORMAL = "normal"
    SOFT_WARNING = "soft_warn"
    HARD_WARNING = "hard_warn"
    EXCEEDED = "exceeded"


@dataclass
class ArkCostEntry:
    tier: str
    token_count: int
    model_cost_per_1k: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class TierQuota:
    tier: str
    daily_budget_usd: float
    consumed_usd: float = 0.0
    priority_weight: float = 1.0
    borrow_allowed: bool = True
    borrowed_from: Dict[str, float] = field(default_factory=dict)
    borrowed_to: Dict[str, float] = field(default_factory=dict)


class ArkCostLedger:
    AUTHORITY_WEIGHTS = {
        "tier_0_apex": 1.3,
        "tier_1_active": 1.0,
        "tier_2_stagnant": 0.8,
        "tier_3_archived": 0.5,
    }

    SOFT_WARNING_THRESHOLD = 0.80
    HARD_WARNING_THRESHOLD = 0.95
    EXCEEDED_THRESHOLD = 1.00

    BORROW_LIMITS = {
        "tier_0_apex": {"tier_1_active": 0.5, "tier_2_stagnant": 0.3, "tier_3_archived": 0.2},
        "tier_1_active": {"tier_2_stagnant": 0.4, "tier_3_archived": 0.2},
        "tier_2_stagnant": {"tier_3_archived": 0.3, "tier_1_active": 0.15},
        "tier_3_archived": {"tier_2_stagnant": 0.2, "tier_1_active": 0.1},
    }

    def __init__(self, daily_budget_usd: float = 10.0, tiers: Optional[List[str]] = None):
        self._budget_usd = daily_budget_usd
        self._tiers = tiers or ["tier_0_apex", "tier_1_active", "tier_2_stagnant", "tier_3_archived"]
        self._budgets: Dict[str, TierQuota] = {}
        self._entries: deque = deque(maxlen=10000)
        self._alarm_callbacks: List[Callable] = []
        self._ema_factor = 0.15
        self._ema_costs: Dict[str, float] = {}
        # Reentrant so lock-holding methods may call _check_alarm/_export_dict.
        # Closes [ERR_LEDGER_RACE]: `consumed_usd += cost` and the borrow
        # check-then-act were unsynchronised (previously passing at 200 ops
        # only by GIL luck -- ARK/VERIFICATION_LOG.md:142-143).
        self._lock = threading.RLock()

        per_layer = daily_budget_usd / len(self._tiers)
        for tier in self._tiers:
            self._budgets[tier] = TierQuota(
                tier=tier,
                daily_budget_usd=per_layer,
                priority_weight=self.AUTHORITY_WEIGHTS.get(tier, 1.0),
            )

    def record_cost(self, entry: ArkCostEntry) -> AlarmLevel:
        tier = entry.tier if entry.tier in self._budgets else "tier_1_active"
        try:
            cost_usd = float((entry.token_count / 1000.0) * entry.model_cost_per_1k)
        except Exception:
            cost_usd = 0.0
        if not math.isfinite(cost_usd) or cost_usd < 0.0:
            cost_usd = 0.0

        with self._lock:
            self._entries.append(entry)
            budget = self._budgets[tier]
            budget.consumed_usd += cost_usd

            old_ema = self._ema_costs.get(tier, cost_usd)
            next_ema = old_ema * (1 - self._ema_factor) + cost_usd * (self._ema_factor)
            self._ema_costs[tier] = next_ema if math.isfinite(next_ema) else old_ema

            level = self._check_alarm(tier)

        # Callbacks run OUTSIDE the lock: a callback that re-enters the ledger
        # from another thread must not be able to deadlock the accumulator.
        if level != AlarmLevel.NORMAL:
            self._trigger_alarm(tier, level, budget)
        return level

    def _check_alarm(self, tier: str) -> AlarmLevel:
        budget = self._budgets[tier]
        usage_ratio = budget.consumed_usd / budget.daily_budget_usd if budget.daily_budget_usd > 0 else 0.0
        if not math.isfinite(usage_ratio):
            usage_ratio = 0.0
        if usage_ratio >= self.EXCEEDED_THRESHOLD:
            return AlarmLevel.EXCEEDED
        if usage_ratio >= self.HARD_WARNING_THRESHOLD:
            return AlarmLevel.HARD_WARNING
        if usage_ratio >= self.SOFT_WARNING_THRESHOLD:
            return AlarmLevel.SOFT_WARNING
        return AlarmLevel.NORMAL

    def _trigger_alarm(self, tier: str, level: AlarmLevel, budget: TierQuota) -> None:
        for callback in self._alarm_callbacks:
            try:
                callback(tier, level, budget)
            except Exception:
                pass

    def register_alarm(self, callback: Callable) -> None:
        self._alarm_callbacks.append(callback)

    def attempt_borrow(self, tier: str, amount: float) -> float:
        if tier not in self.BORROW_LIMITS or tier not in self._budgets:
            return 0.0
        if not math.isfinite(amount) or amount <= 0:
            return 0.0
        # Whole borrow transaction is atomic: `available = daily_budget_usd -
        # consumed_usd` is a check-then-act, so two concurrent borrowers could
        # each pass the check and over-draw the donor tier (total-budget
        # conservation broken). Held under the same lock as record_cost.
        with self._lock:
            budget = self._budgets[tier]
            total_borrowed = 0.0
            others = sorted(
                [(l, b) for l, b in self._budgets.items() if l != tier],
                key=lambda x: x[1].priority_weight,
                reverse=True,
            )
            for other_tier, other_budget in others:
                if other_tier not in self.BORROW_LIMITS.get(tier, {}):
                    continue
                if other_budget.consumed_usd >= other_budget.daily_budget_usd:
                    continue
                limit_fraction = self.BORROW_LIMITS[tier].get(other_tier, 0.0)
                available = other_budget.daily_budget_usd - other_budget.consumed_usd
                max_borrow = available * limit_fraction
                can_borrow = min(max_borrow, amount - total_borrowed)
                if can_borrow > 0:
                    other_budget.daily_budget_usd -= can_borrow
                    budget.daily_budget_usd += can_borrow
                    budget.borrowed_from[other_tier] = budget.borrowed_from.get(other_tier, 0.0) + can_borrow
                    other_budget.borrowed_to[tier] = other_budget.borrowed_to.get(tier, 0.0) + can_borrow
                    total_borrowed += can_borrow
            return total_borrowed

    def get_budget_status(self, tier: Optional[str] = None) -> Dict[str, Any]:
        # Locked: a reader must not observe consumed_usd from one tier and
        # daily_budget_usd from mid-borrow on another (torn read).
        with self._lock:
            if tier and tier in self._budgets:
                b = self._budgets[tier]
                usage = (b.consumed_usd / b.daily_budget_usd * 100) if b.daily_budget_usd > 0 else 0.0
                ema = self._ema_costs.get(tier, 0.0)
                return {
                    "tier": tier,
                    "daily_budget_usd": b.daily_budget_usd,
                    "consumed_usd": b.consumed_usd,
                    "usage_pct": round(usage, 2),
                    "ema_cost": round(ema, 6),
                    "alarm_level": self._check_alarm(tier).value,
                    "borrowed_from": b.borrowed_from,
                    "borrowed_to": b.borrowed_to,
                }
            return {
                tier: {
                    "tier": t,
                    "daily_budget_usd": b.daily_budget_usd,
                    "consumed_usd": b.consumed_usd,
                    "usage_pct": round((b.consumed_usd / b.daily_budget_usd * 100) if b.daily_budget_usd > 0 else 0.0, 2),
                    "alarm_level": self._check_alarm(t).value,
                }
                for t, b in self._budgets.items()
            }

    def _export_dict(self) -> dict:
        """State in the exact schema `import_state` consumes (symmetric)."""
        # Locked so an export can never interleave a concurrent record_cost /
        # attempt_borrow and serialise a torn (half-updated) snapshot.
        with self._lock:
            return {
                "tiers": list(self._tiers),
                "budgets": {
                    t: {
                        "daily_budget_usd": b.daily_budget_usd,
                        "consumed_usd": b.consumed_usd,
                        "priority_weight": b.priority_weight,
                        "borrow_allowed": b.borrow_allowed,
                        "borrowed_from": dict(b.borrowed_from),
                        "borrowed_to": dict(b.borrowed_to),
                    }
                    for t, b in self._budgets.items()
                },
            }

    def to_json(self) -> str:
        """Serialize state in the schema `import_state` consumes (round-trippable)."""
        return json.dumps(self._export_dict(), indent=2)

    def export_state(self, path: str) -> bool:
        """Persist state to `path` for later `import_state` recovery."""
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self.to_json())
            return True
        except Exception:
            return False

    def _import_dict(self, payload: dict) -> None:
        """Validate and apply a state dict (schema from `_export_dict`)."""
        if not isinstance(payload, dict):
            raise LedgerCorruptionError("ledger root must be a mapping")

        tiers = payload.get("tiers")
        budgets = payload.get("budgets")
        if tiers is None or budgets is None:
            raise LedgerCorruptionError("missing tiers/budgets")

        seen = set()
        staged: Dict[str, TierQuota] = {}
        for tier_name, raw in budgets.items():
            if not isinstance(raw, dict):
                raise LedgerCorruptionError(f"bad budget mapping for {tier_name}")
            daily_budget_usd = float(raw.get("daily_budget_usd", 0.0))
            consumed_usd = float(raw.get("consumed_usd", 0.0))
            if not math.isfinite(daily_budget_usd) or not math.isfinite(consumed_usd):
                raise LedgerCorruptionError(f"non-finite budget values for {tier_name}")
            if consumed_usd < 0.0 or daily_budget_usd < 0.0:
                raise LedgerCorruptionError(f"negative budget values for {tier_name}")
            staged[tier_name] = TierQuota(
                tier=tier_name,
                daily_budget_usd=daily_budget_usd,
                consumed_usd=consumed_usd,
                priority_weight=float(raw.get("priority_weight", 1.0)),
                borrow_allowed=bool(raw.get("borrow_allowed", True)),
                borrowed_from=dict(raw.get("borrowed_from", {})),
                borrowed_to=dict(raw.get("borrowed_to", {})),
            )
            seen.add(tier_name)

        missing = [t for t in tiers if t not in seen]
        if missing:
            raise LedgerCorruptionError(f"missing budget entries for tiers: {missing}")

        # Two-phase commit: nothing above touched live state, so every raise
        # above is a clean closed-fail. Swap in atomically under the lock.
        with self._lock:
            self._budgets.update(staged)
            self._tiers = list(tiers)

    def import_state(self, path: str) -> bool:
        """Restore state from a JSON file written by `export_state`/`to_json`.

        Returns False on I/O errors (non-fatal). Raises `LedgerCorruptionError`
        when the file parses as valid JSON but violates the ledger schema --
        corrupt-but-parseable state must never be silently ignored
        (closes hermes_verify_state_roundtrip R3).
        """
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except LedgerCorruptionError:
            raise
        except OSError:
            return False
        except ValueError:
            # invalid JSON: closed-fail, non-fatal (R2 contract)
            return False
        self._import_dict(payload)
        return True

    @classmethod
    def from_json(cls, payload: str) -> "ArkCostLedger":
        """Reconstruct a ledger from a `to_json()` string (recovery path).

        Raises `LedgerCorruptionError` on malformed input -- the explicit
        recovery API for callers wanting strict validation. Closes
        [ERR_NO_RECOVERY]'s 'to_json() has no matching load path' gap.
        """
        inst = cls()
        inst._import_dict(json.loads(payload))
        return inst

    @classmethod
    def load(cls, path: str) -> "ArkCostLedger":
        """Load a ledger from a JSON file (recovery path, strict)."""
        with open(path, "r", encoding="utf-8") as handle:
            return cls.from_json(handle.read())

