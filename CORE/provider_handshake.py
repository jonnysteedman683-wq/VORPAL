"""External LLM/API Handshake Protocol.

[◈VORPAL◈] CORE provider_handshake — makes the GOAL_1.2 [IMPLEMENTED]
claim real (EVOLVE/GOALS/GOALS.md). It is the single outbound seam for
talking to external LLM/API providers (Anthropic / OpenAI / Bedrock /
Gemini-shaped endpoints) and routes every call through
``CORE.llm_circuit_breaker`` so that:

  * PROVIDER-side failures (5xx, overloaded, rate-limited) trip the
    breaker for everyone, then let one probe through after the
    recovery window.
  * CALLER-side failures (4xx auth/validation) are raised but do NOT
    poison the breaker — a bad prompt shouldn't make the provider look
    dead to the rest of the system.

The transport is injected (``Callable[[ProviderRequest], ProviderResponse]``
or an async equivalent), so the handshake is fully testable without
network. ``urllib_transport`` ships as a stdlib reference transport for
real HTTP calls.

Import convention (CORE has no __init__.py, matching the rest of CORE):
    import sys, os
    sys.path.insert(0, os.path.join(ROOT, "CORE"))
    import provider_handshake as ph
"""

from __future__ import annotations

import inspect
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

# Make the sibling breaker package importable regardless of how this
# module was reached (CORE is a flat dir, not a package).
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from llm_circuit_breaker import (  # noqa: E402
    AsyncCircuitBreaker,
    BreakerConfig,
    CircuitBreaker,
    CircuitOpenError,
    predicates,
)

__version__ = "1.0.0"

__all__ = [
    "Provider",
    "HandshakeConfig",
    "ProviderRequest",
    "ProviderResponse",
    "HandshakeError",
    "ClientError",
    "ServiceError",
    "ProviderHandshake",
    "urllib_transport",
]


class Provider(str, Enum):
    """Supported provider families (shapes the default auth header)."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    BEDROCK = "bedrock"
    GEMINI = "gemini"


@dataclass
class HandshakeConfig:
    """Connection + breaker config for one provider endpoint."""

    provider: Provider
    base_url: str = ""
    api_key_env: str = ""
    model: str = ""
    failure_threshold: int = 5
    recovery_timeout_s: float = 30.0

    def resolved_api_key(self) -> str:
        """Return the API key from the environment, or empty string."""
        if not self.api_key_env:
            return ""
        return os.environ.get(self.api_key_env, "")


@dataclass
class ProviderRequest:
    """Normalized outbound request handed to a transport."""

    payload: dict
    headers: dict = field(default_factory=dict)


@dataclass
class ProviderResponse:
    """Normalized response returned by a transport."""

    status: int
    body: Any
    ok: bool


class HandshakeError(Exception):
    """Base error for handshake failures (raised to callers)."""

    service: bool = False


class ClientError(HandshakeError):
    """Caller-side failure (4xx auth/validation). Must NOT trip breaker."""

    service = False


class ServiceError(HandshakeError):
    """Provider-side failure (5xx / overloaded). Trips the breaker."""

    service = True

    def __init__(self, status: int, body: Any, code: str = ""):
        self.status = status
        self.body = body
        self.code = code
        super().__init__(f"{code or 'service_error'} status={status}")


def _extract_code(body: Any) -> str:
    """Best-effort extraction of a provider error code from a response body."""
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict) and err.get("type"):
            return str(err["type"])
        if isinstance(err, str):
            return err
        if body.get("type"):
            return str(body["type"])
    return ""


def _auth_header(provider: Provider) -> str:
    return "x-api-key" if provider == Provider.ANTHROPIC else "Authorization"


class ProviderHandshake:
    """Outbound seam: wraps a transport in a provider-aware breaker.

    Usage::

        hs = ProviderHandshake(
            HandshakeConfig(provider=Provider.OPENAI, base_url=URL,
                            api_key_env="OPENAI_API_KEY"),
            urllib_transport(cfg),
        )
        resp = hs.request({"model": "gpt-5", "messages": [...]})
    """

    def __init__(
        self,
        config: HandshakeConfig,
        transport: Callable[[ProviderRequest], Any],
    ) -> None:
        self.config = config
        self._transport = transport
        self._breaker = CircuitBreaker(
            BreakerConfig(config.failure_threshold, config.recovery_timeout_s)
        )
        self._abreaker = AsyncCircuitBreaker(
            BreakerConfig(config.failure_threshold, config.recovery_timeout_s)
        )
        # Only caller-side (ClientError) is excluded; everything else
        # (provider 5xx + transport/network faults) trips the breaker.
        self._should_count: Callable[[BaseException], bool] = (
            lambda exc: not isinstance(exc, ClientError)
        )

    # ---- sync path ----

    def request(
        self, payload: dict, headers: Optional[dict] = None
    ) -> ProviderResponse:
        """Run one outbound request under the breaker."""
        req = ProviderRequest(payload=payload, headers=headers or {})

        def _call() -> ProviderResponse:
            resp = self._transport(req)
            if not resp.ok:
                if predicates.is_http_status_service_failure(resp.status):
                    raise ServiceError(
                        resp.status, resp.body, _extract_code(resp.body)
                    )
                raise ClientError(resp.status, resp.body)
            return resp

        try:
            return self._breaker.call(_call, should_count=self._should_count)
        except CircuitOpenError:
            raise HandshakeError(
                f"circuit open for {self.config.provider.value}"
            )

    # ---- async path ----

    async def arequest(
        self, payload: dict, headers: Optional[dict] = None
    ) -> ProviderResponse:
        """Async variant of :meth:`request`."""
        req = ProviderRequest(payload=payload, headers=headers or {})

        async def _call() -> ProviderResponse:
            result = self._transport(req)
            if inspect.isawaitable(result):
                result = await result
            if not result.ok:
                if predicates.is_http_status_service_failure(result.status):
                    raise ServiceError(
                        result.status, result.body, _extract_code(result.body)
                    )
                raise ClientError(result.status, result.body)
            return result

        try:
            return await self._abreaker.call(_call, should_count=self._should_count)
        except CircuitOpenError:
            raise HandshakeError(
                f"circuit open for {self.config.provider.value}"
            )


def urllib_transport(
    config: HandshakeConfig,
) -> Callable[[ProviderRequest], ProviderResponse]:
    """Stdlib ``urllib`` reference transport for real HTTP providers.

    Returns a callable ``ProviderRequest -> ProviderResponse``. No third-party
    dependencies. The breaker in :class:`ProviderHandshake` does the
    resilience work; this just performs the POST and normalizes the result.
    """
    import json
    import urllib.error
    import urllib.request

    api_key = config.resolved_api_key()
    auth_hdr = _auth_header(config.provider)

    def _t(req: ProviderRequest) -> ProviderResponse:
        url = config.base_url
        data = json.dumps(req.payload).encode("utf-8")
        headers = {"Content-Type": "application/json", **req.headers}
        if api_key:
            headers[auth_hdr] = (
                f"Bearer {api_key}"
                if auth_hdr == "Authorization"
                else api_key
            )
        r = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(r, timeout=30) as resp:
                raw = resp.read()
                status = resp.status
        except urllib.error.HTTPError as e:  # noqa: B014
            raw = e.read()
            status = e.code
        try:
            body = json.loads(raw) if raw else None
        except Exception:
            body = raw
        return ProviderResponse(status=status, body=body, ok=200 <= status < 300)

    return _t
