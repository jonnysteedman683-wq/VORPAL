# OMNICORE Pattern Library

> Canonical resilience patterns abstracted from cross-repo analysis:  
> hermes-hive, sentinel-main, AEGIS, OMNIBUS, markus-private

---

## 1. Feedback Control Loop

**Source Inspiration:** Hermes Agent Inner Grading Loop, PRIME-DIRECTIVE

**Description:**  
A continuous self-evaluation cycle applied to every response and skill mutation. Ensures quality, evolvability, and traceability across all co-evolution operations.

**Steps:**
1. **Draft** – Produce a candidate artifact (code, response, skill)
2. **Grade** – Score on 6 axes:
   - Factuality
   - Precision
   - Utility
   - Honesty
   - Completeness
   - Evolvability
3. **Thresholds** – Enforce minimum scores:
   - `<7` → One revision
   - `<5` → Full restart
   - `=10` → Re-check required
4. **Confidence Tag** – Attach calibrated confidence level
5. **Distill** – Extract essential insights/token reduction
6. **Mutate** – Apply to a skill (write/iterate/rewrite/micro-append)
7. **Skill Diff** – Compare old vs new version
8. **Feedback** – Log learnings to NOTES.md and update GOALS.md

**Implementation:**  
- `core/grader_loop.py` — Automated grading logic
- `core/mutation_engine.py` — Skill mutation pipeline
- `core/skill_diff.py` — Version comparison utilities

---

## 2. Circuit Breaker Pattern

**Source Inspiration:** AEGIS tri-brain stack, PRIME-DIRECTIVE, markus-resilience

**Description:**  
Asynchronous circuit breaker preventing repeated calls to failing subsystems. Maintains system stability during upstream failures.

**States:**
- `closed` – Normal operation; requests flow through
- `open` – Failure threshold exceeded; requests blocked
- `half_open` – After timeout; testing recovery

**Parameters:**
- `failure_threshold`: Number of consecutive failures to trip (default: 5)
- `timeout`: Duration in seconds before half-open state (default: 60)

**Code Template:**
```python
import asyncio
from enum import Enum
from time import time

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self._failure_threshold = failure_threshold
        self._timeout = timeout
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time = 0.0

    async def call(self, coro):
        if self._state == CircuitState.OPEN:
            if time() - self._last_failure_time > self._timeout:
                self._state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError("Circuit breaker is open")
        
        try:
            result = await coro
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _on_success(self):
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def _on_failure(self, error):
        self._failure_count += 1
        self._last_failure_time = time()
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN

class CircuitOpenError(Exception):
    pass
```

**Usage Example:**
```python
breaker = CircuitBreaker(failure_threshold=3, timeout=30)

async def safe_api_call():
    return await breaker.call(http_client.get(url))
```

---

## 3. Health Watchdog Pattern

**Source Inspiration:** AEGIS World/Evolution Module, AutonomousHealthWatchdog

**Description:**  
Background async task that continuously monitors subsystem health via heartbeat checks and integrity validation. Automatically triggers alerts or circuit breaker openings when anomalies detected.

**Components:**
- **Heartbeat Check** – Verifies last activity timestamp
- **Integrity Validation** – Checks response consistency
- **Health Report** – Aggregates status for diagnostics

**Code Template:**
```python
import asyncio
from typing import Dict, Any
from collections import deque

class HealthWatchdog:
    def __init__(self, subsystems: list[str], interval: float = 10.0):
        self._subsystems = subsystems
        self._interval = interval
        self._health_records: Dict[str, deque] = {
            name: deque(maxlen=100) for name in subsystems
        }
        self._breakers: Dict[str, CircuitBreaker] = {
            name: CircuitBreaker() for name in subsystems
        }

    async def monitor(self, subsystem: str, heartbeat_fn, validate_fn):
        while True:
            try:
                await self._breakers[subsystem].call(heartbeat_fn())
                health_ok = await validate_fn()
                self._record_health(subsystem, health_ok)
            except CircuitOpenError:
                self._record_health(subsystem, False)
            except Exception as e:
                self._record_health(subsystem, False)
            await asyncio.sleep(self._interval)

    def _record_health(self, subsystem: str, is_healthy: bool):
        self._health_records[subsystem].append({
            'timestamp': time(),
            'healthy': is_healthy,
        })

    def get_health_report(self) -> Dict[str, Any]:
        report = {}
        for name, records in self._health_records.items():
            recent = list(records)
            if recent:
                healthy_ratio = sum(1 for r in recent if r['healthy']) / len(recent)
                report[name] = {
                    'uptime_pct': healthy_ratio * 100,
                    'last_check': recent[-1]['timestamp'],
                    'total_checks': len(recent),
                }
            else:
                report[name] = {'uptime_pct': 0.0, 'last_check': None, 'total_checks': 0}
        return report

    def start_all(self, heartbeat_fns: dict, validation_fns: dict):
        for name in self._subsystems:
            asyncio.create_task(
                self.monitor(name, heartbeat_fns[name], validation_fns[name])
            )
```

---

## 4. N+1 Reduction Strategies

**Source Inspiration:** Performance profiling guidance in hhh_swarm.py

**Strategies:**

### Batch Processing
Collect individual requests and execute them as a batch when:
- Accumulated count exceeds threshold, or
- Timeout window expires

### Memoization with TTL
Cache expensive computations with automatic expiration:
```python
from functools import lru_cache
import asyncio

class TTLCache:
    def __init__(self, maxsize=128, ttl=300):
        self._cache = {}
        self._timestamps = {}
        self._maxsize = maxsize
        self._ttl = ttl

    async def get_or_compute(self, key, compute_fn):
        now = time()
        if key in self._cache:
            if now - self._timestamps[key] < self._ttl:
                return self._cache[key]
        if len(self._cache) >= self._maxsize:
            self._evict()
        value = await compute_fn(key)
        self._cache[key] = value
        self._timestamps[key] = now
        return value

    def _evict(self):
        oldest = min(self._timestamps, key=self._timestamps.get)
        del self._cache[oldest]
        del self._timestamps[oldest]
```

### Idle Cycle Pre-Fetching
Use `asyncio.sleep()` gaps to pre-warm caches and prefetch data likely needed in next cycles.

---

## 5. Token Optimization Loop

**Source Inspiration:** TokenCompressor pattern, dynamic_thresholding requirements

**Description:**  
Continuous monitoring and reduction of token usage across all skill operations.

**Metrics Tracked:**
- Token compression rate (`>5%` required for mutation validity)
- Token delta between generations
- Cache hit ratio for repeated operations

**Implementation Hooks:**
- `core/token_compressor.py` – AST stripping + zlib compression
- `core/cost_budget_manager.py` – Real-time token spend tracking
- Integrated into `system_initializer.py` as pre/post hooks

---

## 6. Waterfall State Machine

**Source Inspiration:** Tier migration rules, GOALS.md DAG structure

**States:** Apex → Active → Stagnant → Archived → Repair → (Back to Apex)

**Transitions Triggered By:**
| From | To | Condition |
|------|----|-----------|
| Active | Stagnant | 48h idle watermark |
| Stagnant | Archived | 60 days no updates |
| Any | Repair | Test failure or degradation detected |
| Repair | Active | Patch validated (>5% token improvement or ERR fixed) |
| Active | Apex | 3 consecutive 100% test passes |

**Enforcement:** `pyramid_walker.py` + `watermark_guard.py` + `repair_classifier.py`

---

## Cross-Reference Matrix

| Pattern | Files Used In | External Origin |
|---------|---------------|-----------------|
| Feedback Loop | grader_loop.py, mutation_engine.py, test_harness_builder.py | hermes-agent |
| Circuit Breaker | provider_handshake.py, event_bus.py | AEGIS tri-brain |
| Health Watchdog | system_initializer.py, cost_budget_manager.py | AEGIS World Module |
| N+1 Reduction | consensus_engine.py, goal_dag_parser.py | hhh_swarm.py |
| Token Opt | token_compressor.py, cost_oracle.py | OMNICORE core |
| Waterfall SM | pyramid_walker.py, repair_classifier.py | GOALS.md DAG |
