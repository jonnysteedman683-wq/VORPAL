"""Verification harness for CORE.provider_handshake.

[AURORAL GATE] Exercises the real module — must print evidence and exit
non-zero on any failure. Returns exit 0 with EMPTY stdout (the false-green
pattern GOAL_6.5 forbids) only if nothing ran, which cannot happen here
because every check prints a line.

Usage:
    python VERIFY/harnesses/hermes_verify_provider_handshake.py
"""

import asyncio
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.abspath(os.path.join(HERE, "..", "..", "CORE"))
if CORE not in sys.path:
    sys.path.insert(0, CORE)

import provider_handshake as ph  # noqa: E402

passed = 0
failed = 0


def check(name: str, cond: bool) -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS {name}")
    else:
        failed += 1
        print(f"FAIL {name}")


class FakeTransport:
    """Deterministic injectable transport (no network)."""

    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.calls = 0

    def __call__(self, req: "ph.ProviderRequest") -> "ph.ProviderResponse":
        self.calls += 1
        if self.mode == "ok":
            return ph.ProviderResponse(status=200, body={"ok": True}, ok=True)
        if self.mode == "service":
            return ph.ProviderResponse(status=503, body={"error": "UNAVAILABLE"}, ok=False)
        if self.mode == "client":
            return ph.ProviderResponse(status=400, body={"error": "bad request"}, ok=False)
        raise RuntimeError("transport misconfigured")


def _hs(mode: str, provider=ph.Provider.OPENAI, threshold=3, timeout=1.0):
    return ph.ProviderHandshake(
        ph.HandshakeConfig(provider=provider, failure_threshold=threshold,
                           recovery_timeout_s=timeout),
        FakeTransport(mode),
    )


# 1. success path
hs = _hs("ok")
r = hs.request({"x": 1})
check("success returns 200", r.status == 200)
check("breaker closed after success", hs._breaker.state.value == "closed")

# 2. provider-side failures trip the breaker, then short-circuit
hs2 = _hs("service")
for _ in range(3):
    try:
        hs2.request({"x": 1})
    except ph.HandshakeError:
        pass
check("breaker open after threshold service failures", hs2._breaker.state.value == "open")
before = hs2._transport.calls
try:
    hs2.request({"x": 1})
    check("short-circuit raises", False)
except ph.HandshakeError:
    check("short-circuit raises HandshakeError", True)
check("short-circuit did NOT call transport", hs2._transport.calls == before)

# 3. caller-side 4xx must NOT trip the breaker
hs3 = _hs("client")
for _ in range(5):
    try:
        hs3.request({"x": 1})
    except ph.HandshakeError:
        pass
check("client errors keep breaker closed", hs3._breaker.state.value == "closed")

# 4. classification types
check("ServiceError is service-side", ph.ServiceError(503, {}).service is True)
check("ClientError is not service-side", ph.ClientError(400, {}).service is False)

# 5. async path
async def _async_case():
    hsa = _hs("service", provider=ph.Provider.ANTHROPIC, threshold=2, timeout=1.0)
    for _ in range(2):
        try:
            await hsa.arequest({"x": 1})
        except ph.HandshakeError:
            pass
    return (await hsa._abreaker.get_state()).value

st = asyncio.run(_async_case())
check("async breaker opens on service failures", st == "open")

# 6. reference transport factory is callable
ut = ph.urllib_transport(ph.HandshakeConfig(provider=ph.Provider.OPENAI, base_url="http://x"))
check("urllib_transport returns callable", callable(ut))

print(f"\nSUMMARY provider_handshake passed={passed} failed={failed}")
sys.exit(1 if failed else 0)
