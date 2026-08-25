"""
OMNICORE Tri-Agentic Kernel — Python Port v1.0
Stolen from: OMNICORE-A1/lib/tri_agentic_kernel.ts (499 lines)
+ OMNICORE-A1/types/neurointent.ts (98 lines)
+ OMNICORE-A1/lib/safety_gate.ts (133 lines)
+ OMNICORE-A1/lib/cost_router.ts (165 lines)
+ OMNICORE-A1/lib/dispatcher.ts (63 lines)
+ OMNICORE-A1/lib/event_bus.ts (70 lines)
+ OMNICORE-A1/lib/omni_swarm_adapter.ts (124 lines)
+ OMNICORE-A1/lib/upgrade_registry.ts (240 lines)
+ OMNICORE-A1/lib/swarm_debate_engine.ts (250 lines)
+ OMNICORE-A1/lib/p2p_state_registry.ts (215 lines)
+ OMNICORE-A1/lib/a4_synthesizer.ts (178 lines)

Single-codebase architecture with personality-driven behavior.
A1 = Gatekeeper/Skeptic, A2 = Optimizer/Pragmatist, A3 = Architect/Visionary

Usage:
    from tri_agentic_kernel import TriAgenticKernel
    kernel = TriAgenticKernel(personality='a1')  # The Gatekeeper
    result = kernel.process_intent(intent)
"""
import time
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import deque
from enum import Enum


# ─── Types (stolen from: neurointent.ts) ───

class NeuroIntentSource(Enum):
    EEG = "eeg"
    MOCK = "mock"
    AUDIO = "audio"
    BCI = "bci"
    EGEG = "egeg"
    SIMULATION = "simulation"


class SwarmActionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class NodeStatus(Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"
    SYNCING = "syncing"


# ─── Safety Policy (stolen from: safety_gate.ts) ───

DEFAULT_SAFETY_POLICY = {
    "allowedIntents": ["route", "execute", "query", "observe",
                        "route_neural_path", "knowledge_extraction",
                        "infra", "upgrade", "lint", "task_1", "task_2"],
    "blockedIntents": ["override_system", "destructive_action", "unauthorized_command"],
    "confidenceThreshold": 0.7,
    "maxCostUSD": 5.0,
    "allowedFeatures": ["alpha_power", "beta_alpha_ratio", "asymmetry", "quality"],
    "minQualityThreshold": 0.3,
    "maxRatePerMin": 60
}

ALLOWED_INTENTS_SET = {"route", "execute", "query", "observe"}
ALLOWED_FEATURE_KEYS_SET = {"alpha_power", "beta_alpha_ratio", "asymmetry", "quality"}


def evaluate_safety(intent: dict) -> dict:
    """
    Pure function version — ported from safety_gate.ts evaluateSafety().
    Stolen from: neurocore/core/safety_gate.ts + safety_gate.ts
    """
    if intent.get("intent") not in ALLOWED_INTENTS_SET:
        return {"allowed": False, "reason": "blocked_intent", "requiresOperator": True, "riskLevel": "high"}
    
    if intent.get("confidence", 0) < 0.75:
        return {"allowed": False, "reason": f"Confidence {intent['confidence']} below threshold 0.75",
                "requiresOperator": True, "riskLevel": "high"}
    
    features = intent.get("features", {})
    if isinstance(features, dict):
        invalid_keys = [k for k in features if k not in ALLOWED_FEATURE_KEYS_SET]
        if invalid_keys:
            return {"allowed": False, "reason": f"Feature keys [{', '.join(invalid_keys)}] not in allowlist",
                    "requiresOperator": True, "riskLevel": "moderate"}
    
    requires_operator = intent.get("confidence", 0) < 0.85
    risk_level = "moderate" if requires_operator else "low"
    return {"allowed": True, "reason": "ok", "requiresOperator": requires_operator, "riskLevel": risk_level}


class SafetyGate:
    """
    Safety gate with multi-layer policy enforcement.
    Ported from: safety_gate.ts — intent timestamp rate limiting, confidence threshold,
    biometric dead-man switch, cost enforcement.
    """
    
    def __init__(self, policy: dict = None):
        self.policy = {**DEFAULT_SAFETY_POLICY, **(policy or {})}
        self.intent_timestamps: deque = deque()
    
    def evaluate(self, intent: dict) -> dict:
        threshold = self.policy.get("confidenceThreshold", 0.7)
        start_time = time.time()
        
        # Rule 0: Biometric signal quality dead-man switch
        features = intent.get("features", {})
        if isinstance(features, dict) and "quality" in features:
            min_quality = self.policy.get("minQualityThreshold", 0.3)
            if isinstance(features.get("quality"), (int, float)) and features["quality"] < min_quality:
                return {"allowed": False, "reason": "degraded_signal_quality", "requiresOperator": True, "riskLevel": "high"}
        
        # Rule 0b: Alpha power validation
        if isinstance(features, dict) and "alpha_power" in features:
            if isinstance(features.get("alpha_power"), (int, float)) and features["alpha_power"] < 0.5:
                return {"allowed": False, "reason": "insufficient_alpha_power", "requiresOperator": True, "riskLevel": "moderate"}
        
        # Rule 1: Low confidence check
        if intent.get("confidence", 0) < threshold:
            return {"allowed": False, "reason": "low_confidence", "requiresOperator": True, "riskLevel": "high"}
        
        # Rule 2: Blocked intent check
        blocked = self.policy.get("blockedIntents", [])
        if intent.get("intent") in blocked:
            return {"allowed": False, "reason": "blocked_intent", "requiresOperator": True, "riskLevel": "high"}
        
        # Rule 3: Allowed intent check
        allowed = self.policy.get("allowedIntents", [])
        if intent.get("intent") not in allowed:
            return {"allowed": False, "reason": "unknown_intent", "requiresOperator": True, "riskLevel": "high"}
        
        # Rule 4: Feature key validation
        if isinstance(features, dict) and features:
            allowed_features = set(self.policy.get("allowedFeatures", []))
            feature_keys = set(features.keys())
            has_disallowed = feature_keys - allowed_features
            if has_disallowed:
                return {"allowed": False, "reason": "feature_blocked", "requiresOperator": True, "riskLevel": "moderate"}
        
        # Rule 5: Rate limiting (deque-based sliding window)
        now = time.time()
        while self.intent_timestamps and now - self.intent_timestamps[0] > 60:
            self.intent_timestamps.popleft()
        max_rate = self.policy.get("maxRatePerMin", 60)
        if len(self.intent_timestamps) >= max_rate:
            return {"allowed": False, "reason": "rate_limited", "requiresOperator": False, "riskLevel": "moderate"}
        self.intent_timestamps.append(now)
        
        # Rule 6: Cost enforcement
        if "maxCostUSD" in self.policy:
            quality = features.get("quality", 0) if isinstance(features, dict) else 0
            estimated_cost = (quality or 0) * 0.1
            if estimated_cost > self.policy["maxCostUSD"]:
                return {"allowed": False, "reason": "cost_exceeds_limit", "requiresOperator": True, "riskLevel": "moderate"}
        
        duration_ms = (time.time() - start_time) * 1000
        requires_operator = intent.get("confidence", 0) < 0.85
        risk_level = "moderate" if requires_operator else "low"
        return {"allowed": True, "reason": "ok", "requiresOperator": requires_operator, "riskLevel": risk_level}


# ─── Cost-Aware Router (stolen from: cost_router.ts) ───

class CostAwareRouter:
    """
    Semantic intent routing with model selection.
    Ported from: markus_router.py + cost_router.ts
    """
    
    MODEL_CODE_FAST = "openrouter/poolside/laguna-s-2.1:free"
    MODEL_MEGACONTEXT_ARCH = "openrouter/nvidia/nemotron-3-ultra:free"
    MODEL_REALTIME_LINT = "openrouter/inclusionai/ling-3.0-flash:free"
    MODEL_AIRGAPPED_LOCAL = "custom/qwen2.5-coder:7b"
    
    COST_PER_TOKEN = {
        "openrouter/poolside/laguna-s-2.1:free": 0.0,
        "openrouter/nvidia/nemotron-3-ultra:free": 0.0,
        "openrouter/inclusionai/ling-3.0-flash:free": 0.0,
        "custom/qwen2.5-coder:7b": 0.0
    }
    
    def __init__(self):
        self.code_patterns = re.compile(
            r'\b(def|class|function|import|refactor|optimize|ast|compile|bug|test|async|return)\b', re.IGNORECASE
        )
        self.arch_patterns = re.compile(
            r'\b(architecture|multi-file|roadmap|system design|pipeline|migrate|database schema|specification)\b', re.IGNORECASE
        )
        self.lint_patterns = re.compile(
            r'\b(status|health|ping|check|lint|preflight|metrics|heartbeat)\b', re.IGNORECASE
        )
        self.free_tier_models = {
            self.MODEL_CODE_FAST,
            self.MODEL_REALTIME_LINT,
            self.MODEL_AIRGAPPED_LOCAL
        }
    
    def estimate_cost(self, decision: dict) -> float:
        return decision.get("estimatedTokens", 0) * 0.00001
    
    def route_intent(self, prompt: str, context_tokens: int = 0, is_offline: bool = False) -> dict:
        """Route intent to optimal model based on semantic analysis."""
        estimated_tokens = len(prompt.split()) * 2 + context_tokens
        
        if is_offline:
            return {
                "targetModel": self.MODEL_AIRGAPPED_LOCAL,
                "provider": "custom",
                "tierCategory": "OFFLINE_LOCAL",
                "confidence": 1.0,
                "reason": "System offline / local fallback mode requested.",
                "estimatedTokens": estimated_tokens
            }
        
        if estimated_tokens > 15000 or self.arch_patterns.search(prompt):
            return {
                "targetModel": self.MODEL_MEGACONTEXT_ARCH,
                "provider": "openrouter",
                "tierCategory": "MEGACONTEXT_ARCH",
                "confidence": 0.92,
                "reason": "Detected high token volume or broad system architecture planning scope.",
                "estimatedTokens": estimated_tokens
            }
        
        if self.code_patterns.search(prompt):
            return {
                "targetModel": self.MODEL_CODE_FAST,
                "provider": "openrouter",
                "tierCategory": "CODE_SPECIALIST",
                "confidence": 0.95,
                "reason": "Detected code refactoring, AST optimization, or functional implementation.",
                "estimatedTokens": estimated_tokens
            }
        
        if self.lint_patterns.search(prompt):
            return {
                "targetModel": self.MODEL_REALTIME_LINT,
                "provider": "openrouter",
                "tierCategory": "FAST_TELEMETRY",
                "confidence": 0.90,
                "reason": "Detected fast status, health, or telemetry inspection intent.",
                "estimatedTokens": estimated_tokens
            }
        
        return {
            "targetModel": self.MODEL_CODE_FAST,
            "provider": "openrouter",
            "tierCategory": "DEFAULT_BALANCED",
            "confidence": 0.85,
            "reason": "Balanced default routing via Laguna S 2.1 MoE.",
            "estimatedTokens": estimated_tokens
        }
    
    def route_neuro_intent(self, intent: dict, prompt: str) -> dict:
        """Extended routing using neuro intent features."""
        features = intent.get("features", {})
        confidence = intent.get("confidence", 0)
        
        if confidence >= 0.9 and features.get("band") == "alpha":
            return {
                "targetModel": self.MODEL_CODE_FAST,
                "provider": "openrouter",
                "tierCategory": "HIGH_CONF_ALPHA",
                "confidence": confidence,
                "reason": "High-confidence alpha band intent routed to primary coding model.",
                "estimatedTokens": 0
            }
        
        if confidence < 0.8:
            return {
                "targetModel": self.MODEL_REALTIME_LINT,
                "provider": "openrouter",
                "tierCategory": "LOW_CONF_VALIDATION",
                "confidence": confidence,
                "reason": "Low confidence intent routed for quick validation.",
                "estimatedTokens": 0
            }
        
        return self.route_intent(prompt, 0, False)


import re  # Move to top in production


# ─── Event Bus (stolen from: event_bus.ts) ───

class EventBus:
    """
    Typed system-wide event dispatching.
    Ported from: event_bus.ts — type-safe event emission with error isolation.
    """
    
    def __init__(self):
        self._listeners: Dict[str, List] = {}
    
    def on(self, event: str, handler) -> callable:
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(handler)
        return lambda: self._listeners[event].remove(handler) if handler in self._listeners[event] else None
    
    def once(self, event: str, handler) -> callable:
        def wrapper(data):
            self._listeners[event].remove(wrapper)
            handler(data)
        return self.on(event, wrapper)
    
    def emit(self, event: str, data: Any = None):
        if event in self._listeners:
            for handler in list(self._listeners[event]):
                try:
                    handler(data)
                except Exception as e:
                    print(f"[EventBus] Error in handler for '{event}': {e}")
    
    def remove_all_listeners(self, event: str = None):
        if event:
            self._listeners.pop(event, None)
        else:
            self._listeners = {}


# ─── Routing Table (stolen from: dispatcher.ts) ───

ROUTING_TABLE = {
    "infra": ["ag"],
    "upgrade": ["ag"],
    "lint": ["ag"],
    "neural": ["as"],
    "signal": ["as"],
    "decode": ["as"],
    "code": ["jules"],
    "review": ["jules"],
    "test": ["jules"]
}

DEFAULT_STREAM = "hermes"


def dispatch_intent(intent: dict, safety: dict = None) -> dict:
    """Route validated intents to agent streams."""
    if safety is None:
        safety = evaluate_safety(intent)
    
    if not safety.get("allowed", False):
        return {
            "intentId": intent.get("id", "unknown"),
            "routedTo": "blocked",
            "status": "rejected",
            "reason": safety.get("reason", "unknown")
        }
    
    routed_to = DEFAULT_STREAM
    category_match = ROUTING_TABLE.get(intent.get("intent", "").lower())
    if category_match and category_match:
        routed_to = category_match[0]
    
    status = "queued" if intent.get("requiresConfirmation", False) else "dispatched"
    
    return {
        "intentId": intent.get("id", "unknown"),
        "routedTo": routed_to,
        "status": status,
        "reason": f"{safety.get('reason', 'unknown')} → {routed_to}"
    }


# ─── Tri-Agentic Kernel (stolen from: tri_agentic_kernel.ts) ───

@dataclass
class AgentPersonality:
    name: str
    description: str
    confidenceThreshold: float
    riskTolerance: str  # 'low' | 'medium' | 'high' | 'none'
    cronSchedule: str
    motto: str
    triadRole: str  # 'guard' | 'executor' | 'architect' | 'editor' | 'base'
    costBudgetUSD: float = 0.0
    requiresSignalQuality: bool = False
    thoroughness: float = 1.0


PERSONALITIES = {
    "a1": AgentPersonality(
        name="The Gatekeeper",
        description="Skeptic — cautious, methodical, security-first",
        confidenceThreshold=0.80,
        riskTolerance="low",
        cronSchedule="every tick",
        motto="Trust, but verify",
        triadRole="guard",
        requiresSignalQuality=True,
        thoroughness=0.95
    ),
    "a2": AgentPersonality(
        name="The Optimizer",
        description="Pragmatist — cost-conscious, efficiency-obsessed",
        confidenceThreshold=0.70,
        riskTolerance="medium",
        cronSchedule="*/30 * * * *",
        motto="What's the ROI?",
        triadRole="executor"
    ),
    "a3": AgentPersonality(
        name="The Architect",
        description="Visionary — creative, big-picture, ambitious",
        confidenceThreshold=0.65,
        riskTolerance="high",
        cronSchedule="0 */2 * * *",
        motto="What could be?",
        triadRole="architect"
    ),
    "a4": AgentPersonality(
        name="The Editor",
        description="Editor — collective file editor, upgrade-path optimizer",
        confidenceThreshold=1.0,
        riskTolerance="none",
        cronSchedule="on-demand",
        motto="Refine, then re-watermark",
        triadRole="editor"
    ),
    "base": AgentPersonality(
        name="The Base",
        description="Merged best-of-A1/A2/A3 canonical foundation (safety + cost + vision)",
        confidenceThreshold=0.80,
        riskTolerance="low",
        cronSchedule="every tick",
        motto="Best of all, foundations for one",
        triadRole="base",
        requiresSignalQuality=True,
        thoroughness=0.95
    ),
}

# Role authority weights (stolen from: swarm_debate_engine.ts)
ROLE_AUTHORITY_WEIGHTS = {
    "guard": 1.3,    # A1 — highest authority
    "executor": 1.0,   # A2 — execution weight
    "architect": 1.2,  # A3 — visionary weight
    "editor": 1.0,     # A4 — non-debating
    "base": 1.0        # BASE — merged foundation
}


@dataclass
class EvolutionMetrics:
    cycle: int = 0
    reward: float = 0.0
    provider: str = "default"
    routeEfficiency: float = 0.0
    skillMutationRate: float = 0.0
    avgConfidence: float = 0.0
    intentCount: int = 0
    confidenceThreshold: float = 0.80
    riskTolerance: str = "low"


@dataclass
class AgentFeedback:
    agent: str  # 'hermes' | 'arcane' | 'arise'
    signal: str  # 'fitness' | 'cost' | 'latency' | 'success' | 'error'
    value: float
    timestamp: float


class TriAgenticKernel:
    """
    Unified Tri-Agentic Kernel across A1/A2/A3.
    Single codebase — personality differences driven by config.
    Ported from: tri_agentic_kernel.ts (21KB)
    """
    
    def __init__(self, config: dict = None):
        config = config or {}
        self.personality = PERSONALITIES.get(config.get("personality", "a1"))
        
        safety_policy = {
            **DEFAULT_SAFETY_POLICY,
            "confidenceThreshold": self.personality.confidenceThreshold,
            **(config.get("safetyPolicy", {}) or {})
        }
        self.safety_gate = SafetyGate(safety_policy)
        self.router = CostAwareRouter()
        self.metrics = EvolutionMetrics(
            confidenceThreshold=self.personality.confidenceThreshold,
            riskTolerance=self.personality.riskTolerance
        )
        self.feedback_buffer: List[AgentFeedback] = []
        
        # P2P Registry (simplified)
        self._p2p_nodes: Dict[str, dict] = {}
        self._p2p_state = {
            "version": 1,
            "timestamp": time.time(),
            "activeIntentsCount": 0,
            "consensusThreshold": 0.85,
            "globalMetrics": {
                "totalActionsExecuted": 0,
                "averageConfidence": 0,
                "activePeersCount": 0
            }
        }
        
        # Event bus
        self.event_bus = EventBus()
        
        self._register_as_peer()
    
    def _register_as_peer(self):
        """Register self in P2P mesh."""
        role = self.personality.triadRole
        peer = {
            "id": f"omnicore-{role}",
            "name": self.personality.name,
            "role": role,
            "reputationScore": 0.9,
            "status": "active",
            "lastSeen": time.time(),
            "endpoint": f"localhost:300{1 if role == 'guard' else 2 if role == 'executor' else 3 if role == 'architect' else 4}"
        }
        self._p2p_nodes[peer["id"]] = peer
    
    def check_signal_quality(self, intent: dict) -> dict:
        """A1 Gatekeeper: biometric signal quality dead-man switch."""
        features = intent.get("features", {})
        quality = features.get("quality")
        alpha_power = features.get("alpha_power")
        
        if isinstance(quality, (int, float)) and quality < 0.3:
            return {"pass": False, "reason": "degraded_signal_quality"}
        if isinstance(alpha_power, (int, float)) and alpha_power < 0.5:
            return {"pass": False, "reason": "insufficient_alpha_power"}
        return {"pass": True}
    
    def process_intent(self, intent: dict) -> dict:
        """Process a neuro intent through the full pipeline."""
        safety_result = self.safety_gate.evaluate(intent)
        
        # A1 Gatekeeper: Extra biometric check
        if self.personality.triadRole == "guard" and self.personality.requiresSignalQuality:
            signal_quality = self.check_signal_quality(intent)
            if not signal_quality["pass"]:
                self.event_bus.emit("SafetyBlocked", {"intent": intent, "decision": {"allowed": False, "reason": signal_quality.get("reason", "signal_quality_failed"), "requiresOperator": True, "riskLevel": "high"}})
                return {"status": "blocked", "reason": signal_quality["reason"]}
        
        if not safety_result["allowed"]:
            return {"status": "rejected", "reason": safety_result["reason"]}
        
        route_decision = self.router.route_neuro_intent(intent, intent.get("intent", ""))
        dispatch_result = dispatch_intent(intent)
        
        if dispatch_result["status"] == "dispatched":
            self._record_reward(route_decision, dispatch_result, safety_result)
        
        # A3 Architect: Generate co-evolution feedback
        if self.personality.triadRole == "architect":
            agent_map = {"ag": "arcane", "as": "arise", "jules": "arcane", "hermes": "hermes"}
            feedback = AgentFeedback(
                agent=agent_map.get(route_decision.get("provider", ""), "hermes"),
                signal="fitness",
                value=intent.get("confidence", 0) * 0.7 + route_decision.get("confidence", 0) * 0.3,
                timestamp=intent.get("timestamp", time.time())
            )
            self.feedback_buffer.append(feedback)
        
        return {
            "safety": safety_result,
            "route": route_decision,
            "dispatch": dispatch_result,
            "metrics": self.get_metrics()
        }
    
    def _record_reward(self, route: dict, dispatch: dict, safety: dict):
        reward = self._compute_reward(route, dispatch, safety)
        self.metrics.reward = reward
        self.metrics.cycle += 1
        self.metrics.avgConfidence = (self.metrics.avgConfidence * (self.metrics.cycle - 1) + route.get("confidence", 0)) / self.metrics.cycle
        self.metrics.routeEfficiency = route.get("confidence", 0)
        self.metrics.intentCount += 1
    
    def _compute_reward(self, route: dict, dispatch: dict, safety: dict) -> float:
        confidence_factor = route.get("confidence", 0)
        dispatch_factor = 1.0 if dispatch.get("status") == "dispatched" else 0.5
        safety_factor = 1.0 if safety.get("allowed", False) else 0.0
        personality_weight = 1.2 if self.personality.riskTolerance == "high" else 1.0
        return confidence_factor * dispatch_factor * safety_factor * personality_weight
    
    def get_identity(self) -> dict:
        """Identify which OMNICORE instance this is."""
        instance_map = {"guard": "OMNICORE-A1", "executor": "OMNICORE-A2", "architect": "OMNICORE-A3"}
        watermark_map = {"guard": "A1", "executor": "A2", "architect": "A3"}
        role = self.personality.triadRole
        return {
            "instance": instance_map.get(role, "UNKNOWN"),
            "name": self.personality.name,
            "role": role,
            "watermark": watermark_map.get(role, "U")
        }
    
    def generate_suggestion(self, content: str) -> str:
        """Generate a watermarked suggestion."""
        id = self.get_identity()
        return f"{content}\n\n-- \n[watermark: by {id['watermark']} | {id['name']} | {datetime.utcnow().isoformat()}]"
    
    def evolution_score(self) -> float:
        reward_factor = self.metrics.reward
        efficiency_factor = self.metrics.routeEfficiency
        confidence_factor = self.metrics.avgConfidence
        creativity_weight = 1.2 if self.personality.triadRole == "architect" else 1.0
        return (reward_factor * 0.4 + efficiency_factor * 0.3 + confidence_factor * 0.3) * creativity_weight
    
    def get_metrics(self) -> dict:
        return asdict(self.metrics)
    
    def get_personality(self) -> dict:
        return asdict(self.personality)
    
    # Feed-forward: A1 → A2 → A3 chain
    def feed_forward(self, target: str = "a2") -> str:
        return f"omnicore-{self.personality.triadRole}"


# ─── Global instances ───
default_router = CostAwareRouter()
default_event_bus = EventBus()
