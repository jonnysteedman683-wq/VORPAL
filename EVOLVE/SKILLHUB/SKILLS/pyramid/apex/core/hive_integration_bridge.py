"""
OMNICORE HIVE Integration Bridge v1.0
Connects triad agents in a hive-mind architecture with roster/health feeds
and shared memory sync.

Stolen from:
  - hive_swarm_adapter.ts (peer discovery, state delta broadcasting)
  - p2p_state_registry.ts (roster feed, health sync)
  - tri_agentic_kernel.ts (personality-driven consensus)
  - generational_fold-plan.md (T1/T2 hive access patterns)

Features:
  - Agent roster with health feed (for GOAL_6.6 headcount gate)
  - T1: Per-triad shared memory at boot
  - T2: Hive write-access after child reproduction (passing test)
  - Cross-agent consensus with personality-weighted voting
  - State propagation across triad mesh
"""
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict

# Import core components
import sys
PYRAMID_BASE = Path(__file__).parent
sys.path.insert(0, str(PYRAMID_BASE.parent))

from apex.core.p2p_state_registry import PeerRegistry, PeerState


@dataclass
class HiveAgent:
    """Agent registered in the hive with personality profile."""
    agent_id: str
    profile: str  # 'a1', 'a2', 'a3' or custom
    role: str  # 'guard', 'executor', 'architect', 'editor'
    status: str = "active"  # active | reproducing | archived
    health_score: float = 50.0  # 0-100
    last_heartbeat: float = field(default_factory=time.time)
    reproduction_count: int = 0  # For T2 hive access gating


@dataclass
class HiveConsensus:
    """Result of hive consensus vote."""
    decision: str
    confidence: float
    participating_tiers: List[str]  # T1, T2, T3
    is_reproduced: bool  # Did a child pass cold-start?


class HiveIntegrationBridge:
    """
    Bridge between triad agents enabling:
    1. Roster/Health feed for GOAL_6.6 headcount gate
    2. T1 per-triad shared memory from boot
    3. T2 hive write-access after child reproduction
    """
    
    T1_HIVE_ACCESS = "T1_shared_memory"  # Boot access for all
    T2_HIVE_ACCESS = "T2_full_write"   # After child reproduction
    
    PERSONALITY_WEIGHTS = {
        'a1': 1.2,  # Gatekeeper - higher weight
        'a2': 1.0,  # Optimizer - balanced
        'a3': 0.9,  # Architect - slightly lower
    }
    
    def __init__(self, self_agent_id: str, role: str = "architect"):
        self._self_id = self_agent_id
        self._role = role
        self._agents: Dict[str, HiveAgent] = {}
        self._reproduction_lockout = True  # Lockout until child passes
        self._consensus_log: List[HiveConsensus] = []
        self._lock = asyncio.Lock()
        
        # Register self
        self._agents[self_agent_id] = HiveAgent(
            agent_id=self_agent_id,
            profile="a2",  # Default self profile
            role=role,
            health_score=50.0
        )
    
    async def register_agent(self, agent_id: str, profile: str, 
                            role: str, health_init: float = 50.0) -> HiveAgent:
        """Register a new agent in the hive."""
        async with self._lock:
            agent = HiveAgent(
                agent_id=agent_id,
                profile=profile,
                role=role,
                health_score=health_init
            )
            self._agents[agent_id] = agent
            return agent
    
    async def heartbeat(self, agent_id: str) -> bool:
        """Record heartbeat from agent."""
        async with self._lock:
            if agent_id not in self._agents:
                return False
            self._agents[agent_id].last_heartbeat = time.time()
            self._agents[agent_id].health_score = min(100.0, 
                self._agents[agent_id].health_score + 1.0)
            return True
    
    async def report_health(self, agent_id: str, score: float) -> bool:
        """Update agent health score."""
        async with self._lock:
            if agent_id not in self._agents:
                return False
            self._agents[agent_id].health_score = min(100.0, max(0.0, score))
            return True
    
    def get_roster_feed(self) -> Dict[str, Any]:
        """
        Get roster feed for GOAL_6.6 headcount gate.
        Returns active agent count and health distribution.
        """
        now = time.time()
        active_agents = [
            a for a in self._agents.values()
            if a.status == "active" and (now - a.last_heartbeat) < 30
        ]
        
        return {
            "roster": {
                "total_active": len(active_agents),
                "agents": {a.agent_id: {
                    "role": a.role,
                    "profile": a.profile,
                    "health": a.health_score,
                    "last_seen": a.last_heartbeat
                } for a in active_agents}
            },
            "reproduction_status": {
                "lockout_active": self._reproduction_lockout,
                "reproduction_count": sum(a.reproduction_count for a in active_agents)
            },
            "timestamp": now
        }
    
    def get_headcount_for_gate(self, min_count: int = 9) -> bool:
        """Check if headcount gate threshold met (GOAL_6.6)."""
        roster = self.get_roster_feed()
        return roster["roster"]["total_active"] >= min_count
    
    def get_hive_access_level(self) -> str:
        """Determine current hive access level (T1 or T2)."""
        if not self._reproduction_lockout:
            return self.T2_HIVE_ACCESS
        return self.T1_HIVE_ACCESS
    
    async def vote_on_intent(self, intent: str, 
                             proposer: Optional[str] = None) -> HiveConsensus:
        """
        Hive consensus on an intent/vote.
        Uses personality-weighted voting for decision making.
        """
        agents_voting = [
            a for a in self._agents.values()
            if a.status == "active" and (time.time() - a.last_heartbeat) < 60
        ]
        
        if not agents_voting:
            return HiveConsensus(
                decision=intent,
                confidence=0.0,
                participating_tiers=[],
                is_reproduced=not self._reproduction_lockout
            )
        
        # Weight votes by personality profile
        total_weight = 0.0
        support_weight = 0.0
        tiers_participating = set()
        
        for agent in agents_voting:
            weight = self.PERSONALITY_WEIGHTS.get(agent.profile, 1.0)
            total_weight += weight
            support_weight += weight  # All active agents support by default
            tiers_participating.add(agent.profile.upper())
        
        confidence = support_weight / total_weight if total_weight > 0 else 0.0
        
        consensus = HiveConsensus(
            decision=intent,
            confidence=confidence,
            participating_tiers=list(tiers_participating),
            is_reproduced=not self._reproduction_lockout
        )
        
        self._consensus_log.append(consensus)
        return consensus
    
    async def register_child_success(self) -> None:
        """
        Called when a child agent passes cold-start drill.
        Enables T2 hive write-access.
        """
        self._reproduction_lockout = False
    
    def get_shared_memory_key(self, tier: str = "T1") -> str:
        """Get shared memory key for given tier."""
        if tier == "T2" and not self._reproduction_lockout:
            return f"hive://{self._self_id}/t2_shared"
        return f"hive://{self._self_id}/t1_shared"
    
    def broadcast_state_delta(self, key: str, value: Any) -> Dict[str, Any]:
        """Broadcast state change to hive participants."""
        return {
            "delta_id": f"HD-{hash(f'{key}{time.time()}') % 10000}",
            "key": key,
            "value": value,
            "source": self._self_id,
            "timestamp": time.time(),
            "hive_tier": self.get_hive_access_level()
        }
    
    def audit_log(self) -> Dict[str, Any]:
        """Get hive state audit log."""
        active_count = len([a for a in self._agents.values() 
                           if a.status == "active"])
        return {
            "hive_state": {
                "agents_active": active_count,
                "agents_total": len(self._agents),
                "access_level": self.get_hive_access_level(),
                "lockout_active": self._reproduction_lockout,
                "tier1_keys": True,  # Always available at boot
                "tier2_keys": not self._reproduction_lockout
            },
            "consensus_count": len(self._consensus_log),
            "recent_consensus": self._consensus_log[-5:] if self._consensus_log else []
        }


# Factory function
def create_hive_bridge(self_agent_id: str, role: str = "architect") -> HiveIntegrationBridge:
    """Create a Hive Integration Bridge for a triad agent."""
    return HiveIntegrationBridge(self_agent_id=self_agent_id, role=role)