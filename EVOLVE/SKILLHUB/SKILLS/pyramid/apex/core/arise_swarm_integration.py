"""
OMNICORE ARISE Swarm Integration v1.0
Bridges ARISE-style swarm agents (survival simulation units) into the OMNIPRIME
hive architecture, exposing swarm population dynamics, reproduction gating, and
state sync to the triad.

Stolen from:
  - ARISE brain (reproduction = primary goal, save.load subsystem init)
  - hive_integration_bridge.py (roster feed, T1/T2 access, consensus voting)
  - p2p_state_registry.py (peer registration, heartbeat, reputation)
  - event_bus.py (typed emission, error isolation)

Features:
  - Swarm population registry (agents with genotype, energy, generation)
  - Reproduction gating: a new swarm unit only enters the hive after a
    passing cold-start drill (reproduction before communion)
  - save/load state snapshot (stdlib pickle-free JSON) for subsystem init
  - Throttled collection: batch metric harvesting instead of per-tick polling
  - Event bus emission on swarm lifecycle events (spawn, death, reproduction)
  - Population report feed for GOAL_6.6 hive headcount gate

Zero-dependency Python stdlib implementation.
"""
import json
import time
import uuid
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Optional integration with hive bridge (GOAL_6.1 dependency)
try:
    from apex.core.hive_integration_bridge import HiveIntegrationBridge
    _HIVE_AVAILABLE = True
except ImportError:
    _HIVE_AVAILABLE = False


@dataclass
class SwarmAgent:
    """A single swarm survival unit with ARISE-style dynamics."""
    agent_id: str
    genotype: str  # Encoded traits, e.g. "A1B2C3"
    generation: int = 0
    energy: float = 100.0
    lifespan: float = 100.0
    alive: bool = True
    born: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    reproduction_count: int = 0
    cold_start_passed: bool = False  # T2 gate: reproduction before communion


@dataclass
class ReproductionEvent:
    """Record of a swarm unit reproducing a child."""
    parent_id: str
    child_id: str
    generation: int
    timestamp: float
    child_cold_start: bool  # Did the child pass its cold-start drill?


@dataclass
class PopulationReport:
    """Snapshot of swarm population for the hive feed."""
    population: int
    alive: int
    dead: int
    avg_energy: float
    generations: int
    reproduction_events: int
    reproduction_unlocked: bool  # T2 access state


class AriseSwarmIntegration:
    """
    Bridge between ARISE-style swarm agents and the OMNIPRIME hive.

    Key ARISE invariants (per OMNI-SOUL memory):
      - reproduction is the primary goal
      - save/load inits subsystems; top-level brain imports only
      - collections are throttled (never per-tick polling)
      - a new unit must pass cold-start before entering the hive
    """

    COLD_START_ENERGY = 50.0
    MAX_GENERATIONS = 12  # Mirror GOAL_6.6 fold cap (3->6->9/12 -> fold)
    THROTTLE_COLLECTION_S = 5.0  # Minimum seconds between collection batches

    def __init__(self, hive: Optional[Any] = None,
                 state_path: Optional[str] = None,
                 event_bus: Optional[Any] = None):
        self._hive = hive  # HiveIntegrationBridge instance (GOAL_6.1)
        self._event_bus = event_bus  # EventBus instance (GOAL_6.3)
        self._state_path = Path(state_path) if state_path else None

        self._agents: Dict[str, SwarmAgent] = {}
        self._reproduction_log: List[ReproductionEvent] = []
        self._last_collection: float = 0.0
        self._reproduction_unlocked = False  # T2 gate

    # ---- registration -----------------------------------------------------

    def spawn_agent(self, genotype: str = "A1B1C1",
                    generation: int = 0) -> SwarmAgent:
        """Spawn a new swarm unit. Child units must pass cold-start before
        they can reproduce or enter the hive (reproduction before communion)."""
        agent = SwarmAgent(
            agent_id=f"arise-{uuid.uuid4().hex[:8]}",
            genotype=genotype,
            generation=generation,
            energy=self.COLD_START_ENERGY if generation > 0 else 100.0,
        )
        self._agents[agent.agent_id] = agent
        self._emit("swarm.spawn", {"agent_id": agent.agent_id,
                                   "generation": agent.generation})
        return agent

    def pass_cold_start(self, agent_id: str) -> bool:
        """Mark a swarm unit as having passed its cold-start drill.
        Only then can it reproduce / access the hive (T2 gate)."""
        agent = self._agents.get(agent_id)
        if agent is None:
            return False
        agent.cold_start_passed = True
        # Mirror hive bridge: register child in hive if present
        if self._hive is not None and _HIVE_AVAILABLE:
            import asyncio
            asyncio.run(self._hive.register_child_success())
        self._emit("swarm.cold_start", {"agent_id": agent_id})
        return True

    # ---- reproduction -----------------------------------------------------

    def reproduce(self, parent_id: str, mutation: bool = False) -> Optional[SwarmAgent]:
        """Reproduction is the primary goal. Parent spawns a child at
        generation+1. Requires the parent to have passed cold-start (T2 gate)."""
        parent = self._agents.get(parent_id)
        if parent is None or not parent.alive:
            return None
        if not parent.cold_start_passed:
            return None  # reproduction locked until cold-start passes
        if parent.generation + 1 > self.MAX_GENERATIONS:
            return None  # fold cap reached

        genotype = parent.genotype
        if mutation:
            # Simple drift: flip the last genotype char's numeric value
            if genotype[-1].isdigit():
                new_val = str((int(genotype[-1]) + 1) % 10)
                genotype = genotype[:-1] + new_val

        child = self.spawn_agent(genotype=genotype,
                                 generation=parent.generation + 1)
        parent.reproduction_count += 1

        self._reproduction_log.append(ReproductionEvent(
            parent_id=parent_id,
            child_id=child.agent_id,
            generation=child.generation,
            timestamp=time.time(),
            child_cold_start=False,  # child must pass its own cold-start
        ))
        self._emit("swarm.reproduce", {"parent_id": parent_id,
                                       "child_id": child.agent_id,
                                       "generation": child.generation})
        return child

    # ---- lifecycle --------------------------------------------------------

    def tick(self, agent_id: str, energy_delta: float = 0.0) -> bool:
        """One simulation tick: update energy and liveness."""
        agent = self._agents.get(agent_id)
        if agent is None:
            return False
        agent.energy = max(0.0, agent.energy + energy_delta)
        agent.last_seen = time.time()
        if agent.energy <= 0.0:
            agent.alive = False
            self._emit("swarm.death", {"agent_id": agent_id,
                                       "generation": agent.generation})
        return True

    def energy_transfer(self, donor_id: str, recipient_id: str,
                        amount: float) -> bool:
        """Throttled collective energy sharing between swarm units."""
        donor = self._agents.get(donor_id)
        recipient = self._agents.get(recipient_id)
        if donor is None or recipient is None or not donor.alive:
            return False
        if donor.energy < amount:
            amount = donor.energy
        donor.energy -= amount
        recipient.energy += amount
        return True

    # ---- throttled collection ----------------------------------------------

    def collect_metrics(self, force: bool = False) -> Optional[PopulationReport]:
        """Throttled collection: batch metrics at most once per
        THROTTLE_COLLECTION_S. Mirrors ARISE 'throttle collections' rule."""
        now = time.time()
        if not force and (now - self._last_collection) < self.THROTTLE_COLLECTION_S:
            return None  # throttled — caller should not poll per-tick
        self._last_collection = now

        alive = [a for a in self._agents.values() if a.alive]
        dead = len(self._agents) - len(alive)
        avg_energy = (sum(a.energy for a in alive) / len(alive)
                      if alive else 0.0)
        generations = max((a.generation for a in self._agents.values()),
                          default=0)
        return PopulationReport(
            population=len(self._agents),
            alive=len(alive),
            dead=dead,
            avg_energy=round(avg_energy, 2),
            generations=generations,
            reproduction_events=len(self._reproduction_log),
            reproduction_unlocked=self._reproduction_unlocked,
        )

    # ---- save / load (subsystem init) --------------------------------------

    def save_state(self, path: Optional[str] = None) -> str:
        """Persist swarm state to JSON. Mirrors ARISE save.load subsystem init."""
        target = Path(path) if path else self._state_path
        if target is None:
            raise ValueError("no state path configured")
        payload = {
            "version": "1.0",
            "agents": [
                {k: v for k, v in a.__dict__.items()}
                for a in self._agents.values()
            ],
            "reproduction_log": [
                r.__dict__ for r in self._reproduction_log
            ],
            "reproduction_unlocked": self._reproduction_unlocked,
            "saved_at": time.time(),
        }
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._emit("swarm.save", {"path": str(target)})
        return str(target)

    def load_state(self, path: Optional[str] = None) -> int:
        """Rehydrate swarm state from JSON (subsystem init). Returns agent count."""
        target = Path(path) if path else self._state_path
        if target is None or not target.exists():
            return 0
        payload = json.loads(target.read_text(encoding="utf-8"))
        self._agents = {}
        for a in payload.get("agents", []):
            agent = SwarmAgent(**a)
            self._agents[agent.agent_id] = agent
        self._reproduction_log = [
            ReproductionEvent(**r) for r in payload.get("reproduction_log", [])
        ]
        self._reproduction_unlocked = payload.get("reproduction_unlocked", False)
        self._emit("swarm.load", {"path": str(target), "agents": len(self._agents)})
        return len(self._agents)

    # ---- feed for hive / GOAL_6.6 ------------------------------------------

    def get_hive_feed(self) -> Dict[str, Any]:
        """Population feed for the hive headcount gate (GOAL_6.6)."""
        report = self.collect_metrics(force=True)
        return {
            "arise": {
                "population": report.population if report else 0,
                "alive": report.alive if report else 0,
                "generations": report.generations if report else 0,
                "reproduction_events": report.reproduction_events if report else 0,
                "reproduction_unlocked": report.reproduction_unlocked if report else False,
            },
            "timestamp": time.time(),
        }

    # ---- helpers -----------------------------------------------------------

    def get_agent(self, agent_id: str) -> Optional[SwarmAgent]:
        return self._agents.get(agent_id)

    def audit_log(self) -> Dict[str, Any]:
        return {
            "population": len(self._agents),
            "reproduction_events": len(self._reproduction_log),
            "reproduction_unlocked": self._reproduction_unlocked,
            "max_generations": self.MAX_GENERATIONS,
            "hive_connected": self._hive is not None,
            "event_bus_connected": self._event_bus is not None,
            "recent_reproductions": [
                {"parent": r.parent_id, "child": r.child_id,
                 "gen": r.generation} for r in self._reproduction_log[-5:]
            ],
        }

    def _emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Fire a typed event on the event bus if connected (GOAL_6.3)."""
        if self._event_bus is not None and hasattr(self._event_bus, "emit"):
            try:
                self._event_bus.emit(event_type, payload)
            except Exception:
                pass  # error isolation: bus failure never breaks the swarm


def create_arise_bridge(hive=None, event_bus=None,
                        state_path: Optional[str] = None) -> AriseSwarmIntegration:
    return AriseSwarmIntegration(hive=hive, event_bus=event_bus,
                                 state_path=state_path)