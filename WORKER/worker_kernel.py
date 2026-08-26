"""
worker_kernel.py — VORPAL Worker · autonomous kanban→Hermes task loop
[◈VORPAL◈]

The sentinel blade: claims tasks off the Hermes kanban board, executes them via
one-shot Hermes, verifies the result through the VORPAL gate, then completes or
blocks on the board. Durable, ledger-disciplined, VORPAL-clean.

Loop (per task):
  1. CLAIM   — `hermes kanban claim <id>` (atomic, TTL)
  2. EXECUTE — `hermes chat -q "<task>"` (bounded timeout, model override)
  3. VERIFY  — VORPAL gate: non-empty output, exit 0, no failure tokens
  4. REPORT  — complete() with result+metadata, OR block() with typed reason
  5. LEDGER  — append [ERR_*]/[VERIFY] delta to EVOLVE/NOTES.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

# Ensure WORKER/ is importable whether run directly or imported as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import hermes_bridge as hb

# ── VORPAL gate tokens — a task whose output contains these is NOT green ──
FAIL_TOKENS = ("[FAIL", "FAILED", "[FAILURE]", "NEEDS ATTENTION", "TRACEBACK")

WORKTREE = Path(__file__).resolve().parents[1]          # Desktop/VORPAL
LEDGER = WORKTREE / "EVOLVE" / "NOTES.md"
CLAIM_TTL = int(os.environ.get("VORPAL_CLAIM_TTL", "900"))
EXEC_TIMEOUT = int(os.environ.get("VORPAL_EXEC_TIMEOUT", "600"))
HEARTBEAT_EVERY = 60


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def verify_output(text: str) -> tuple[bool, str]:
    """VORPAL gate: non-empty, no failure tokens. Returns (ok, reason)."""
    text = text.strip()
    if not text:
        return False, "empty output"
    for tok in FAIL_TOKENS:
        if tok in text.upper():
            return False, f"failure token '{tok}' in output"
    return True, ""


def ledger(entry: str) -> None:
    """Append a line to EVOLVE/NOTES.md (audit trail, never delete)."""
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(f"\n[{now()}] {entry}\n")


def build_prompt(task: hb.Task, description: str) -> str:
    """Compose a self-contained one-shot prompt from the kanban task."""
    return (
        "You are the VORPAL worker executing a kanban task. "
        "Do the work completely and verify it yourself before finishing. "
        "If you cannot complete it, say so explicitly and state what is missing.\n\n"
        f"TASK: {task.title}\n"
        f"TASK ID: {task.id}\n"
        f"WORKSPACE: {task.workspace or 'scratch'}\n\n"
        f"CONTEXT:\n{description}\n\n"
        "Report what you did and the result. Include file paths of anything created."
    )


def process_task(task: hb.Task, model: str | None, provider: str | None,
                 dry_run: bool) -> dict:
    """Run one task through the full loop. Returns a report dict."""
    start = time.monotonic()
    report = {"task": task.id, "title": task.title, "status": "pending"}

    try:
        # 1. CLAIM
        ws = hb.claim(task.id, ttl=CLAIM_TTL)
        report["claimed_workspace"] = ws
        hb.heartbeat(task.id, note="claimed by VORPAL worker")
        ledger(f"[ERR_*] task {task.id} claimed (ws={ws})")
        if dry_run:
            report["status"] = "would-execute"
            return report

        # 2. EXECUTE (with heartbeat keep-alive on long runs)
        description = hb.task_description(task.id)
        prompt = build_prompt(task, description)
        report["prompt"] = prompt[:200]

        # 3. VERIFY + heartbeat
        hb.heartbeat(task.id, note="executing via hermes chat -q")
        output = hb.chat(prompt, model=model, provider=provider, timeout=EXEC_TIMEOUT)

        ok, reason = verify_output(output)
        elapsed = int(time.monotonic() - start)
        report["elapsed_s"] = elapsed
        report["output_head"] = output[:300]

        if ok:
            hb.complete(task.id, result=output[:1500],
                        metadata={"elapsed_s": elapsed, "model": model or "default",
                                  "provider": provider or "default"})
            report["status"] = "done"
            ledger(f"[VERIFY] task {task.id} COMPLETE ({elapsed}s) — {task.title}")
        else:
            hb.block(task.id, reason=f"verify gate: {reason}", kind="transient")
            report["status"] = "blocked"
            report["block_reason"] = reason
            ledger(f"[ERR_VERIFY] task {task.id} blocked — {reason}")

    except hb.BridgeError as e:
        report["status"] = "error"
        report["error"] = str(e)
        ledger(f"[ERR_BRIDGE] task {task.id} — {e}")
    except Exception as e:  # noqa: BLE001 — the worker must survive any task
        report["status"] = "error"
        report["error"] = f"{type(e).__name__}: {e}"
        ledger(f"[ERR_KERNEL] task {task.id} — {type(e).__name__}: {e}")

    return report


def run_once(board: str, max_tasks: int, model: str | None, provider: str | None,
             dry_run: bool, idle_sleep: int) -> None:
    """One sweep: claim and process up to max_tasks ready tasks."""
    ready = hb.list_ready_tasks(board=board)
    if not ready:
        print(f"[{now()}] no ready tasks on '{board}' — sleeping {idle_sleep}s")
        time.sleep(idle_sleep)
        return

    for task in ready[:max_tasks]:
        print(f"[{now()}] → {task.id} | {task.title[:70]}")
        rep = process_task(task, model, provider, dry_run)
        print(f"    [{rep['status']}] {rep.get('elapsed_s', '')}s  "
              f"{rep.get('block_reason') or rep.get('error') or ''}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="vorpal-worker", description="VORPAL kanban→Hermes worker")
    ap.add_argument("--board", default=os.environ.get("VORPAL_BOARD", "default"))
    ap.add_argument("--once", action="store_true", help="single sweep, then exit")
    ap.add_argument("--max-tasks", type=int, default=1)
    ap.add_argument("--model", default=os.environ.get("VORPAL_MODEL"))
    ap.add_argument("--provider", default=os.environ.get("VORPAL_PROVIDER"))
    ap.add_argument("--dry-run", action="store_true", help="claim + report, do not execute")
    ap.add_argument("--idle-sleep", type=int, default=30,
                    help="seconds to wait when the board is empty (loop mode)")
    args = ap.parse_args()

    print(f"[{now()}] VORPAL worker up — board='{args.board}' "
          f"model={args.model or 'default'} dry={args.dry_run}")
    if args.once:
        run_once(args.board, args.max_tasks, args.model, args.provider, args.dry_run, 0)
    else:
        while True:
            try:
                run_once(args.board, args.max_tasks, args.model, args.provider,
                         args.dry_run, args.idle_sleep)
            except KeyboardInterrupt:
                print(f"\n[{now()}] worker halted.")
                break
            except Exception as e:  # noqa: BLE001 — never die silently
                ledger(f"[ERR_KERNEL] sweep failed — {type(e).__name__}: {e}")
                time.sleep(args.idle_sleep)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
