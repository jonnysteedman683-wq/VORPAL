"""
OMNICORE Conflict Mediator v1.0 — A4 Harmonizer
Detects and mediates conflicts between agent outputs using
semantic analysis, authority weighting, and reconciliation strategies.

Stolen from: swarm_debate_engine.ts — conflict detection and resolution
+ tri_agentic_kernel.ts — personality-based arbitration
"""
import time
import difflib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class ConflictType(Enum):
    VALUE_DIVERGENCE = "value_divergence"
    STRUCTURAL_MISMATCH = "structural_mismatch"
    CONFIDENCE_GAP = "confidence_gap"
    ROLE_CONFLICT = "role_conflict"
    MISSING_CONTENT = "missing_content"


class MediationOutcome(Enum):
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    COMPROMISED = "compromised"
    UNCHANGED = "unchanged"


@dataclass
class Conflict:
    conflict_type: ConflictType
    agents_involved: List[str]
    description: str
    severity: float
    location: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MediationResult:
    outcome: MediationOutcome
    resolution: Any
    confidence: float
    method_used: str
    conflicts_addressed: int
    unresolved_conflicts: List[Conflict]
    details: Dict[str, Any] = field(default_factory=dict)


class ConflictMediator:
    CONFIDENCE_GAP_THRESHOLD = 0.3
    ROLE_CONFLICT_PAIRS = [("guard", "architect")]

    def __init__(self):
        self._mediation_history: list = []

    def detect_conflicts(self, inputs: List[dict]) -> List[Conflict]:
        conflicts = []
        if len(inputs) < 2:
            return conflicts

        dict_inputs = [(i, inp) for i, inp in enumerate(inputs) if isinstance(inp.get("content"), dict)]

        if len(dict_inputs) >= 2:
            conflicts.extend(self._detect_value_divergences(dict_inputs, inputs))
            conflicts.extend(self._detect_structural_mismatches(dict_inputs, inputs))

        conflicts.extend(self._detect_confidence_gaps(inputs))
        conflicts.extend(self._detect_role_conflicts(inputs))

        for c in conflicts:
            c.severity = self._compute_severity(c, inputs)

        return conflicts

    def _detect_value_divergences(self, dict_inputs: List[tuple], all_inputs: List[dict]) -> List[Conflict]:
        conflicts = []
        seen_keys = set()
        for idx1, inp1 in dict_inputs:
            content1 = inp1["content"]
            agent1 = all_inputs[idx1]["agent_id"]
            for idx2, inp2 in dict_inputs:
                if idx1 >= idx2:
                    continue
                content2 = inp2["content"]
                agent2 = all_inputs[idx2]["agent_id"]
                for key in set(content1.keys()) & set(content2.keys()):
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    val1, val2 = content1[key], content2[key]
                    if self._values_differ(val1, val2):
                        severity = self._divergence_severity(val1, val2)
                        conflicts.append(Conflict(
                            conflict_type=ConflictType.VALUE_DIVERGENCE,
                            agents_involved=[agent1, agent2],
                            description=f"Key '{key}': {self._short_repr(val1)} vs {self._short_repr(val2)}",
                            severity=severity,
                            location=f"key:{key}",
                            details={"key": key, "agent1_value": val1, "agent2_value": val2, "agent1": agent1, "agent2": agent2},
                        ))
        return conflicts

    def _detect_structural_mismatches(self, dict_inputs: List[tuple], all_inputs: List[dict]) -> List[Conflict]:
        conflicts = []
        all_keys = set()
        key_owners = defaultdict(list)
        for idx, inp in dict_inputs:
            content = inp["content"]
            agent = all_inputs[idx]["agent_id"]
            for key in content:
                all_keys.add(key)
                key_owners[key].append(agent)

        for key, owners in key_owners.items():
            if len(owners) < len(dict_inputs):
                missing = [all_inputs[idx]["agent_id"] for idx, _ in dict_inputs if all_inputs[idx]["agent_id"] not in owners]
                conflicts.append(Conflict(
                    conflict_type=ConflictType.MISSING_CONTENT,
                    agents_involved=missing,
                    description=f"Key '{key}' missing from: {', '.join(missing)}",
                    severity=0.3, location=f"key:{key}",
                    details={"key": key, "missing_from": missing},
                ))
        return conflicts

    def _detect_confidence_gaps(self, inputs: List[dict]) -> List[Conflict]:
        conflicts = []
        for i, inp1 in enumerate(inputs):
            for j, inp2 in enumerate(inputs):
                if i >= j:
                    continue
                gap = abs(inp1["confidence"] - inp2["confidence"])
                if gap >= self.CONFIDENCE_GAP_THRESHOLD:
                    conflicts.append(Conflict(
                        conflict_type=ConflictType.CONFIDENCE_GAP,
                        agents_involved=[inp1["agent_id"], inp2["agent_id"]],
                        description=f"Confidence gap: {inp1['confidence']:.2f} vs {inp2['confidence']:.2f} (gap={gap:.2f})",
                        severity=min(gap, 1.0), location="confidence",
                        details={"agent1_conf": inp1["confidence"], "agent2_conf": inp2["confidence"], "gap": gap},
                    ))
        return conflicts

    def _detect_role_conflicts(self, inputs: List[dict]) -> List[Conflict]:
        conflicts = []
        for i, inp1 in enumerate(inputs):
            for j, inp2 in enumerate(inputs):
                if i >= j:
                    continue
                role1, role2 = inp1.get("agent_role", ""), inp2.get("agent_role", "")
                pair = tuple(sorted([role1, role2]))
                if pair in [tuple(sorted(p)) for p in self.ROLE_CONFLICT_PAIRS]:
                    conflicts.append(Conflict(
                        conflict_type=ConflictType.ROLE_CONFLICT,
                        agents_involved=[inp1["agent_id"], inp2["agent_id"]],
                        description=f"Role conflict: {role1} ({inp1['agent_id']}) vs {role2} ({inp2['agent_id']})",
                        severity=0.5, location="role",
                        details={"role1": role1, "role2": role2, "agent1": inp1["agent_id"], "agent2": inp2["agent_id"]},
                    ))
        return conflicts

    def _values_differ(self, v1: Any, v2: Any) -> bool:
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            if v1 == v2:
                return False
            max_val = max(abs(v1), abs(v2), 1e-10)
            return abs(v1 - v2) / max_val > 0.01
        if isinstance(v1, str) and isinstance(v2, str):
            return v1 != v2
        return self._serialize(v1) != self._serialize(v2)

    def _divergence_severity(self, v1: Any, v2: Any) -> float:
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            max_val = max(abs(v1), abs(v2), 1e-10)
            return min(abs(v1 - v2) / max_val, 1.0)
        if isinstance(v1, str) and isinstance(v2, str):
            return 1.0 - difflib.SequenceMatcher(None, v1, v2).ratio()
        return 0.5

    def _compute_severity(self, conflict: Conflict, inputs: List[dict]) -> float:
        return conflict.severity

    def _serialize(self, v: Any) -> str:
        if v is None:
            return "null"
        if isinstance(v, (int, float, str, bool)):
            return str(v)
        return str(type(v).__name__)

    def _short_repr(self, v: Any) -> str:
        s = self._serialize(v)
        return s[:47] + "..." if len(s) > 50 else s

    def mediate(self, inputs: List[dict], conflicts: List[Conflict] = None) -> MediationResult:
        if conflicts is None:
            conflicts = self.detect_conflicts(inputs)

        if not conflicts and len(inputs) >= 1:
            best = max(inputs, key=lambda i: i["confidence"])
            return MediationResult(
                outcome=MediationOutcome.UNCHANGED, resolution=best.get("content"),
                confidence=best["confidence"], method_used="no_conflicts",
                conflicts_addressed=0, unresolved_conflicts=[],
            )

        if not inputs:
            return MediationResult(
                outcome=MediationOutcome.UNCHANGED, resolution=None, confidence=0.0,
                method_used="no_inputs", conflicts_addressed=0, unresolved_conflicts=conflicts,
            )

        by_type: Dict[ConflictType, List[Conflict]] = defaultdict(list)
        for c in conflicts:
            by_type[c.conflict_type].append(c)

        resolution = self._merge_contents(inputs)
        addressed = 0
        unresolved = []

        for ctype, cfs in by_type.items():
            if ctype == ConflictType.VALUE_DIVERGENCE:
                resolution = self._mediate_value_divergences(resolution, cfs, inputs)
                addressed += len(cfs)
            elif ctype == ConflictType.CONFIDENCE_GAP:
                resolution = self._mediate_confidence_gaps(resolution, cfs, inputs)
                addressed += len(cfs)
            elif ctype == ConflictType.ROLE_CONFLICT:
                resolution = self._mediate_role_conflicts(resolution, cfs, inputs)
                addressed += len(cfs)
            elif ctype == ConflictType.MISSING_CONTENT:
                resolution = self._mediate_missing_content(resolution, cfs, inputs)
                addressed += len(cfs)
            else:
                unresolved.extend(cfs)

        if unresolved:
            outcome = MediationOutcome.COMPROMISED if addressed > 0 else MediationOutcome.DEFERRED
        elif addressed > 0:
            outcome = MediationOutcome.RESOLVED
        else:
            outcome = MediationOutcome.UNCHANGED

        avg_conf = sum(i.get("confidence", 0) for i in inputs) / max(len(inputs), 1)
        confidence = avg_conf * (0.9 if unresolved else 1.0)

        return MediationResult(
            outcome=outcome, resolution=resolution, confidence=confidence,
            method_used=self._describe_methods(by_type),
            conflicts_addressed=addressed, unresolved_conflicts=unresolved,
        )

    def _merge_contents(self, inputs: List[dict]) -> dict:
        merged = {}
        for inp in inputs:
            content = inp.get("content")
            if isinstance(content, dict):
                merged.update(content)
        return merged

    def _mediate_value_divergences(self, current: dict, conflicts: List[Conflict], inputs: List[dict]) -> dict:
        agent_info = {inp["agent_id"]: inp for inp in inputs}
        role_weights = {"guard": 1.3, "architect": 1.2, "collaborator": 1.1, "executor": 1.0}
        for c in conflicts:
            key = c.details.get("key")
            if not key:
                continue
            best_agent, best_weight = None, -1
            for agent_id in c.agents_involved:
                info = agent_info.get(agent_id, {})
                role = info.get("agent_role", "executor")
                conf = info.get("confidence", 0.5)
                weight = role_weights.get(role, 1.0) * conf
                if weight > best_weight:
                    best_weight = weight
                    best_agent = agent_id
            if best_agent and best_agent in agent_info:
                content = agent_info[best_agent].get("content", {})
                if isinstance(content, dict) and key in content:
                    current[key] = content[key]
        return current

    def _mediate_confidence_gaps(self, current: dict, conflicts: List[Conflict], inputs: List[dict]) -> dict:
        best = max(inputs, key=lambda i: i.get("confidence", 0))
        content = best.get("content", {})
        if isinstance(content, dict):
            current.update(content)
        return current

    def _mediate_role_conflicts(self, current: dict, conflicts: List[Conflict], inputs: List[dict]) -> dict:
        guard_inputs = [i for i in inputs if i.get("agent_role") == "guard"]
        if guard_inputs:
            best_guard = max(guard_inputs, key=lambda i: i.get("confidence", 0))
            content = best_guard.get("content", {})
            if isinstance(content, dict):
                current.update(content)
        return current

    def _mediate_missing_content(self, current: dict, conflicts: List[Conflict], inputs: List[dict]) -> dict:
        for inp in inputs:
            content = inp.get("content", {})
            if isinstance(content, dict):
                current.update(content)
        return current

    def _describe_methods(self, by_type: Dict) -> str:
        methods = []
        if ConflictType.VALUE_DIVERGENCE in by_type:
            methods.append("authority_arbitration")
        if ConflictType.CONFIDENCE_GAP in by_type:
            methods.append("confidence_priority")
        if ConflictType.ROLE_CONFLICT in by_type:
            methods.append("guard_priority")
        if ConflictType.MISSING_CONTENT in by_type:
            methods.append("key_merge")
        return "+".join(methods) if methods else "none"

    def get_history(self, limit: int = 50) -> list:
        return self._mediation_history[-limit:]

    def record_mediation(self, result: MediationResult, context: str = ""):
        self._mediation_history.append({
            "timestamp": time.time(), "outcome": result.outcome.value,
            "confidence": result.confidence, "conflicts_addressed": result.conflicts_addressed,
            "method": result.method_used, "context": context,
        })
