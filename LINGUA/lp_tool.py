"""
lp_tool.py — Lingua Prima CLI for VORPAL (consolidated single agent).
Wraps the canonical engine (LINGUA/lingua_prima.py) so any profile can
encode/decode compressed traffic without importing the module directly.

Usage:
    python lp_tool.py enc  "analyze then build then test"
    python lp_tool.py dec  "a→b→t"
    python lp_tool.py info "a"
"""
import json
import sys
from pathlib import Path

# Canonical engine is LOCAL to VORPAL's LINGUA dir (the OMNIPRIME reference was
# frozen during consolidation — pointing at it is a stale cross-tree reference).
CANONICAL = Path(__file__).resolve().parent
sys.path.insert(0, str(CANONICAL))

from lingua_prima import LinguaPrima  # noqa: E402


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in {"enc", "dec", "info"}:
        print(__doc__)
        sys.exit(2)
    cmd, text = sys.argv[1], sys.argv[2]
    lp = LinguaPrima()
    if cmd == "enc":
        out = lp.compress_semantic_chain(text) if ("→" not in text and "_" in text or " then " in text) else lp.compress(text)
        raw = len(text)
        print(json.dumps({"lingua": out, "raw_chars": raw,
                          "compressed_chars": len(out),
                          "ratio": round(len(out) / raw, 2) if raw else 0}, ensure_ascii=False))
    elif cmd == "dec":
        print(lp.expand(text))
    elif cmd == "info":
        print(json.dumps(lp.get_token_info(text), ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
