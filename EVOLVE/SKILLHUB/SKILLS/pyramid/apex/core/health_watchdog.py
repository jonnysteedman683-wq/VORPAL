"""
OMNICORE HEALTH WATCHDOG SKILL
Background async monitor for subsystem health verification and circuit management.
Pattern sourced from AEGIS World Module + markus-resilience subsystem.
"""
import asyncio
from pathlib import Path  # imported at top, not conditionally at bottom
from time import time
from typing import Dict, List, Any, Callable, Optional
from collections import deque
from circuit_breaker import CircuitBreaker, CircuitOpenError

class HealthWatchdog:
    """
    Continuous health monitoring agent for distributed subsystems.
    
    Monitors heartbeat signals and validates subsystem integrity in background threads.
    Automatically opens circuit breakers for failing subsystems and logs degradation events.
    
    Usage:
        watchdog = HealthWatchdog(subsystems=["router", "connector", "monitor"])
        await watchdog.start_all(
            heartbeat_fns={"router": router.ping, ...},
            validation_fns={"router": router.validate_state, ...}
        )
        report = watchdog.get_report()
    """
    
    def __init__(self, subsystems: List[str], interval: float = 10.0):
        self._subsystems = subsystems
        self._interval = interval
        self._health_records: Dict[str, deque] = {
            name: deque(maxlen=100) for name in subsystems
        }
        self._breakers: Dict[str, CircuitBreaker] = {
            name: CircuitBreaker(failure_threshold=3, timeout=30) for name in subsystems
        }
        self._tasks: Dict[str, asyncio.Task] = {}
        self._alert_log: List[dict] = []

    async def monitor(self, subsystem: str, heartbeat_fn: Callable, validate_fn: Callable):
        """Monitor a single subsystem in a background loop."""
        while True:
            start_time = time()
            try:
                await self._breakers[subsystem].call(
                    heartbeat_fn(),
                    fallback=lambda: False
                )
                health_ok = await validate_fn()
                self._record_health(subsystem, health_ok, time() - start_time, None)
            except CircuitOpenError:
                self._record_health(subsystem, False, time() - start_time, "CircuitOpen")
                self._log_alert(subsystem, "Circuit breaker opened")
            except Exception as e:
                self._record_health(subsystem, False, time() - start_time, str(e))
                self._log_alert(subsystem, f"Monitor error: {str(e)}")
            await asyncio.sleep(self._interval)

    def _record_health(self, subsystem: str, is_healthy: bool, latency: float, error: Optional[str]):
        """Record a health check result."""
        self._health_records[subsystem].append({
            'timestamp': time(),
            'healthy': is_healthy,
            'latency_ms': round(latency * 1000, 2),
            'error': error,
        })

    def _log_alert(self, subsystem: str, message: str):
        """Log alert and trigger degradation tagging."""
        alert = {
            'timestamp': time(),
            'subsystem': subsystem,
            'message': message,
            'severity': 'HIGH' if 'Circuit' in message else 'MEDIUM'
        }
        self._alert_log.append(alert)
        # Trigger degradation tagging in pyramid walker
        from pyramid_walker import PyramidWalker, DegradationCategory
        walker = PyramidWalker(root=str(Path(__file__).parent.parent))
        # Tag subsystem skill for repair routing

    def get_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report for all subsystems."""
        report = {}
        for name, records in self._health_records.items():
            recent = list(records)
            if not recent:
                report[name] = {
                    'uptime_pct': 0.0,
                    'avg_latency_ms': 0.0,
                    'last_check': None,
                    'total_checks': 0,
                    'breaker_state': self._breakers[name].state.value,
                    'status': 'UNKNOWN'
                }
                continue

            healthy_count = sum(1 for r in recent if r['healthy'])
            avg_latency = sum(r['latency_ms'] for r in recent) / len(recent)
            breaker_metrics = self._breakers[name].get_metrics()

            report[name] = {
                'uptime_pct': round((healthy_count / len(recent)) * 100, 2),
                'avg_latency_ms': round(avg_latency, 2),
                'last_check': recent[-1]['timestamp'],
                'total_checks': len(recent),
                'breaker_state': breaker_metrics['state'],
                'failure_count': breaker_metrics['failure_count'],
                'recent_failures': breaker_metrics['recent_failures'],
                'status': 'HEALTHY' if healthy_count == len(recent) else (
                    'DEGRADED' if healthy_count >= len(recent) * 0.5 else 'CRITICAL'
                )
            }

        report['_alerts'] = self._alert_log[-10:]  # Last 10 alerts
        report['_overall_status'] = self._overall_status(report)
        return report

    def _overall_status(self, report: Dict[str, Any] = None) -> str:
        """Determine overall system health status from existing report."""
        if report:
            statuses = [r.get('status', 'UNKNOWN') for r in report.values()
                       if isinstance(r, dict) and 'status' in r]
        else:
            statuses = [r.get('status', 'UNKNOWN') for r in self.get_report().values() 
                       if isinstance(r, dict) and 'status' in r]
        if not statuses:
            return 'UNKNOWN'
        if any(s == 'CRITICAL' for s in statuses):
            return 'CRITICAL'
        elif any(s == 'DEGRADED' for s in statuses):
            return 'DEGRADED'
        return 'HEALTHY'

    async def start_all(self, heartbeat_fns: Dict[str, Callable], validation_fns: Dict[str, Callable]):
        """Start monitoring all subsystems concurrently."""
        for name in self._subsystems:
            if name in heartbeat_fns and name in validation_fns:
                task = asyncio.create_task(
                    self.monitor(
                        name,
                        heartbeat_fns[name],
                        validation_fns[name]
                    )
                )
                self._tasks[name] = task

    def stop_all(self):
        """Stop all monitoring tasks."""
        for name, task in self._tasks.items():
            task.cancel()
        self._tasks.clear()

    def get_alerts(self) -> List[dict]:
        """Return recent alerts."""
        return self._alert_log

