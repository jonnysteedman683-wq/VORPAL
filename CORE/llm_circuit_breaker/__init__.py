"""
[◈VORPAL◈] Core: llm_circuit_breaker

Adapted from MukundaKatta/llm-circuit-breaker-py (MIT license).
- breaker.py: thread-safe + async Closed/Open/HalfOpen state machine
- predicates.py: provider-specific should_count detectors

Used to harden markus_router.py provider routing with provider-aware error
counting so caller bugs (4xx) don't poison the breaker for everyone else.
"""

from .breaker import (
    AsyncCircuitBreaker,
    BreakerConfig,
    BreakerState,
    BreakerStats,
    CircuitBreaker,
    CircuitOpenError,
    guard,
)
from .predicates import (
    ANTHROPIC_SERVICE_FAILURES,
    BEDROCK_SERVICE_FAILURES,
    GEMINI_SERVICE_FAILURES,
    HTTP_SERVICE_STATUSES,
    OPENAI_SERVICE_FAILURES,
    any_of,
    anthropic,
    bedrock,
    contains_any,
    gemini,
    is_http_status_service_failure,
    openai,
)

__version__ = "0.2.0"

__all__ = [
    "AsyncCircuitBreaker",
    "BreakerConfig",
    "BreakerState",
    "BreakerStats",
    "CircuitBreaker",
    "CircuitOpenError",
    "anthropic",
    "bedrock",
    "contains_any",
    "gemini",
    "guard",
    "is_http_status_service_failure",
    "openai",
    "any_of",
    "__version__",
]