"""
OMNICORE IDEA ENGINE SKILL
Dual-dice decision engine for creative idea generation and selection.
Pattern stolen from SOUL.md v4.0 - Dual dice engine, no A4, 2-of-own rule.
"""
import random
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class IdeaTier(Enum):
    INNOVATION = "innovation"
    OPTIMIZATION = "optimization"
    REPAIR = "repair"
    EXPLORATION = "exploration"

@dataclass
class IdeaNode:
    id: str
    title: str
    description: str
    tier: IdeaTier
    confidence: float  # 0.0 - 1.0
    token_cost: int
    dependencies: List[str]
    generated_by: str  # Which dice roll generated this
    lineage: List[str]  # Parent idea IDs for tracing

class IdeaEngine:
    """
    Dual-dice creative engine implementing SOUL.md v4.0 patterns.
    
    Dice 1: Innovation/Exploration (left brain - logical)
    Dice 2: Optimization/Repair (right brain - intuitive)
    
    Rules:
    - No A4 (no infinite recursion)
    - 2-of-own (at least 2 internal references per idea)
    - Token optimization mandatory
    """
    
    def __init__(self, state_db: str = "omnicore_ideas.db"):
        self._ideas: Dict[str, IdeaNode] = {}
        self._roll_history: List[dict] = []
        self._seed = random.randint(0, 2**32 - 1)
        self._rng = random.Random(self._seed)
        
    def _roll_die(self, sides: int = 6) -> int:
        """Roll a virtual die with specified sides."""
        roll = self._rng.randint(1, sides)
        self._roll_history.append({
            'roll': roll,
            'sides': sides,
            'timestamp': len(self._roll_history)
        })
        return roll

    def _dual_dice_generate(self) -> Tuple[IdeaTier, float]:
        """Roll dual dice to determine idea generation parameters."""
        die1 = self._roll_die()  # Innovation axis
        die2 = self._roll_die()  # Optimization axis
        
        # Combined interpretation
        total = die1 + die2
        
        if die1 == die2:
            # Perfect alignment - high innovation
            return IdeaTier.INNOVATION, 0.9
        elif die1 > die2:
            # Logical dominance
            return IdeaTier.EXPLORATION, (die1 + die2) / 12
        else:
            # Intuitive dominance
            return IdeaTier.OPTIMIZATION, (die1 + die2) / 12
            
        # Fallback for repair bias
        if total <= 4:
            return IdeaTier.REPAIR, 0.3

    def generate_idea(
        self,
        title: str,
        description: str,
        context: Dict[str, Any],
        max_tokens: int = 1000
    ) -> IdeaNode:
        """Generate a new idea node based on dual-dice algorithm."""
        tier, confidence = self._dual_dice_generate()
        idea_id = hashlib.sha256(
            f"{title}:{len(self._ideas)}".encode()
        ).hexdigest()[:12]
        
        # Token cost estimation (simplified)
        token_cost = min(
            max_tokens,
            max(10, len(description) // 4)  # ~4 chars per token
        )
        
        # Enforce 2-of-own rule: idea must reference internal components
        dependencies = self._identify_dependencies(description)
        if len(dependencies) < 2 and len(context.get('related_skills', [])) >= 2:
            dependencies = (context.get('related_skills', [])[:2])
            
        idea = IdeaNode(
            id=idea_id,
            title=title,
            description=description,
            tier=tier,
            confidence=confidence,
            token_cost=token_cost,
            dependencies=dependencies,
            generated_by=f"dice({self._roll_history[-2:]})",
            lineage=context.get('parent_ideas', [])
        )
        
        self._ideas[idea_id] = idea
        return idea

    def _identify_dependencies(self, description: str) -> List[str]:
        """Extract potential dependencies by scanning for known skill references."""
        known_skills = list(self._ideas.keys()) + [
            'state_memory_manager', 'token_compressor', 'safety_gate',
            'circuit_breaker', 'health_watchdog', 'path_resolver',
            'metadata_extractor', 'pyramid_walker', 'persistent_state_store'
        ]
        
        found = []
        desc_lower = description.lower()
        for skill in known_skills:
            if skill in desc_lower:
                found.append(skill)
        return found

    def evolve_idea(self, idea_id: str, mutation: str) -> IdeaNode:
        """Apply mutation to an existing idea."""
        if idea_id not in self._ideas:
            raise ValueError(f"Unknown idea: {idea_id}")
            
        original = self._ideas[idea_id]
        new_idea = IdeaNode(
            id=hashlib.sha256(
                f"{idea_id}:{mutation}:{len(self._ideas)}".encode()
            ).hexdigest()[:12],
            title=f"{original.title} (evolved)",
            description=mutation,
            tier=original.tier,
            confidence=min(1.0, original.confidence + 0.1),  # Evolution improves confidence
            token_cost=max(10, original.token_cost + len(mutation) // 4),
            dependencies=original.dependencies + [idea_id],  # New dependency on parent
            generated_by=f"dice({self._roll_history[-2:]})",
            lineage=[idea_id] + original.lineage
        )
        
        self._ideas[new_idea.id] = new_idea
        return new_idea

    def select_best_ideas(self, count: int = 5) -> List[IdeaNode]:
        """Select top ideas by weighted score."""
        scored = []
        for idea in self._ideas.values():
            # Weighted score: confidence * 0.6 + (1/token_cost) * 0.4
            cost_factor = 1.0 / max(1, idea.token_cost / 100)
            weighted_score = (idea.confidence * 0.6) + (cost_factor * 0.4)
            scored.append((weighted_score, idea))
        
        scored.sort(reverse=True)
        return [idea for _, idea in scored[:count]]

    def get_lineage_depth(self, idea_id: str) -> int:
        """Calculate lineage depth (enforces no-A4 rule)."""
        depth = 0
        current_id = idea_id
        while current_id in self._ideas:
            idea = self._ideas[current_id]
            if not idea.lineage:
                break
            current_id = idea.lineage[0]
            depth += 1
            if depth > 10:  # Safety limit
                break
        return depth

    def export_to_state_db(self, store_path: str = "omnicore_ideas.json"):
        """Export all ideas to JSON for persistence."""
        data = {
            'seed': self._seed,
            'roll_history': self._roll_history,
            'ideas': [
                {
                    'id': idea.id,
                    'title': idea.title,
                    'description': idea.description,
                    'tier': idea.tier.value,
                    'confidence': idea.confidence,
                    'token_cost': idea.token_cost,
                    'dependencies': idea.dependencies,
                    'generated_by': idea.generated_by,
                    'lineage': idea.lineage
                }
                for idea in self._ideas.values()
            ]
        }
        
        Path(store_path).write_text(
            json.dumps(data, indent=2, default=str),
            encoding='utf-8'
        )
        return len(data['ideas'])
    
    @property
    def idea_count(self) -> int:
        return len(self._ideas)

# Singleton instance
ENGINE = IdeaEngine()
