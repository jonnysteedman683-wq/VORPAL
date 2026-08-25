"""
OMNICORE Fold-Gate Monitor v1.0 — GOAL_6.6 Generational Fold Gates
Watches the four maturity gates defined in GOALS.md and signals when the
generation is ready for CONVERGENCE_FOLD.

Stolen from:
  - GOALS.md §GOAL_6.6 (dual trigger: G1 headcount AND G2 maturity)
  - agent-triad-orchestration/references/generational-fold-plan.md
  - hive_integration_bridge.py (roster feed, headcount)
  - arise_swarm_integration.py (population feed)
  - event_bus.py (typed emission, error isolation)

Gates (all must be green for fold):
  - GATE_G1_HEADCOUNT:   live agent roster count >= 9 (cap 12)
  - GATE_G2_CLEAN_CYCLES: >= 10 clean gate cycles, zero open degradations
  - GATE_G2B_DIALECT:    dialect ledger clean, no unmerged tokens pending M4
  - GATE_G2C_CHILDREN:   every spawned triad's next instance passed cold-start
                         drill OR archived-with-lessons

CONVERGENCE_FOLD (all gates green):
  freeze -> distill retiring profiles -> merge canon (codebases->skills->
  dialect->Hermes config) -> re-baseline (verdict-free first cycle) ->
  boot gen N+1 at 3 agents with HUMAN_GATE mandatory at the boundary.

Zero-dependency Python stdlib implementation.
"""
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class GateStatus:
    """Status of a single fold gate."""
    gate_id: str
    label: str
    satisfied: bool
    current: Any
    required: Any
    detail: str = ""

    def progress(self) -> float:
        """Normalized 0.0-1.0 progress toward satisfying the gate."""
        if self.satisfied:
            return 1.0
        try:
            return min(1.0, float(self.current) / float(self.required))
        except (TypeError, ValueError, ZeroDivisionError):
            return 0.0


@dataclass
class FoldReadiness:
    """Aggregate readiness assessment across all gates."""
    generation: int
    gates: List[GateStatus]
    all_gates_green: bool
    fold_ready: bool       # gates green AND generation >= 1 (boot gating)
    human_gate_required: bool  # always True — HUMAN_GATE is mandatory
    blocking_gates: List[str]

    def summary(self) -> Dict[str, Any]:
        return {
            "generation": self.generation,
            "fold_ready": self.fold_ready,
            "all_gates_green": self.all_gates_green,
            "human_gate_required": self.human_gate_required,
            "blocking_gates": self.blocking_gates,
            "gates": {
                g.gate_id: {
                    "satisfied": g.satisfied,
                    "current": g.current,
                    "required": g.required,
                    "progress": round(g.progress(), 3),
                } for g in self.gates
            },
        }


class FoldGateMonitor:
    """Continuously assesses generation fold readiness (GOAL_6.6)."""

    HEADCOUNT_TARGET = 9
    HEADCOUNT_CAP = 12
    CLEAN_CYCLES_TARGET = 10
    BOOT_GENERATION = 3  # Gen N+1 boots at 3 agents

    def __init__(self, generation: int = 0,
                 hive: Any = None,  # HiveIntegrationBridge
                 arise: Any = None,  # AriseSwarmIntegration
                 event_bus: Any = None,
                 dialect_ledger: Optional[Dict] = None):
        self._generation = generation
        self._hive = hive
        self._arise = arise
        self._event_bus = event_bus
        self._dialect_ledger = dialect_ledger or {
            "pending_tokens": 0,       # unmerged dialect tokens awaiting M4
            "m4_audit_passed": False,
        }
        # Bookkeeping updated by record_* methods
        self._clean_cycles = 0
        self._open_degradations = 0
        self._children: Dict[str, bool] = {}  # child_id -> cold_start_passed
        self._archived_with_lessons: List[str] = []
        self._fold_log: List[Dict[str, Any]] = []
        self._last_check: float = 0.0
        self._last_readiness: Optional[FoldReadiness] = None  # throttle cache
        self._check_interval_s = 5.0  # throttled, mirrors arise pattern
        self._roster_override: Optional[int] = None  # cron watchdog override

    # ---- record bookkeeping -------------------------------------------------

    def record_clean_cycle(self) -> None:
        """Increment the clean-cycle counter (GATE_G2)."""
        self._clean_cycles += 1

    def record_degradation(self) -> None:
        """Record an open degradation (negates GATE_G2 progress)."""
        self._open_degradations += 1

    def resolve_degradation(self) -> None:
        """Close a degradation (floor at 0)."""
        self._open_degradations = max(0, self._open_degradations - 1)

    def register_child(self, child_id: str, cold_start_passed: bool = False) -> None:
        """Register a spawned triad's next instance."""
        self._children[child_id] = cold_start_passed

    def child_passed_cold_start(self, child_id: str) -> None:
        """Mark a child as passing its cold-start drill."""
        if child_id in self._children:
            self._children[child_id] = True
        else:
            self._children[child_id] = True

    def archive_child_with_lessons(self, child_id: str) -> None:
        """Mark a child as archived-with-lessons (satisfies GATE_G2C)."""
        self._children[child_id] = True  # archived counts as satisfied
        self._archived_with_lessons.append(child_id)

    def set_dialect_ledger(self, pending_tokens: int,
                           m4_audit_passed: bool) -> None:
        """Update dialect ledger state (GATE_G2B)."""
        self._dialect_ledger = {
            "pending_tokens": max(0, pending_tokens),
            "m4_audit_passed": m4_audit_passed,
        }

    def set_roster_count(self, count: int) -> None:
        """Override the headcount feed source (used by cron watchdog when no
        live hive/arise process is running)."""
        self._roster_override = max(0, int(count))

    # ---- gate evaluation ----------------------------------------------------

    def _gate_headcount(self) -> GateStatus:
        # Cron-watchdog override takes precedence (no live feed needed)
        if self._roster_override is not None:
            current = self._roster_override
            detail = "from cron watchdog override"
        elif self._hive is not None and hasattr(self._hive, "get_roster_feed"):
            try:
                feed = self._hive.get_roster_feed()
                current = feed["roster"]["total_active"]
                detail = "from hive roster feed"
            except Exception:
                current = 0
                detail = "hive feed unavailable"
        elif self._arise is not None and hasattr(self._arise, "get_hive_feed"):
            try:
                current = self._arise.get_hive_feed()["arise"]["alive"]
                detail = "from arise population feed"
            except Exception:
                current = 0
                detail = "arise feed unavailable"
        else:
            current = 0
            detail = "no roster feed wired"

        capped = min(current, self.HEADCOUNT_CAP)
        return GateStatus(
            gate_id="GATE_G1_HEADCOUNT",
            label="live agent roster count",
            satisfied=capped >= self.HEADCOUNT_TARGET,
            current=current,
            required=self.HEADCOUNT_TARGET,
            detail=detail,
        )

    def _gate_clean_cycles(self) -> GateStatus:
        satisfied = (self._clean_cycles >= self.CLEAN_CYCLES_TARGET
                     and self._open_degradations == 0)
        return GateStatus(
            gate_id="GATE_G2_CLEAN_CYCLES",
            label="clean gate cycles (zero degradations)",
            satisfied=satisfied,
            current=self._clean_cycles,  # numeric for progress()
            required=self.CLEAN_CYCLES_TARGET,
            detail=(f"{self._clean_cycles} clean cycles, "
                    f"{self._open_degradations} open degradations"),
        )

    def _gate_dialect(self) -> GateStatus:
        ledger = self._dialect_ledger
        satisfied = (ledger.get("pending_tokens", 0) == 0
                     and ledger.get("m4_audit_passed", False))
        return GateStatus(
            gate_id="GATE_G2B_DIALECT",
            label="dialect ledger clean, M4 audit passed",
            satisfied=satisfied,
            current=ledger.get("pending_tokens", 0),
            required=0,
            detail=(f"{ledger.get('pending_tokens', 0)} pending tokens, "
                    f"M4 audit {'passed' if ledger.get('m4_audit_passed') else 'pending'}"),
        )

    def _gate_children(self) -> GateStatus:
        children = self._children
        if not children:
            # No children spawned yet -> vacuously satisfied (nothing to gate)
            return GateStatus(
                gate_id="GATE_G2C_CHILDREN",
                label="all children passed cold-start or archived",
                satisfied=True,
                current=0,
                required=0,
                detail="no children spawned this generation (vacuous)",
            )
        unpassed = [cid for cid, passed in children.items() if not passed]
        satisfied = len(unpassed) == 0
        return GateStatus(
            gate_id="GATE_G2C_CHILDREN",
            label="all children passed cold-start or archived",
            satisfied=satisfied,
            current=len(children) - len(unpassed),
            required=len(children),
            detail=(f"{len(children) - len(unpassed)}/{len(children)} passed "
                    f"(unpassed: {unpassed})"),
        )

    # ---- aggregate ----------------------------------------------------------

    def evaluate(self, force: bool = False) -> FoldReadiness:
        """Evaluate all gates. Throttled unless force=True."""
        now = time.time()
        if not force and (now - self._last_check) < self._check_interval_s:
            # Return cached readiness if within throttle window
            if self._last_readiness is not None:
                return self._last_readiness
        self._last_check = now

        gates = [
            self._gate_headcount(),
            self._gate_clean_cycles(),
            self._gate_dialect(),
            self._gate_children(),
        ]
        all_green = all(g.satisfied for g in gates)
        blocking = [g.gate_id for g in gates if not g.satisfied]

        readiness = FoldReadiness(
            generation=self._generation,
            gates=gates,
            all_gates_green=all_green,
            fold_ready=all_green and self._generation >= 1,
            human_gate_required=True,  # HUMAN_GATE always mandatory
            blocking_gates=blocking,
        )

        self._last_readiness = readiness
        self._emit("fold.gate_check", {
            "fold_ready": readiness.fold_ready,
            "blocking": blocking,
        })
        return readiness

    # ---- fold protocol -------------------------------------------------------

    def trigger_convergence_fold(self, actor: str = "omniprime") -> Optional[Dict]:
        """
        Execute CONVERGENCE_FOLD protocol. Returns protocol plan if gates green,
        else None. HUMAN_GATE is mandatory — this never auto-boots gen N+1.
        """
        readiness = self.evaluate(force=True)
        if not readiness.fold_ready:
            self._emit("fold.blocked", {"blocking": readiness.blocking_gates})
            return None

        plan = {
            "protocol": "CONVERGENCE_FOLD",
            "generation": self._generation,
            "actor": actor,
            "steps": [
                "freeze retiring generation",
                "distill all retiring profiles",
                "merge canon: codebases -> skills -> dialect -> Hermes config",
                "re-baseline (verdict-free first cycle)",
                "boot gen N+1 at 3 agents",
            ],
            "human_gate": {
                "required": True,
                "status": "MANDATORY — awaiting human approval before boot",
            },
            "next_generation": self._generation + 1,
            "boot_agents": self.BOOT_GENERATION,
            "triggered_at": time.time(),
        }
        self._fold_log.append(plan)
        self._emit("fold.trigger", {"generation": self._generation,
                                    "next": plan["next_generation"]})
        return plan

    def boot_next_generation(self, human_approved: bool = False) -> bool:
        """Boot gen N+1 at 3 agents. REQUIRES human approval."""
        if not human_approved:
            return False  # HUMAN_GATE blocks auto-boot
        self._generation += 1
        self._children = {}
        self._clean_cycles = 0
        self._open_degradations = 0
        self._fold_log = []
        self._emit("fold.boot", {"generation": self._generation,
                                 "agents": self.BOOT_GENERATION})
        return True

    # ---- introspection -------------------------------------------------------

    def audit_log(self) -> Dict[str, Any]:
        return {
            "generation": self._generation,
            "clean_cycles": self._clean_cycles,
            "open_degradations": self._open_degradations,
            "children": dict(self._children),
            "archived_with_lessons": self._archived_with_lessons,
            "dialect_ledger": self._dialect_ledger,
            "fold_events": len(self._fold_log),
        }

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._event_bus is not None and hasattr(self._event_bus, "emit"):
            try:
                self._event_bus.emit(event_type, payload)
            except Exception:
                pass  # error isolation


def create_fold_monitor(generation: int = 0, hive=None, arise=None,
                        event_bus=None) -> FoldGateMonitor:
    return FoldGateMonitor(generation=generation, hive=hive, arise=arise,
                           event_bus=event_bus)