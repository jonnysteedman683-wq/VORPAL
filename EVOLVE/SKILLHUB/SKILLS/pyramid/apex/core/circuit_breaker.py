"""
OMNICORE CIRCUIT BREAKER SKILL
Asynchronous circuit breaker preventing repeated calls to failing subsystems.
Pattern sourced from AEGIS tri-brain stack + PRIME-DIRECTIVE resilience mandates.
"""
import asyncio
from enum import Enum
from time import time
from typing import Any, Callable, Optional
import heapq


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Asynchronous circuit breaker with configurable failure threshold and timeout.
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=3, timeout=30)
        result = await breaker.call(http_get(url))
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self._failure_threshold = failure_threshold
        self._timeout = timeout
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time = 0.0
        self._metrics: list = []  # Min-heap for tracking failure timestamps

    @property
    def state(self) -> CircuitState:
        return self._state
    
    @property
    def failure_count(self) -> int:
        return self._failure_count

    async def call(self, coro, fallback: Optional[Callable] = None):
        """Execute coroutine with circuit breaker protection."""
        if self._state == CircuitState.OPEN:
            if time() - self._last_failure_time > self._timeout:
                self._state = CircuitState.HALF_OPEN
            else:
                if fallback:
                    fallback_result = fallback()
                    coro.close()  # Prevent "coroutine never awaited" warning
                    if asyncio.iscoroutine(fallback_result):
                        return await fallback_result
                    return fallback_result
                else:
                    coro.close()  # Prevent "coroutine never awaited" warning
                    raise CircuitOpenError("Circuit breaker is open")
        
        try:
            result = await coro
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            if self._state == CircuitState.OPEN and fallback:
                fallback_result = fallback()
                if asyncio.iscoroutine(fallback_result):
                    return await fallback_result
                return fallback_result
            raise

    def _on_success(self):
        """Reset failure count on successful execution."""
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def _on_failure(self, error: Exception):
        """Record failure and trip circuit if threshold exceeded."""
        self._failure_count += 1
        now = time()
        heapq.heappush(self._metrics, -now)  # Max-heap simulation with negation
        self._last_failure_time = now
        
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN

    def get_metrics(self) -> dict:
        """Return circuit breaker metrics."""
        now = time()
        cutoff = now - self._timeout
        recent_failures = sum(1 for ts in self._metrics if -ts > cutoff)
        return {
            'state': self._state.value,
            'failure_count': self._failure_count,
            'recent_failures': recent_failures,
            'last_failure_time': self._last_failure_time,
            'failure_threshold': self._failure_threshold,
            'timeout': self._timeout,
        }


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and request is blocked."""
    pass

# Async-safe singleton for global use
DEFAULT_BREAKER = CircuitBreaker(failure_threshold=3, timeout=60)