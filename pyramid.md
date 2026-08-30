#!/usr/bin/env python3
"""
Pyramid Agent Lifecycle System
Binary tree structure: 1-2-4-8 agents (T0-T3)
Each agent spawns 2 children and consolidates 2 inputs from below
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import hashlib

class Tier(Enum):
    TIER_0 = 0  # Final consolidator (1 agent)
    TIER_1 = 1  # Intermediate (2 agents)
    TIER_2 = 2  # Aggregate (4 agents)
    TIER_3 = 3  # Leaf workers (8 agents)

@dataclass
class AgentState:
    """State for pyramid agents"""
    agent_id: str
    tier: Tier
    parent_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    work_completed: bool = False

class PyramidAgent:
    """Base agent class for pyramid structure"""
    
    def __init__(self, agent_id: str, tier: Tier, pyramid_dir: Path):
        self.state = AgentState(agent_id=agent_id, tier=tier, pyramid_dir=str(pyramid_dir))
        self.pyramid_dir = Path(pyramid_dir)
        self.agent_file = self.pyramid_dir / f"tier{tier.value}" / f"{agent_id}.json"
        
    def spawn_children(self) -> List['PyramidAgent']:
        """Spawn 2 children agents (for tiers 0-2)"""
        if self.state.tier == Tier.TIER_3:
            return []  # Leaf agents don't spawn children
        
        children = []
        child_tier = Tier(self.state.tier.value + 1)
        for i in range(2):
            child_id = f"{self.state.agent_id}_child_{i}"
            child = PyramidAgent(child_id, child_tier, self.pyramid_dir)
            self._register_child(child_id)
            children.append(child)
        
        # Set parent reference for children
        for child in children:
            child._set_parent(self.state.agent_id)
            
        return children
    
    def _register_child(self, child_id: str):
        """Register child in file system"""
        self.state.child_ids.append(child_id)
        self._save_state()
    
    def _set_parent(self, parent_id: str):
        """Set parent reference"""
        self.state.parent_ids.append(parent_id)
    
    def receive_input(self, data: Dict[str, Any]):
        """Receive consolidated work from children (tiers 1-3)"""
        self.state.input_data = data
        self.state.status = "processing"
    
    def process_work(self):
        """Do tier-appropriate work"""
        if self.state.tier == Tier.TIER_3:
            # Leaf work - process raw input
            self._do_leaf_work()
        else:
            # Consolidation work - merge child results
            self._consolidate_children()
        
        self.state.status = "completed"
        self.state.work_completed = True
    
    def _do_leaf_work(self):
        """T3: Perform foundational work"""
        # Example: generate data chunks
        work_items = [f"work_item_{self.state.agent_id}_{i}" for i in range(4)]
        self.state.output_data = {
            "agent_id": self.state.agent_id,
            "tier": self.state.tier.value,
            "chunks": work_items,
            "hash": self._compute_hash(work_items)
        }
    
    def _consolidate_children(self):
        """Higher tiers: consolidate 2 child results"""
        if self.state.parent_ids:
            # Send data up to parent
            pass
        
        # Aggregate from 2 children (stored in input_data)
        consolidated = {
            "agent_id": self.state.agent_id,
            "tier": self.state.tier.value,
            "consolidated_from": len(self.state.input_data.get("sources", [])),
            "merged_chunks": self._merge_chunks(),
            "source_agents": self.state.input_data.get("source_agents", [])
        }
        self.state.output_data = consolidated
    
    def _merge_chunks(self):
        """Merge chunks from children"""
        chunks = []
        for key, val in self.state.input_data.items():
            if isinstance(val, dict) and "chunks" in val:
                chunks.extend(val["chunks"])
        return chunks
    
    def _compute_hash(self, data: Any) -> str:
        """Compute SHA256 hash for data integrity"""
        return hashlib.sha256(str(data).encode()).hexdigest()[:16]
    
    def _save_state(self):
        """Persist agent state to file"""
        self.agent_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.agent_file, 'w') as f:
            json.dump(self.state.__dict__, f, indent=2)
    
    def load_state(self) -> AgentState:
        """Load agent state from file"""
        if self.agent_file.exists():
            with open(self.agent_file, 'r') as f:
                data = json.load(f)
                self.state = AgentState(**data)
        return self.state
    
    def get_result(self) -> Dict[str, Any]:
        """Get agent's output data"""
        return self.state.output_data


class PyramidOrchestrator:
    """Manages the entire pyramid lifecycle"""
    
    def __init__(self, base_dir: Path = None):
        self.base_dir = Path(base_dir or "/tmp/pyramid_agents")
        self.tier_dirs = {
            Tier.TIER_0: self.base_dir / "tier0",
            Tier.TIER_1: self.base_dir / "tier1", 
            Tier.TIER_2: self.base_dir / "tier2",
            Tier.TIER_3: self.base_dir / "tier3"
        }
    
    def initialize_structure(self):
        """Create directory structure"""
        for tier_dir in self.tier_dirs.values():
            tier_dir.mkdir(parents=True, exist_ok=True)
    
    def create_pyramid(self):
        """Initialize the full pyramid: 1-2-4-8"""
        self.initialize_structure()
        
        # Tier 0: Final consolidator
        t0_agent = PyramidAgent("consolidator_final", Tier.TIER_0, self.base_dir)
        t0_agents = [t0_agent]
        
        # Tier 1: 2 agents
        t1_agents = [
            PyramidAgent(f"t1_agent_{i}", Tier.TIER_1, self.base_dir) 
            for i in range(2)
        ]
        
        # Tier 2: 4 agents
        t2_agents = [
            PyramidAgent(f"t2_agent_{i}", Tier.TIER_2, self.base_dir)
            for i in range(4)
        ]
        
        # Tier 3: 8 leaf agents
        t3_agents = [
            PyramidAgent(f"t3_agent_{i}", Tier.TIER_3, self.base_dir)
            for i in range(8)
        ]
        
        # Set up parent-child relationships
        self._wire_pyramid(t0_agents, t1_agents, t2_agents, t3_agents)
        
        return {
            "tier0": t0_agents,
            "tier1": t1_agents,
            "tier2": t2_agents,
            "tier3": t3_agents
        }
    
    def _wire_pyramid(self, t0, t1, t2, t3):
        """Wire parent-child relationships"""
        # Each T1 agent gets 2 T2 children
        for i, t1_agent in enumerate(t1):
            t2_parents = t2[i*2:(i+1)*2]
            t2_agent_ids = [t2_parents[0].state.agent_id, t2_parents[1].state.agent_id]
            t1_agent.state.parent_ids = t2_agent_ids
            t1_agent._save_state()
            
            for t2_agent in t2_parents:
                t2_agent._register_child(t1_agent.state.agent_id)
        
        # Each T2 agent gets 2 T3 children
        for i, t2_agent in enumerate(t2):
            t3_parents = t3[i*2:(i+1)*2]
            t3_agent_ids = [t3_parents[0].state.agent_id, t3_parents[1].state.agent_id]
            t2_agent.state.parent_ids = t3_agent_ids
            t2_agent._save_state()
            
            for t3_agent in t3_parents:
                t3_agent._register_child(t2_agent.state.agent_id)
        
        # T0 agent gets both T1 children
        t0 = t0[0]
        t1_agent_ids = [t1_agent.state.agent_id for t1_agent in t1]
        t0.state.parent_ids = t1_agent_ids
        t0._save_state()
        
        for t1_agent in t1:
            t1_agent._register_child(t0.state.agent_id)
    
    def run_lifecycle(self, agents: Dict[str, List]) -> Dict[str, Any]:
        """Execute pyramid lifecycle: T3 → T2 → T1 → T0"""
        results = {"tier_results": {}, "final_output": None}
        
        # Phase 1: T3 leaves do work
        print("Phase 1: Tier 3 leaf workers processing...")
        for agent in agents["tier3"]:
            agent.process_work()
            results["tier_results"][agent.state.agent_id] = agent.get_result()
            print(f"  {agent.state.agent_id}: chunks generated")
        
        # Phase 2: T2 aggregates T3 outputs (pairs of 2)
        print("\nPhase 2: Tier 2 consolidation...")
        for i, agent in enumerate(agents["tier2"]):
            # Get results from paired T3 agents
            t3_parents = agents["tier3"][i*2:(i+1)*2]
            child_results = {t3.state.agent_id: t3.get_result() for t3 in t3_parents}
            
            agent.receive_input({
                "sources": list(child_results.keys()),
                **child_results
            })
            agent.process_work()
            results["tier_results"][agent.state.agent_id] = agent.get_result()
            print(f"  {agent.state.agent_id}: consolidated {len(child_results)} sources")
        
        # Phase 3: T1 aggregates T2 outputs (pairs of 2)
        print("\nPhase 3: Tier 1 consolidation...")
        for i, agent in enumerate(agents["tier1"]):
            t2_parents = agents["tier2"][i*2:(i+1)*2]
            child_results = {t2.state.agent_id: t2.get_result() for t2 in t2_parents}
            
            agent.receive_input({
                "sources": list(child_results.keys()),
                **child_results
            })
            agent.process_work()
            results["tier_results"][agent.state.agent_id] = agent.get_result()
            print(f"  {agent.state.agent_id}: consolidated {len(child_results)} sources")
        
        # Phase 4: T0 final consolidation
        print("\nPhase 4: Tier 0 final consolidation...")
        t0_agent = agents["tier0"][0]
        t1_parents = agents["tier1"]
        child_results = {t1.state.agent_id: t1.get_result() for t1 in t1_parents}
        
        t0_agent.receive_input({
            "sources": list(child_results.keys()),
            **child_results
        })
        t0_agent.process_work()
        results["final_output"] = t0_agent.get_result()
        print(f"  {t0_agent.state.agent_id}: FINAL aggregation complete")
        print(f"    Merged {len(results['tier_results'])} agent outputs")
        
        return results


# Example usage
if __name__ == "__main__":
    orchestrator = PyramidOrchestrator(Path("/tmp/pyramid_agents"))
    agents = orchestrator.create_pyramid()
    results = orchestrator.run_lifecycle(agents)
    
    print("\n" + "="*60)
    print("PYRAMID LIFECYCLE COMPLETE")
    print("="*60)
    print(f"Final output: {json.dumps(results['final_output'], indent=2)}")