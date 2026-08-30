"""Built-in `should_count` predicates for major LLM providers.

[◈VORPAL◈] Adapted from MukundaKatta/llm-circuit-breaker-py (MIT).

The breaker takes a `should_count(exc) -> bool` callback that decides
whether an exception flips it. In practice, the answer is "yes for
provider-side failures (rate-limit, overloaded, 5xx) and no for
caller-side failures (auth, validation)" — so this module ships
ready-made detectors per provider.

Usage:

    from llm_circuit_breaker import CircuitBreaker, predicates

    cb = CircuitBreaker()
    cb.call(
        call_anthropic,
        should_count=predicates.anthropic,   # only count provider errors
    )

The detectors match against `str(exc)` so they work whether the SDK
raises a typed exception class or a generic one with the error code in
the message.
"""

from __future__ import annotations

from collections.abc import Iterable

# Provider-side error code substrings — what the provider says is *its*
# fault (or transient on its end), not the caller's. Caller-side failures
# (authentication, validation, billing) should NOT trip the breaker.

# Anthropic — https://docs.anthropic.com/en/api/errors
ANTHROPIC_SERVICE_FAILURES: tuple[str, ...] = (
    "rate_limit_error",
    "overloaded_error",
    "api_error",
    "timeout",
)

# OpenAI — https://platform.openai.com/docs/guides/error-codes
OPENAI_SERVICE_FAILURES: tuple[str, ...] = (
    "rate_limit_exceeded",
    "server_error",
    "engine_overloaded",
    "tokens_exhausted",
    "timeout",
)

# AWS Bedrock — https://docs.aws.amazon.com/bedrock/latest/userguide/troubleshoot.html
BEDROCK_SERVICE_FAILURES: tuple[str, ...] = (
    "ThrottlingException",
    "Throttling",
    "TooManyRequestsException",
    "ServiceUnavailableException",
    "ProvisionedThroughputExceededException",
    "ModelTimeoutException",
)

# Google Gemini — https://ai.google.dev/api/rest/v1/HttpStatusCode
GEMINI_SERVICE_FAILURES: tuple[str, ...] = (
    "RESOURCE_EXHAUSTED",
    "UNAVAILABLE",
    "DEADLINE_EXCEEDED",
    "INTERNAL",
)

# Generic HTTP status codes that are service-side failures.
HTTP_SERVICE_STATUSES: tuple[int, ...] = (408, 425, 429, 500, 502, 503, 504)


def contains_any(s: str, patterns: Iterable[str]) -> bool:
    """True if `s` contains any of `patterns` (case-sensitive substring)."""
    return any(p in s for p in patterns)


def _exc_to_str(exc: BaseException) -> str:
    """Compose the exception class name + message so a typed exception
    carrying a provider error code is still matchable."""
    return f"{type(exc).__name__}: {exc}"


def anthropic(exc: BaseException) -> bool:
    """Service-failure detector for Anthropic SDK exceptions."""
    return contains_any(_exc_to_str(exc), ANTHROPIC_SERVICE_FAILURES)


def openai(exc: BaseException) -> bool:
    """Service-failure detector for OpenAI SDK exceptions."""
    return contains_any(_exc_to_str(exc), OPENAI_SERVICE_FAILURES)


def bedrock(exc: BaseException) -> bool:
    """Service-failure detector for AWS Bedrock SDK exceptions."""
    return contains_any(_exc_to_str(exc), BEDROCK_SERVICE_FAILURES)


def gemini(exc: BaseException) -> bool:
    """Service-failure detector for Google Gemini SDK exceptions."""
    return contains_any(_exc_to_str(exc), GEMINI_SERVICE_FAILURES)


def is_http_status_service_failure(code: int) -> bool:
    """True if `code` is a typically service-side HTTP status."""
    return code in HTTP_SERVICE_STATUSES


def any_of(*detectors):
    """Compose multiple detectors — count if ANY of them matches.

    Handy when the same call site might talk to multiple providers
    behind a uniform interface (e.g. a model-router that translates
    Anthropic / OpenAI errors into a common shape).

        cb.call(fn, should_count=predicates.any_of(predicates.anthropic, predicates.openai))
    """

    def _composed(exc: BaseException) -> bool:
        return any(d(exc) for d in detectors)

    return _composed


__all__ = [
    "ANTHROPIC_SERVICE_FAILURES",
    "BEDROCK_SERVICE_FAILURES",
    "GEMINI_SERVICE_FAILURES",
    "HTTP_SERVICE_STATUSES",
    "OPENAI_SERVICE_FAILURES",
    "any_of",
    "anthropic",
    "bedrock",
    "contains_any",
    "gemini",
    "is_http_status_service_failure",
    "openai",
]
