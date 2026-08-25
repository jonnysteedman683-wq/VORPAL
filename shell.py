#!/usr/bin/env python3
"""OMNIPRIME Agent-OS shell — command surface + --selftest gate.

Satisfies hermes_verify_os_ready.py stage_shell:
  `python shell.py --selftest` must exit 0 and emit a RESULT: line.

Stdlib-only. Watermark: [OMNIPRIME-FORGE]
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _selftest() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("python_runtime", sys.version_info >= (3, 11)))
    try:
        kp = Path(__file__).resolve().parent / "kernel.py"
        spec = importlib.util.spec_from_file_location("_shell_kernel", kp)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        snap = mod.ps()
        checks.append(("kernel_ps_ok", isinstance(snap, dict) and snap.get("ok") is True))
    except Exception:
        checks.append(("kernel_ps_ok", False))

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"RESULT: {'PASS' if passed == total else 'FAIL'}  ({passed}/{total})")
    return 0 if passed == total else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    print("OMNIPRIME Agent-OS shell. Use --selftest for diagnostics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
