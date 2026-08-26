"""
hermes_bridge.py — VORPAL Worker · thin Hermes CLI bridge
[◈VORPAL◈]

Drives Hermes via its own CLI surface (no reinvention):
  - `hermes kanban *`  → durable task board (claim/complete/block/heartbeat)
  - `hermes chat -q`   → one-shot LLM execution with full tool access

Every call: subprocess, bounded timeout, structured result. This is the ONLY
file that talks to the Hermes CLI — the kernel stays Hermes-agnostic.
"""

import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

HERMES = "hermes"  # or shutil.which("hermes")


class BridgeError(RuntimeError):
    """Raised when a Hermes CLI call fails structurally."""


@dataclass
class Task:
    """A kanban task as the worker sees it."""
    id: str
    title: str
    status: str
    board: str = "default"
    assignee: str = ""
    workspace: str = ""
    description: str = ""


def _run(args: list[str], timeout: int = 120, cwd: str | None = None) -> str:
    """Run a hermes subcommand; raise BridgeError on failure."""
    cmd = [HERMES, *args]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
    except subprocess.TimeoutExpired as e:
        raise BridgeError(f"timeout after {timeout}s: {' '.join(cmd)}") from e
    except FileNotFoundError as e:
        raise BridgeError("`hermes` not on PATH") from e
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[-300:]
        raise BridgeError(f"exit {proc.returncode}: {' '.join(cmd)}\n{err}")
    return proc.stdout



def _kanban(subcmd: list[str], board: str | None = None, timeout: int = 60) -> str:
    """Run `hermes kanban [--board X] <subcommand ...>`; --board goes BEFORE the verb."""
    args = ["kanban"]
    if board:
        args += ["--board", board]
    args += subcmd
    return _run(args, timeout=timeout)


def list_ready_tasks(board: str = "default", assignee: str = "") -> list[Task]:
    """List ready/todo tasks on a board."""
    out = _kanban(["list"], board=board, timeout=60)
    tasks: list[Task] = []
    for line in out.splitlines():
        # e.g. "◻ t_abc123  todo      default   ...title"
        parts = line.split()
        if len(parts) >= 4 and parts[1].startswith("t_"):
            t = Task(id=parts[1], title=" ".join(parts[4:]), status=parts[2], board=parts[3])
            if t.status in ("todo", "ready"):
                tasks.append(t)
    return tasks


def claim(task_id: str, ttl: int = 900) -> str:
    """Atomically claim a task; returns the resolved workspace path."""
    out = _kanban(["claim", "--ttl", str(ttl), task_id], timeout=60)
    return out.strip()


def heartbeat(task_id: str, note: str = "") -> None:
    """Keep a long-running claim alive."""
    args = ["heartbeat", task_id]
    if note:
        args += ["--note", note]
    _kanban(args, timeout=60)


def complete(task_id: str, result: str, metadata: dict | None = None) -> None:
    """Mark a task done with a result summary + structured metadata."""
    args = ["complete", task_id, "--result", result]
    if metadata:
        args += ["--metadata", json.dumps(metadata)]
    _kanban(args, timeout=60)


def block(task_id: str, reason: str, kind: str = "transient") -> None:
    """Block a task with a typed reason (capability/dependency/needs_input/transient)."""
    _kanban(["block", task_id, "--kind", kind, "--reason", reason], timeout=60)


def chat(prompt: str, model: str | None = None, provider: str | None = None,
         timeout: int = 600) -> str:
    """One-shot Hermes execution. Returns the final response text."""
    args = ["chat", "-q", prompt, "-Q"]
    if model:
        args += ["-m", model]
    if provider:
        args += ["--provider", provider]
    return _run(args, timeout=timeout)


def task_description(task_id: str) -> str:
    """Fetch a task's full text (title + comments + attachments list)."""
    out = _kanban(["show", task_id], timeout=60)
    return out.strip()

