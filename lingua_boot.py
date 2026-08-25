# lingua_boot.py -- Lingua Prima boot path for OMNIPRIME
# [OMNIPRIME-FORGE] | Version: 1.0.0 | Lingua Status: V3
#
# Closes [ERR_LINGUA_BOOT_GAP] (VERIFICATION_LOG.md:117).
#
# The gap: LINGUA.md declares "language before identity" and the triad claims
# LP dictionary stability, but NOTHING booted the dictionary at cold-start and
# NO LP events were ever emitted onto the bus. Every stability claim was
# therefore VACUOUS -- true only because the event set was empty.
#
# This module makes it non-vacuous:
#   1. boot()                 loads the canonical engine + emits real LP events
#   2. dictionary_fingerprint() deterministic sha256 over the token surface
#   3. stability_report(n)    boots n times and compares fingerprints
#   4. lp_events()            replays the LP events actually written to the bus
#
# Zero dependencies (stdlib only). Import by path -- the engine lives outside
# any package, so importlib.util is used rather than a package import.

"""OMNIPRIME LINGUA BOOT PATH -- Watermarked [OMNIPRIME-FORGE]"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
ENGINE_PATH = (
    ROOT / "EVOLVE" / "SKILLHUB" / "SKILLS" / "pyramid" / "LANGUAGE" / "lingua_prima.py"
)
BUS = ROOT / ".hive" / "bus"
EVENTS = BUS / "events.jsonl"

WATERMARK = "[OMNIPRIME-FORGE]"
BOOT_ANCHOR = "[OMNIPRIME-BOOT]"

# Lingua status codes (mirror syscalls.LinguaStatus -- kept local to stay
# import-free in either direction).
P = "P"
F = "F"
V3 = "V3"

# The signal alphabet LINGUA.md section 2 promises. boot() proves each of these
# round-trips through the live dictionary, so the doc is checkable, not decor.
BOOT_LEXICON = ("analyze", "build", "test", "validate", "upgrade")
BOOT_CHAIN = "analyze then build then test"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_engine():
    """Import the canonical lingua_prima engine by absolute path.

    Never fork the engine: LINGUA.md names one canonical source and this is the
    only loader OMNIPRIME uses.
    """
    if not ENGINE_PATH.exists():
        raise FileNotFoundError(f"canonical Lingua engine absent: {ENGINE_PATH}")
    spec = importlib.util.spec_from_file_location("lingua_prima_canonical", ENGINE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot build import spec for {ENGINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass/Enum machinery resolves cleanly.
    sys.modules.setdefault("lingua_prima_canonical", module)
    spec.loader.exec_module(module)
    return module


def dictionary_fingerprint(lang=None) -> str:
    """Deterministic sha256 over the dictionary's token surface.

    Fingerprints ONLY the durable surface (token -> word + tier), never the
    ephemeral auto_alias entries, so two cold boots of an unmodified engine
    agree while any real dictionary edit changes the hash.
    """
    if lang is None:
        lang = load_engine().LinguaPrima()

    tokens = getattr(lang._dict, "_tokens", {})
    surface: List[str] = []
    for token in sorted(tokens.keys()):
        info = tokens[token] or {}
        if info.get("source") == "auto" or info.get("category") == "alias":
            continue  # ephemeral session alias -- not part of the stable surface
        surface.append(f"{token}|{info.get('word', '')}|{info.get('tier', '')}")

    payload = "\n".join(surface)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def dictionary_stats(lang=None) -> Dict[str, Any]:
    """Size metrics for the booted dictionary (used in the boot event)."""
    if lang is None:
        lang = load_engine().LinguaPrima()
    d = lang._dict
    return {
        "tokens": len(getattr(d, "_tokens", {})),
        "macros": len(getattr(d, "_macros", {})),
        "aliases": len(getattr(d, "_aliases", {})),
        "signals": len(getattr(d, "_signals", {}) or {}),
    }


def _emit(event: Dict[str, Any]) -> None:
    """Append one LP event to the bus event log (real newline, never '\\n')."""
    BUS.mkdir(parents=True, exist_ok=True)
    with open(EVENTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


def boot(emit: bool = True) -> Dict[str, Any]:
    """Boot Lingua Prima and emit real LP events. Returns the boot record.

    Emits, in order:
      LP_BOOT_START  -- engine located
      LP_LEXICON     -- one event per BOOT_LEXICON round-trip (encode/decode)
      LP_CHAIN       -- semantic-chain compression with measured ratio
      LP_BOOT_READY  -- fingerprint + stats, status V3 (or F on any failure)

    These events are what makes dictionary stability non-vacuous: the LP event
    set on the bus is now provably non-empty and fingerprint-bearing.
    """
    record: Dict[str, Any] = {
        "ts": _now(),
        "anchor": BOOT_ANCHOR,
        "engine": str(ENGINE_PATH),
        "events_emitted": 0,
        "lexicon": {},
        "status": P,
    }
    emitted = 0

    if emit:
        _emit({
            "event": "LP_BOOT_START",
            "ts": record["ts"],
            "agent": "omniprime",
            "engine": str(ENGINE_PATH),
            "lingua": P,
            "watermark": WATERMARK,
        })
        emitted += 1

    try:
        lang = load_engine().LinguaPrima()
    except Exception as exc:  # engine missing/broken -> fail closed, loudly
        record["status"] = F
        record["error"] = f"{type(exc).__name__}: {exc}"
        if emit:
            _emit({
                "event": "LP_BOOT_READY",
                "ts": _now(),
                "agent": "omniprime",
                "lingua": F,
                "error": record["error"],
                "watermark": WATERMARK,
            })
            emitted += 1
        record["events_emitted"] = emitted
        return record

    # --- lexicon round-trip: encode -> decode must return the concept ---
    all_ok = True
    for concept in BOOT_LEXICON:
        token = lang.encode(concept)
        back = lang.decode(token) if token else None
        ok = bool(token) and back == concept
        all_ok = all_ok and ok
        record["lexicon"][concept] = {"token": token, "decoded": back, "ok": ok}
        if emit:
            _emit({
                "event": "LP_LEXICON",
                "ts": _now(),
                "agent": "omniprime",
                "concept": concept,
                "token": token,
                "roundtrip": ok,
                "lingua": V3 if ok else F,
                "watermark": WATERMARK,
            })
            emitted += 1

    # --- semantic chain: must actually compress (guards [ERR_LP_NOCOMPRESS]) ---
    chain_out = lang.compress_semantic_chain(BOOT_CHAIN)
    ratio = round(len(chain_out) / len(BOOT_CHAIN), 3) if BOOT_CHAIN else 1.0
    chain_ok = ratio < 1.0
    all_ok = all_ok and chain_ok
    record["chain"] = {"raw": BOOT_CHAIN, "lingua": chain_out, "ratio": ratio, "ok": chain_ok}
    if emit:
        _emit({
            "event": "LP_CHAIN",
            "ts": _now(),
            "agent": "omniprime",
            "raw": BOOT_CHAIN,
            "compressed": chain_out,
            "ratio": ratio,
            "lingua": V3 if chain_ok else F,
            "watermark": WATERMARK,
        })
        emitted += 1

    fingerprint = dictionary_fingerprint(lang)
    stats = dictionary_stats(lang)
    record["fingerprint"] = fingerprint
    record["stats"] = stats
    record["status"] = V3 if all_ok else F

    if emit:
        _emit({
            "event": "LP_BOOT_READY",
            "ts": _now(),
            "agent": "omniprime",
            "fingerprint": fingerprint,
            "stats": stats,
            "lingua": record["status"],
            "os_ready": all_ok,
            "watermark": WATERMARK,
        })
        emitted += 1

    record["events_emitted"] = emitted
    return record


def lp_events(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return the LP_* events actually present on the bus (newest last)."""
    if not EVENTS.exists():
        return []
    out: List[Dict[str, Any]] = []
    with open(EVENTS, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue  # foreign line -- bus log is shared, stay tolerant
            if str(ev.get("event", "")).startswith("LP_"):
                out.append(ev)
    return out[-limit:] if limit else out


def stability_report(n: int = 3, emit: bool = False) -> Dict[str, Any]:
    """Boot n times and compare fingerprints.

    NON-VACUITY: a report with samples < 2 is meaningless, so `vacuous` is
    reported explicitly and `stable` is only True when at least 2 real boots
    produced identical fingerprints.
    """
    n = max(1, int(n))
    prints: List[str] = []
    for _ in range(n):
        prints.append(boot(emit=emit).get("fingerprint", ""))

    unique = sorted(set(p for p in prints if p))
    vacuous = len(prints) < 2 or not unique
    report = {
        "ts": _now(),
        "samples": len(prints),
        "unique_fingerprints": len(unique),
        "fingerprint": unique[0] if len(unique) == 1 else None,
        "vacuous": vacuous,
        "stable": (not vacuous) and len(unique) == 1,
        "lp_events_on_bus": len(lp_events()),
        "watermark": WATERMARK,
    }
    return report


def main() -> int:
    args = sys.argv[1:]
    cmd = args[0] if args else "boot"

    if cmd == "boot":
        rec = boot()
        print(json.dumps(rec, indent=2))
        return 0 if rec["status"] == V3 else 1

    if cmd == "fingerprint":
        print(dictionary_fingerprint())
        return 0

    if cmd == "stability":
        n = int(args[1]) if len(args) > 1 else 3
        rep = stability_report(n)
        print(json.dumps(rep, indent=2))
        return 0 if rep["stable"] else 1

    if cmd == "events":
        for ev in lp_events(limit=int(args[1]) if len(args) > 1 else 20):
            print(json.dumps(ev))
        return 0

    print(f"usage: {Path(__file__).name} [boot|fingerprint|stability N|events N]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
