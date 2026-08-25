"""OMNIPRIME cost ledger -- VARIANT A.

Original, self-contained token-economy ledger. Persists to cost_ledger_a.json
next to this module. Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

VARIANT = "A"
DEFAULT_BALANCE = 1000
_MODULE_DIR = Path(__file__).resolve().parent
_LEDGER_NAME = "cost_ledger_a.json"
_ENV_OVERRIDE = "OMNIPRIME_COST_LEDGER_A_PATH"


class BlockedError(RuntimeError):
    """Raised when a self-dispatch would drive the balance negative."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ledger_path() -> Path:
    override = os.environ.get(_ENV_OVERRIDE)
    if override:
        return Path(override).expanduser().resolve()
    return _MODULE_DIR / _LEDGER_NAME


def _blank(path: Path) -> dict:
    return {
        "variant": VARIANT,
        "ledger_id": uuid.uuid4().hex,
        "created": _now(),
        "updated": _now(),
        "balance": DEFAULT_BALANCE,
        "debits": {},   # packet_id -> total tokens spent
        "credits": {},  # artifact_id -> total tokens credited
        "journal": [],  # append-only entries
    }


def _load(path: Path | None = None) -> dict:
    p = path or ledger_path()
    if p.exists():
        try:
            with p.open("r", encoding="utf-8") as fh:
                state = json.load(fh)
            state.setdefault("balance", DEFAULT_BALANCE)
            state.setdefault("debits", {})
            state.setdefault("credits", {})
            state.setdefault("journal", [])
            return state
        except (json.JSONDecodeError, OSError):
            pass
    state = _blank(p)
    _save(state, p)
    return state


def _save(state: dict, path: Path | None = None) -> None:
    p = path or ledger_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = _now()
    payload = json.dumps(state, indent=2, sort_keys=True)
    state["checksum"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    with p.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)


def _journal(state: dict, kind: str, ref: str, tokens: int, ok: bool) -> None:
    state["journal"].append(
        {
            "ts": _now(),
            "kind": kind,
            "ref": ref,
            "tokens": int(tokens),
            "ok": bool(ok),
            "balance_after": state["balance"],
        }
    )
    if len(state["journal"]) > 500:
        state["journal"] = state["journal"][-500:]


# ---------------------------------------------------------------- public API

def ledger_balance() -> int:
    return int(_load()["balance"])


def ledger_spend(packet_id: str, tokens: int) -> bool:
    """Debit `tokens` against `packet_id`. Rejected if balance insufficient."""
    tokens = int(tokens)
    state = _load()
    if tokens < 0:
        return False
    if state["balance"] - tokens < 0:
        _journal(state, "spend_rejected", str(packet_id), tokens, False)
        _save(state)
        return False
    state["balance"] -= tokens
    key = str(packet_id)
    state["debits"][key] = int(state["debits"].get(key, 0)) + tokens
    _journal(state, "spend", key, tokens, True)
    _save(state)
    return True


def ledger_credit(artifact_id: str, tokens: int) -> int:
    """Award credit for a PASS-verified artifact. Returns the new balance."""
    tokens = max(0, int(tokens))
    state = _load()
    state["balance"] += tokens
    key = str(artifact_id)
    state["credits"][key] = int(state["credits"].get(key, 0)) + tokens
    _journal(state, "credit", key, tokens, True)
    _save(state)
    return int(state["balance"])


def can_self_dispatch(cost: int, raise_on_block: bool = False) -> bool:
    """M3 gate: True only when the current balance covers `cost`."""
    cost = int(cost)
    balance = ledger_balance()
    allowed = cost >= 0 and balance >= cost
    if not allowed and raise_on_block:
        raise BlockedError(
            f"self-dispatch BLOCKED: cost={cost} exceeds balance={balance}"
        )
    return allowed


def ledger_report() -> dict:
    state = _load()
    return {
        "variant": VARIANT,
        "path": str(ledger_path()),
        "balance": int(state["balance"]),
        "packets": len(state["debits"]),
        "artifacts": len(state["credits"]),
        "spent": sum(int(v) for v in state["debits"].values()),
        "credited": sum(int(v) for v in state["credits"].values()),
    }


def ledger_reset(balance: int = DEFAULT_BALANCE) -> int:
    p = ledger_path()
    state = _blank(p)
    state["balance"] = int(balance)
    _save(state, p)
    return int(balance)


if __name__ == "__main__":
    rpt = ledger_report()
    print(f"[cost_ledger:{VARIANT}] path={rpt['path']}")
    print(f"[cost_ledger:{VARIANT}] balance={rpt['balance']}")
    print(
        f"[cost_ledger:{VARIANT}] packets={rpt['packets']} artifacts={rpt['artifacts']} "
        f"spent={rpt['spent']} credited={rpt['credited']}"
    )
    ready = rpt["balance"] > 0
    print(f"[cost_ledger:{VARIANT}] os_ready={'YES' if ready else 'NO'}")
    sys.exit(0 if ready else 1)
