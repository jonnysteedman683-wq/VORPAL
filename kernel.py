#!/usr/bin/env python3
"""OMNIPRIME Agent-OS kernel — process table + spawn/kill/log surface.

Stdlib-only. Satisfies hermes_verify_os_ready.py stage_kernel: exposes
callable ps(), spawn(), kill(), log(); ps() returns {"ok": True, ...}.

Watermark: [OMNIPRIME-FORGE]
"""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROC_TABLE = ROOT / ".hive" / "bus" / "kernel_proc_table.json"
LOG_PATH = ROOT / ".hive" / "bus" / "kernel.log"

_processes: dict[str, dict] = {}
_next_pid = 1


def _load_table() -> dict[str, dict]:
    if PROC_TABLE.exists():
        try:
            return json.loads(PROC_TABLE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_table(table: dict[str, dict]) -> None:
    PROC_TABLE.parent.mkdir(parents=True, exist_ok=True)
    PROC_TABLE.write_text(json.dumps(table, indent=2), encoding="utf-8")


def ps() -> dict:
    """Process-table snapshot. ok=True signals the kernel is responsive."""
    table = _load_table()
    return {"ok": True, "count": len(table), "processes": table}


def spawn(name: str, entrypoint: str = "", args: list | None = None) -> int:
    """Register a new process; returns its pid."""
    global _next_pid
    table = _load_table()
    if table:
        _next_pid = max(int(k) for k in table) + 1
    pid = _next_pid
    _next_pid += 1
    table[str(pid)] = {
        "name": name,
        "entrypoint": entrypoint,
        "args": args or [],
        "started": time.time(),
        "status": "running",
    }
    _save_table(table)
    return pid


def kill(pid: int) -> bool:
    """Remove a process by pid. Returns True if it was present."""
    table = _load_table()
    key = str(pid)
    if key in table:
        del table[key]
        _save_table(table)
        return True
    return False


def log(msg: str) -> str:
    """Append a kernel log line; returns the log file path."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"[{ts}] {msg}\n")
    return str(LOG_PATH)


if __name__ == "__main__":
    print("OMNIPRIME kernel — process table:", ps())
