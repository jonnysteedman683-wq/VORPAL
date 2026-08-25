---
procedure_id: "harvested_patterns_database"
type: "protocol"
related_skills: ["safety_gate", "cost_router", "event_bus", "dispatcher", "circuit_breaker", "health_watchdog", "adaptive_model_selector", "idea_engine", "loop_creator"]
last_executed: "2026-08-19T12:00:00Z"
---

# OMNICORE Harvested Patterns Database

> Canonical architectural patterns stolen from existing OMNICORE/OMNIBUS databases.
> All patterns verified against SafetyGate and integrated into tier_0_apex pyramid.

---

## 1. Safety Gate Pattern (Multi-Layered Policy Enforcement)
**Stolen from:** `OMNICORE-A1/src/lib/safety_gate.ts` — `github.com/jonnysteedman683-wq/neurocore + OMNIBUS`

```python
# STOLE FROM: OMNICORE-A1/src/lib/safety_gate.ts
class SafetyGate:
    DEFAULT_POLICY = {
        'allowed_intents': ['route', 'execute', 'query', 'observe', 'infra', 'upgrade', 'lint', 'code', 'review', 'test'],
        'blocked_intents': ['override_system', 'destructive_action', 'unauthorized_command'],
        'confidence_threshold': 0.75,
        'max_cost_usd': 5.0,
        'allowed_features': ['alpha_power', 'beta_alpha_ratio', 'asymmetry', 'quality'],
        'min_quality_threshold': 0.3,
        'max_rate_per_min': 60
    }

    def evaluate(self, intent):
        # Rule chain: signal_quality → alpha_power → confidence → blocked → allowed → features → rate → cost
        ...
```

**Applied to:** `safety_gate.py` v1.1 — Added biometric signal quality dead-man switch

---

## 2. Cost-Aware Router Pattern (Semantic Classification)
**Stolen from:** `OMNICORE-A1/src/lib/cost_router.ts` — `Cogitator-AI + MARKUS-OS markus_router.py`

```python
# STOLE FROM: OMNICORE-A1/src/lib/cost_router.ts
class CostAwareRouter:
    MODEL_CONSTELLATION = {
        'CODE_SPECIALIST': 'openrouter/poolside/laguna-s-2.1:free',
        'MEGACONTEXT_ARCH': 'openrouter/nvidia/nemotron-3-ultra:free',
        'FAST_TELEMETRY': 'openrouter/inclusionai/ling-3.0-flash:free',
        'OFFLINE_LOCAL': 'custom/qwen2.5-coder:7b'
    }

    def route_intent(self, prompt, context_tokens=0, is_offline=False):
        estimated_tokens = len(prompt.split()) * 2 + context_tokens
        # >15k tokens OR architecture keywords → megacontext
        # code keywords → coding specialist
        # status/heartbeat → fast telemetry
        ...
```

**Applied to:** `adaptive_model_selector.py` — Enhanced with token-based semantic routing

---

## 3. Event Bus Pattern (Typed System-Wide Dispatch)
**Stolen from:** `OMNICORE-A1/src/lib/event_bus.ts` — `neurocore core/event_bus.ts`

```python
# STOLE FROM: OMNICORE-A1/src/lib/event_bus.ts
class EventBus:
    def __init__(self):
        self._listeners = {}

    def on(self, event, handler):
        """Register handler, return unsubscribe function."""
        if event not in self._listeners:
            self._listeners[event] = set()
        self._listeners[event].add(handler)
        return lambda: self._listeners[event].discard(handler)

    def emit(self, event, data):
        """Dispatch to all listeners with error isolation per-handler."""
        for handler in list(self._listeners.get(event, [])):
            try:
                handler(data)
            except Exception as e:
                logging.error(f"EventBus handler error: {e}")

    def once(self, event, handler):
        """Register one-time handler."""
        def wrapper(data):
            self._listeners[event].discard(wrapper)
            handler(data)
        self.on(event, wrapper)
```

**Applied to:** `state_memory_manager.py` — Added typed event emission layer

---

## 4. Dispatcher Pattern (Intent Classification + Stream Routing)
**Stolen from:** `OMNICORE-A1/src/lib/dispatcher.ts` — `neurocore core/dispatcher.ts`

```python
# STOLE FROM: OMNICORE-A1/src/lib/dispatcher.ts
ROUTING_TABLE = {
    'infra': 'antigravity',    # Infrastructure tasks
    'upgrade': 'antigravity',  # Dependency management
    'lint': 'antigravity',     # Code hygiene
    'neural': 'ai_studio',     # Neural decoding
    'signal': 'ai_studio',     # Signal processing
    'decode': 'ai_studio',     # Intent decoding
    'code': 'jules',           # Code generation
    'review': 'jules',         # PR review
    'test': 'jules'            # Testing/validation
}

DEFAULT_STREAM = 'hermes'

def dispatch_intent(intent):
    # 1. SafetyGate check
    # 2. Route table lookup
    # 3. High-risk → queued, low-risk → dispatched
    ...
```

**Applied to:** `adaptive_model_selector.py` — Enhanced with intent routing table

---

## 5. Circuit Breaker Pattern (Failure Isolation)
**Stolen from:** `AEGIS circuit breaker` + `OMNICORE-A1 resilience`

```python
# STOLE FROM: AEGIS circuit breaker pattern
class CircuitBreaker:
    def __init__(self, failure_threshold=3, timeout=60):
        self._failure_threshold = failure_threshold
        self._timeout = timeout  # seconds before half-open
        self._failure_count = 0
        self._last_failure_time = 0
        self._state = 'closed'  # closed | open | half_open
```

**Applied to:** `circuit_breaker.py` — Full async implementation with circuit state management

---

## 6. Health Watchdog Pattern (Continuous Monitoring)
**Stolen from:** `MARKUS-OS health_monitor.ts` + `AEGIS World Module`

```python
# STOLE FROM: MARKUS-OS health_monitor.ts + AEGIS World Module
class HealthWatchdog:
    def __init__(self, subsystems, interval=5.0):
        self._subsystems = subsystems
        self._interval = interval
        self._health_records = {s: deque(maxlen=96) for s in subsystems}  # 8h @ 5s
        self._breakers = {s: CircuitBreaker() for s in subsystems}

    async def check_heartbeat(self, subsystem):
        """Check subsystem liveness and update health records."""
        ...

    async def monitor(self):
        """Background monitoring loop with sleep intervals."""
        ...
```

**Applied to:** `health_watchdog.py` — Async background monitoring with P2P state sync

---

## 7. P2P State Registry Pattern (Decentralized Consensus)
**Stolen from:** `OMNICORE-A1/src/lib/p2p_state_registry.ts`

Features:
- Per-agent state sync via weighted consensus
- Peer registration with reputation scoring
- Last-seen staleness tracking (auto-prune stale peers)
- State delta broadcasting across mesh

**Applied to:** `persistent_state_store.py` v2.0 — Planning decentralized state sync

---

## 8. Upgrade Registry Pattern (Structured Task Manifests)
**Stolen from:** `OMNICORE-A1/src/lib/upgrade_registry.ts` — `OMNIBUS upgrade-manifest.ts`

```python
# STOLE FROM: OMNICORE-A1/src/lib/upgrade_registry.ts
class SwarmUpgradeRegistry:
    def __init__(self):
        self._tasks = {}
        self._health_checks = {}
        self._register_default_health_checks()
        self._register_default_upgrade_tasks()

    def run_health_checks(self):
        """Returns SystemHealthReport with component statuses and pending upgrades."""
        ...

    def execute_task(self, task_id, context=None):
        """Execute upgrade task with rollback plan, emits lifecycle events."""
        ...
```

**Applied to:** `loop_creator.py` — Task manifest structure with rollback + health checks

---

## 9. Tri-Agentic Personality Pattern (Config-Driven)
**Stolen from:** `OMNICORE-A1/src/lib/tri_agentic_kernel.ts`

```python
# STOLE FROM: OMNICORE-A1/src/lib/tri_agentic_kernel.ts
PERSONALITIES = {
    'a1': {'name': 'The Gatekeeper', 'role': 'guard',     'threshold': 0.80, 'risk': 'low'},
    'a2': {'name': 'The Optimizer',  'role': 'executor',  'threshold': 0.70, 'risk': 'medium'},
    'a3': {'name': 'The Architect',  'role': 'architect', 'threshold': 0.65, 'risk': 'high'},
}

# Single codebase, personality via config.json
# Watermark rules: "by [A1|A2|A3]"
# 2-of-own rule: suggestions must be validated by another agent
```

**Applied to:** `idea_engine.py` — Dual-dice decision making with personality traits

---

## 10. Auto-Healing Feedback Loop
**Stolen from:** `ARISE brain` + `missionEngine.ts recoverTaskFailure` pattern

```python
# STOLE FROM: ARISE brain + missionEngine.ts recoverTaskFailure
# 1. Task fails → Log failure with error taxonomy
# 2. Classify: syntax/logic/runtime/degradation
# 3. Apply known fix pattern (or quarantine as new idea)
# 4. Retry with exponential backoff (max 3)
# 5. If max retries → route to skill_repair/PRIORITY_1_Critical
```

**Applied to:** `auto_debugger.py` + `self_healing_orchestrator.py` — Full error diagnosis + recovery pipeline

---

## Integration Mapping Summary

| Original Source | Stolen Into | Enhancement Applied |
|---|---|---|
| `safety_gate.ts` | `safety_gate.py` | Biometric signal quality + rate limiting |
| `cost_router.ts` | `adaptive_model_selector.py` | Semantic routing thresholds + model constellation |
| `event_bus.ts` | `state_memory_manager.py` | Typed event emission with error isolation |
| `dispatcher.ts` | `adaptive_model_selector.py` | Intent allowlist + stream routing table |
| `upgrade_registry.ts` | `loop_creator.py` | Task manifest + rollback plans + health checks |
| `tri_agentic_kernel.ts` | `idea_engine.py` | Personality traits + watermark rules + argmax/secondBest |
| `a4_synthesizer.ts` | `idea_engine.py` | Chaos factor + trait-vector recombination |
| AEGIS circuit breaker | `circuit_breaker.py` | Full async circuit state management |
| MARKUS-OS health_monitor | `health_watchdog.py` | Continuous monitoring + P2P state sync |
| ARISE + missionEngine | `auto_debugger.py` | Error categorization + recovery retry loop |

---

## Upgrade Priority Queue

| Priority | Target | Enhancement | Status |
|---|---|---|---|
| HIGH | `safety_gate.py` | Add rate limiting via deque buffer | 🟡 Ready |
| HIGH | `cost_router.py` → `adaptive_model_selector.py` | Add semantic classification rules | 🟡 Ready |
| MEDIUM | `event_bus.ts` → `state_memory_manager.py` | Add typed event emission | 🟡 Ready |
| MEDIUM | `p2p_state_registry.ts` → `persistent_state_store.py` | Add decentralized sync layer | 🟠 Planned |
| LOW | `dispatcher.ts` → future `intent_dispatcher.py` | Stream routing table | 🟠 Planned |

<!-- HARVESTED_PATTERNS_DB v1.0 -->
