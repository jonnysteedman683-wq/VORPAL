"""
OMNICORE Synthesis Engine v1.0 — A4 Harmonizer
Cross-layer output synthesis: merges, deduplicates, and resolves
conflicting outputs from A1/A2/A3 agents into unified results.

Stolen from: tri_agentic_kernel.ts + swarm_debate_engine.ts
+ OMNICORE-A1/src/lib/swarm_debate_engine.ts (conflict resolution patterns)
"""
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class SynthesisInput:
    """A single agent's output for synthesis."""
    agent_id: str  # "A1", "A2", "A3"
    agent_role: str  # "guard", "executor", "architect"
    content: Any
    confidence: float  # 0.0-1.0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SynthesisResult:
    """Unified output after synthesis."""
    synthesized_content: Any
    contributing_agents: List[str]
    confidence: float
    method: str  # "consensus" | "weighted_merge" | "conflict_resolution" | "single_source"
    conflict_detected: bool
    details: Dict[str, Any] = field(default_factory=dict)


class SynthesisEngine:
    """
    A4 Harmonizer core: takes multiple agent outputs and synthesizes one result.

    Strategies (in priority order):
    1. Single source — only one agent contributed
    2. Exact consensus — all agents agree on identical content
    3. Weighted merge — merge based on agent authority weights
    4. Conflict resolution — detect and resolve disagreements
    """

    ROLE_WEIGHTS = {
        "guard": 1.3,
        "executor": 1.0,
        "architect": 1.2,
        "collaborator": 1.1,
    }

    def __init__(self):
        self._synthesis_history: list = []

    def synthesize(self, inputs: List[SynthesisInput]) -> SynthesisResult:
        if not inputs:
            return SynthesisResult(
                synthesized_content=None,
                contributing_agents=[],
                confidence=0.0,
                method="none",
                conflict_detected=False,
                details={"reason": "no inputs"},
            )

        if len(inputs) == 1:
            inp = inputs[0]
            return SynthesisResult(
                synthesized_content=inp.content,
                contributing_agents=[inp.agent_id],
                confidence=inp.confidence,
                method="single_source",
                conflict_detected=False,
            )

        contents = [self._serialize(i.content) for i in inputs]
        if len(set(contents)) == 1:
            avg_conf = sum(i.confidence for i in inputs) / len(inputs)
            return SynthesisResult(
                synthesized_content=inputs[0].content,
                contributing_agents=[i.agent_id for i in inputs],
                confidence=avg_conf,
                method="consensus",
                conflict_detected=False,
            )

        conflicts = self._detect_conflicts(inputs)
        if conflicts:
            resolved = self._resolve_conflicts(inputs, conflicts)
            return SynthesisResult(
                synthesized_content=resolved,
                contributing_agents=[i.agent_id for i in inputs],
                confidence=self._compute_confidence(inputs, method="conflict_resolution"),
                method="conflict_resolution",
                conflict_detected=True,
                details={"conflicts": conflicts, "resolved": True},
            )

        merged = self._weighted_merge(inputs)
        return SynthesisResult(
            synthesized_content=merged,
            contributing_agents=[i.agent_id for i in inputs],
            confidence=self._compute_confidence(inputs, method="weighted_merge"),
            method="weighted_merge",
            conflict_detected=False,
        )

    def _serialize(self, content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, (str, int, float, bool)):
            return str(content)
        if isinstance(content, dict):
            return str(sorted((k, self._serialize(v)) for k, v in content.items()))
        if isinstance(content, (list, tuple)):
            return str([self._serialize(item) for item in content])
        return str(content)

    def _detect_conflicts(self, inputs: List[SynthesisInput]) -> List[dict]:
        conflicts = []
        content_by_agent = {}
        for inp in inputs:
            if isinstance(inp.content, dict):
                content_by_agent[inp.agent_id] = inp.content

        if len(content_by_agent) < 2:
            return conflicts

        all_keys = set()
        for c in content_by_agent.values():
            all_keys.update(c.keys())

        for key in all_keys:
            values_by_agent = {}
            for agent_id, content in content_by_agent.items():
                if key in content:
                    values_by_agent[agent_id] = self._serialize(content[key])

            unique_values = set(values_by_agent.values())
            if len(unique_values) > 1:
                conflicts.append({
                    "key": key,
                    "values": {
                        agent: content_by_agent[agent].get(key)
                        for agent in content_by_agent
                        if key in content_by_agent[agent]
                    },
                    "agents_disagree": list(values_by_agent.keys()),
                })

        return conflicts

    def _resolve_conflicts(self, inputs: List[SynthesisInput],
                           conflicts: List[dict]) -> dict:
        content_by_agent = {}
        role_by_agent = {}
        for inp in inputs:
            content_by_agent[inp.agent_id] = inp.content
            role_by_agent[inp.agent_id] = inp.agent_role

        merged = {}
        for content in content_by_agent.values():
            if isinstance(content, dict):
                merged.update(content)

        for conflict in conflicts:
            key = conflict["key"]
            best_agent = None
            best_weight = -1
            for agent_id in conflict["agents_disagree"]:
                role = role_by_agent.get(agent_id, "executor")
                weight = self.ROLE_WEIGHTS.get(role, 1.0)
                if weight > best_weight:
                    best_weight = weight
                    best_agent = agent_id

            if best_agent and best_agent in content_by_agent:
                merged[key] = content_by_agent[best_agent].get(key)

        return merged

    def _weighted_merge(self, inputs: List[SynthesisInput]) -> dict:
        if not inputs:
            return {}

        all_keys = set()
        for inp in inputs:
            if isinstance(inp.content, dict):
                all_keys.update(inp.content.keys())

        if not all_keys:
            best = max(inputs, key=lambda i: i.confidence * self.ROLE_WEIGHTS.get(i.agent_role, 1.0))
            return best.content if isinstance(best.content, dict) else {"value": best.content}

        merged = {}
        for key in all_keys:
            values = []
            for inp in inputs:
                if isinstance(inp.content, dict) and key in inp.content:
                    values.append((inp, inp.content[key]))

            if not values:
                continue

            numeric_vals = []
            for inp, val in values:
                if isinstance(val, (int, float)):
                    weight = self.ROLE_WEIGHTS.get(inp.agent_role, 1.0)
                    numeric_vals.append((val, weight, inp.confidence))

            if numeric_vals and len(numeric_vals) == len(values):
                total_weight = sum(w * c for _, w, c in numeric_vals)
                if total_weight > 0:
                    weighted_avg = sum(v * w * c for v, w, c in numeric_vals) / total_weight
                    merged[key] = weighted_avg
                else:
                    merged[key] = numeric_vals[0][0]
            else:
                best = max(values, key=lambda x: self.ROLE_WEIGHTS.get(x[0].agent_role, 1.0))
                merged[key] = best[1]

        return merged

    def _compute_confidence(self, inputs: List[SynthesisInput], method: str) -> float:
        if not inputs:
            return 0.0
        avg_conf = sum(i.confidence for i in inputs) / len(inputs)
        if method == "single_source":
            return inputs[0].confidence
        elif method == "consensus":
            return min(avg_conf + 0.1, 1.0)
        elif method == "conflict_resolution":
            return avg_conf * 0.9
        else:
            return avg_conf

    def get_history(self, limit: int = 50) -> list:
        return self._synthesis_history[-limit:]

    def record_synthesis(self, result: SynthesisResult, context: str = ""):
        self._synthesis_history.append({
            "timestamp": time.time(),
            "method": result.method,
            "confidence": result.confidence,
            "conflict_detected": result.conflict_detected,
            "agents": result.contributing_agents,
            "context": context,
        })
