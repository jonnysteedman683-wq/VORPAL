---
name: hermes-pyramid-evolve
description: Pyramid tier walking, degradation routing, and self-healing orchestration.
category: mlops

## Hermes Pyramid Evolve — Skill Lifecycle & Degradation Routing

### Trigger
When analyzing skill health, routing degraded skills through repair queues,
or walking the evolutionary pyramid for co-evolution cycles.

### Pyramid Tiers

```
Tier.APEX     → apex/level_0      (production, highest quality)
Tier.ACTIVE   → active/level_1   (in-use, monitored)
Tier.STAGNANT → stagnant/level_2 (stable, low churn)
Tier.ARCHIVED → archived/level_3 (frozen, read-only)
Tier.REPAIR   → repair/level_4_base (actively degrading)
```

### Repair Columns

| Priority | Categories |
|----------|------------|
| PRIORITY_1_CRITICAL | critical_multi_category |
| PRIORITY_2_SINGLE | syntax_crash, logic_hallucination, token_bloat, overlap_redundant |
| PRIORITY_3 | inactivity_decay |

### Degradation Detection

```python
def detect_degradation(self, file_path: Path) -> List[DegradationCategory]:
    content = file_path.read_text(encoding='utf-8')
    match = re.search(r'linked_degradations:\s*\[(.*?)\]', content, re.DOTALL)
    if match:
        degradations = re.findall(r'"([^"]+)"', match.group(1))
        return [DegradationCategory(d) for d in degradations
                if d in [e.value for e in DegradationCategory]]
    return []
```

### Migration Routing

```python
def identify_migration_target(self, file_path: Path) -> Optional[str]:
    degradations = self.detect_degradation(file_path)
    if not degradations:
        return Tier.ACTIVE.value
    if DegradationCategory.CRITICAL_MULTI in degradations:
        return "repair/PRIORITY_1_CRITICAL/critical_multi_category"
    elif DegradationCategory.SYNTAX_CRASH in degradations:
        return "repair/PRIORITY_2_SINGLE/syntax_crash"
    elif DegradationCategory.LOGIC_HALLUCINATION in degradations:
        return "repair/PRIORITY_2_SINGLE/logic_hallucination"
    # ... etc
    return Tier.STAGNANT.value
```

### Health Watchdog

```python
class HealthWatchdog:
    def __init__(self, subsystems: List[str], interval: float = 10.0):
        self._breakers = {
            name: CircuitBreaker(failure_threshold=3, timeout=30)
            for name in subsystems
        }
        self._health_records = {
            name: deque(maxlen=100) for name in subsystems
        }

    async def monitor(self, subsystem, heartbeat_fn, validate_fn):
        while True:
            # Circuit breaker wraps heartbeat
            await self._breakers[subsystem].call(
                heartbeat_fn(),
                fallback=lambda: False
            )
            health_ok = await validate_fn()
            self._record_health(subsystem, health_ok, ...)
            await asyncio.sleep(self._interval)
```

### Self-Healing Orchestrator

```python
class SelfHealingOrchestrator:
    async def execute_with_healing(self, subsystem, operation):
        breaker = self._system_breakers.get(subsystem)
        debugger = self._debuggers.get(subsystem)
        if breaker:
            try:
                return await breaker.call(operation())
            except CircuitOpenError:
                return await self._fallback_execution(subsystem, ...)
            except Exception as e:
                report = debugger.diagnose(str(e))
                for err in report:
                    fixed_code, success = await debugger.auto_correct(err, "")
                    if success:
                        self._recovery_actions.append({...})
                raise
```

### Pattern Proved
The two-layer lock (thread mutex + OS advisory) is essential when multiple
cron processes touch the same bus. Without it, `consume()` has a TOCTOU
window between `_locate()` and `read_text()` that causes `FileNotFoundError`
under concurrency instead of clean exit code 2.
