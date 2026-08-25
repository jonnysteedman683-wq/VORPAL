"""
OMNICORE Consensus Resolver v1.0 — A4 Harmonizer
Decentralized consensus protocol for resolving state disagreements
across A1/A2/A3 agent layers using weighted voting.

Stolen from: p2p_state_registry.ts — weighted consensus algorithm
+ swarm_debate_engine.ts — authority-weighted voting
"""
import time
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ConsensusVote:
    proposal_id: str
    voter_id: str
    voter_role: str
    vote: Any
    weight: float
    confidence: float
    timestamp: float = field(default_factory=time.time)
    reason: str = ""


@dataclass
class ConsensusResult:
    proposal_id: str
    winning_value: Any
    winning_weight: float
    total_weight: float
    confidence: float
    votes_cast: int
    is_reached: bool
    minority_values: List[Any]
    details: Dict[str, Any] = field(default_factory=dict)


class ConsensusResolver:
    DEFAULT_THRESHOLD = 0.85
    ROLE_WEIGHTS = {
        "guard": 1.3,
        "architect": 1.2,
        "collaborator": 1.1,
        "executor": 1.0,
    }

    def __init__(self, threshold: float = None):
        self.threshold = threshold or self.DEFAULT_THRESHOLD
        self._proposals: Dict[str, List[ConsensusVote]] = defaultdict(list)
        self._resolved: Dict[str, ConsensusResult] = {}

    def propose(self, proposal_id: str, voter_id: str, voter_role: str,
                vote: Any, confidence: float = 1.0, reason: str = "") -> ConsensusVote:
        weight = self.ROLE_WEIGHTS.get(voter_role, 1.0)
        v = ConsensusVote(
            proposal_id=proposal_id, voter_id=voter_id, voter_role=voter_role,
            vote=vote, weight=weight, confidence=confidence, reason=reason,
        )
        self._proposals[proposal_id].append(v)
        return v

    def resolve(self, proposal_id: str, recent_threshold_s: float = 60.0) -> ConsensusResult:
        if proposal_id in self._resolved:
            return self._resolved[proposal_id]

        votes = self._proposals.get(proposal_id, [])
        if not votes:
            result = ConsensusResult(
                proposal_id=proposal_id, winning_value=None, winning_weight=0.0,
                total_weight=0.0, confidence=0.0, votes_cast=0, is_reached=False,
                minority_values=[], details={"reason": "no votes"},
            )
            self._resolved[proposal_id] = result
            return result

        now = time.time()
        recent = [v for v in votes if now - v.timestamp <= recent_threshold_s]
        if not recent:
            result = ConsensusResult(
                proposal_id=proposal_id, winning_value=None, winning_weight=0.0,
                total_weight=0.0, confidence=0.0, votes_cast=0, is_reached=False,
                minority_values=[], details={"reason": "no recent votes"},
            )
            self._resolved[proposal_id] = result
            return result

        value_groups: Dict[str, Tuple[Any, float, int]] = {}
        for v in recent:
            value_repr = json.dumps(v.vote, sort_keys=True, default=str)
            if value_repr not in value_groups:
                value_groups[value_repr] = (v.vote, 0.0, 0)
            prev_value, prev_weight, prev_count = value_groups[value_repr]
            effective_weight = v.weight * v.confidence
            value_groups[value_repr] = (prev_value, prev_weight + effective_weight, prev_count + 1)

        winning_repr = max(value_groups, key=lambda k: value_groups[k][1])
        winning_value, winning_weight, winning_votes = value_groups[winning_repr]

        total_weight = sum(w for _, w, _ in value_groups.values())
        confidence = winning_weight / total_weight if total_weight > 0 else 0.0
        is_reached = confidence >= self.threshold

        minority = [value_groups[k][0] for k in value_groups if k != winning_repr]

        result = ConsensusResult(
            proposal_id=proposal_id, winning_value=winning_value,
            winning_weight=winning_weight, total_weight=total_weight,
            confidence=confidence, votes_cast=winning_votes, is_reached=is_reached,
            minority_values=minority,
            details={"threshold": self.threshold, "total_votes": len(recent), "value_groups": len(value_groups)},
        )
        self._resolved[proposal_id] = result
        return result

    def resolve_all(self) -> Dict[str, ConsensusResult]:
        results = {}
        for pid in list(self._proposals.keys()):
            if pid not in self._resolved:
                results[pid] = self.resolve(pid)
        return results

    def get_proposal_votes(self, proposal_id: str) -> List[ConsensusVote]:
        return list(self._proposals.get(proposal_id, []))

    def summary(self) -> dict:
        resolved_count = len(self._resolved)
        pending_count = len(self._proposals) - resolved_count
        reached = sum(1 for r in self._resolved.values() if r.is_reached)
        return {
            "proposals_total": len(self._proposals),
            "resolved": resolved_count,
            "pending": pending_count,
            "consensus_reached": reached,
            "threshold": self.threshold,
            "role_weights": self.ROLE_WEIGHTS,
        }
