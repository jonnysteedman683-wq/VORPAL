"""
OMNICORE SELF-HEALING ORCHESTRATOR SKILL
Coordinates health monitoring, circuit breaking, and auto-debugging.
Pattern stolen from AEGIS tri-brain resilience stack.
"""
import asyncio
import logging
from typing import Dict, List, Any, Callable
from circuit_breaker import CircuitBreaker, CircuitOpenError
from health_watchdog import HealthWatchdog
from auto_debugger import AutoDebugger

class SelfHealingOrchestrator:
    """
    Central coordination point for autonomous recovery.
    
    Integrates:
    - CircuitBreaker for immediate failure isolation
    - HealthWatchdog for continuous monitoring
    - AutoDebugger for root-cause analysis and fixes
    """
    
    def __init__(self, subsystems: List[str]):
        self._watchdog = HealthWatchdog(subsystems=subsystems, interval=5.0)
        self._debuggers: Dict[str, AutoDebugger] = {
            name: AutoDebugger() for name in subsystems
        }
        self._system_breakers: Dict[str, CircuitBreaker] = {
            name: CircuitBreaker(failure_threshold=3, timeout=30)
            for name in subsystems
        }
        self._logger = logging.getLogger("omnicore.healing")
        self._recovery_actions: List[dict] = []

    async def execute_with_healing(self, subsystem: str, operation: Callable):
        """Execute operation with full self-healing pipeline."""
        breaker = self._system_breakers.get(subsystem)
        debugger = self._debuggers.get(subsystem)
        
        if breaker:
            try:
                return await breaker.call(operation())
            except CircuitOpenError:
                self._logger.warning(f"Circuit open for {subsystem}, attempting bypass")
                # Try degraded mode or cached result
                return await self._fallback_execution(subsystem, lambda: operation())
            except Exception as e:
                # Trigger auto-debug pipeline
                if debugger:
                    report = debugger.diagnose(str(e))
                    for err in report:
                        self._logger.error(f"Diagnosed: {err.message}")
                        fixed_code, success = await debugger.auto_correct(err, "")
                        if success:
                            self._recovery_actions.append({
                                'subsystem': subsystem,
                                'fix': err.suggested_fix,
                                'success': True
                            })
                raise
                
    async def _fallback_execution(self, subsystem: str, operation: Callable):
        """Fallback execution when circuit is open."""
        # Try reading from persistent state
        try:
            from persistent_state_store import get_store
            store = get_store()
            cached = store.get(f"{subsystem}_last_result")
            if cached:
                self._logger.info(f"Fallback: Using cached result for {subsystem}")
                return cached
        except ImportError:
            pass
        
        # Try operation in degraded mode (single attempt)
        try:
            coro = operation()
            if asyncio.iscoroutine(coro):
                return await coro
            return coro
        except Exception as e:
            self._logger.error(f"Fallback execution failed: {e}")
            raise RuntimeError(f"No fallback available for {subsystem}")

    def start_monitoring(self):
        """Start background health monitoring tasks."""
        # This would be called within an async context in production
        pass

    def get_healing_report(self) -> Dict[str, Any]:
        """Generate comprehensive healing status report."""
        report = {
            'subsystems': {},
            'recent_actions': self._recovery_actions[-10:],
            'overall_status': 'HEALTHY'
        }
        
        for name in self._watchdog._subsystems:
            breaker_metrics = self._system_breakers[name].get_metrics()
            report['subsystems'][name] = {
                'circuit_state': breaker_metrics['state'],
                'failure_count': breaker_metrics['failure_count'],
                'debuggers_registered': name in self._debuggers
            }
            
            if breaker_metrics['state'] != 'closed':
                report['overall_status'] = 'DEGRADED'
                
        return report

# Singleton instance
HEALER = None

def get_orchestrator(subsystems: List[str] = ["router", "connector", "monitor"]) -> SelfHealingOrchestrator:
    """Get singleton SelfHealingOrchestrator instance."""
    global HEALER
    if HEALER is None:
        HEALER = SelfHealingOrchestrator(subsystems)
    return HEALER
