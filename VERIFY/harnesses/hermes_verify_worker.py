"""
hermes_verify_worker.py — VORPAL Worker verification harness
[◈VORPAL◈] — Gate for WORKER/ (SOUL invariant #7)

Verifies:
  W1  hermes_bridge compiles + imports clean
  W2  worker_kernel compiles + imports clean
  W3  verify_output() gate catches empty output
  W4  verify_output() gate catches failure tokens
  W5  verify_output() accepts clean output
  W6  verify_output() is case-insensitive on tokens
  W7  build_prompt() composes title + id + workspace into the prompt
  W8  ledger() appends to EVOLVE/NOTES.md non-destructively
  W9  FAIL_TOKENS set is non-empty
  W10 bridge raises BridgeError on missing `hermes` binary (structural)

Run:  python VERIFY/harnesses/hermes_verify_worker.py
Exit: 0 = PASS (all checks), 1 = FAIL
"""

import importlib.util
import io
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

WORKER_DIR = Path(__file__).resolve().parents[2] / "WORKER"
PASSED = 0
FAILED = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  [PASS] {name}" + (f" -- {detail}" if detail else ""))
    else:
        FAILED += 1
        print(f"  [FAIL] {name}" + (f" -- {detail}" if detail else ""))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    print(f"HARNESS: hermes_verify_worker.py  (WORKER/ under {WORKER_DIR})")

    bridge_py = WORKER_DIR / "hermes_bridge.py"
    kernel_py = WORKER_DIR / "worker_kernel.py"

    # W1 / W2 — import both modules (compiles + imports clean)
    try:
        bridge = load("hermes_bridge", bridge_py)
        check("W1 bridge imports", True)
    except Exception as e:  # noqa: BLE001
        check("W1 bridge imports", False, str(e))
        bridge = None

    try:
        kernel = load("worker_kernel", kernel_py)
        check("W2 kernel imports", True)
    except Exception as e:  # noqa: BLE001
        check("W2 kernel imports", False, str(e))
        kernel = None

    if kernel is None:
        print("\nRESULT: FAIL (kernel failed to import — aborting)")
        sys.exit(1)

    # W3–W6 — the verify gate itself
    ok, reason = kernel.verify_output("   ")
    check("W3 empty output → fail", not ok and "empty" in reason, reason)

    ok, reason = kernel.verify_output("Everything green")
    check("W4 clean output → pass", ok)

    ok, reason = kernel.verify_output("build FAILED with 3 errors")
    check("W5 failure token → fail", not ok and "FAILED" in reason.upper(), reason)

    ok, reason = kernel.verify_output("I hit a [fail] trying to deploy")
    check("W6 case-insensitive token", not ok, reason)

    # W7 — prompt composition
    if bridge is not None:
        t = bridge.Task(id="t_abc123", title="Build a widget", status="todo",
                        board="default", workspace="/tmp/ws")
        prompt = kernel.build_prompt(t, "do it now")
        check("W7 prompt contains task fields",
              all(x in prompt for x in ("Build a widget", "t_abc123", "/tmp/ws")),
              prompt[:80])
    else:
        check("W7 prompt contains task fields", False, "bridge unavailable")

    # W8 — ledger append is non-destructive
    with tempfile.TemporaryDirectory() as td:
        notes = Path(td) / "NOTES.md"
        notes.write_text("# ledger\n", encoding="utf-8")
        old = kernel.LEDGER
        kernel.LEDGER = notes
        try:
            with redirect_stdout(io.StringIO()):
                kernel.ledger("[VERIFY] test entry")
            text = notes.read_text(encoding="utf-8")
            check("W8 ledger appends non-destructively",
                  text.startswith("# ledger") and "test entry" in text)
        finally:
            kernel.LEDGER = old

    # W9 — FAIL_TOKENS non-empty
    check("W9 FAIL_TOKENS set", len(kernel.FAIL_TOKENS) > 0, str(len(kernel.FAIL_TOKENS)))

    # W10 — bridge structural failure raises BridgeError
    if bridge is not None:
        orig = bridge.HERMES
        bridge.HERMES = "definitely-not-a-real-binary-xyz"
        try:
            bridge._run(["kanban", "list"], timeout=10)
            check("W10 BridgeError on missing binary", False, "no exception raised")
        except bridge.BridgeError as e:
            check("W10 BridgeError on missing binary", True, str(e)[:50])
        except Exception as e:  # noqa: BLE001
            check("W10 BridgeError on missing binary", False, f"wrong type: {type(e).__name__}")
        finally:
            bridge.HERMES = orig
    else:
        check("W10 BridgeError on missing binary", False, "bridge unavailable")

    print(f"\nRESULT: {PASSED} passed, {FAILED} failed, {PASSED + FAILED} total")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
