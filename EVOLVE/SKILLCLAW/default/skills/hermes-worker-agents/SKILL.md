---
name: hermes-worker-agents
description: "Use when building an agent that drives Hermes via its CLI."
---

# Hermes Worker Agents

Build thin external agents that drive Hermes through its OWN CLI primitives instead of reinventing a queue, router, or mesh.

## When to use
- "I want an agent that works with Hermes"
- A worker that claims tasks and executes them
- Automation that consumes the kanban board or fires one-shot chat
- Anything in the lineage of a task "agent that works hand and hand with hermes"

## Core principle: don't reinvent Hermes primitives
Hermes already ships the pieces a worker needs:
- **Queue** → kanban board (durable SQLite, atomic claims, built-in dispatcher)
- **Executor** → `hermes chat -q "<prompt>"` (one-shot LLM with full tool access)
- **Scheduling** → cron / `hermes cron`
- **Delivery** → `hermes send`

A hand-rolled router/mesh/server (the old markus pattern) is the anti-pattern — it duplicated durability, routing, and dispatch that Hermes already provides. Build a THIN kernel:

```
worker_kernel.py (the loop) → hermes_bridge.py (ONLY file that calls the CLI)
                              ├─ hermes kanban claim/complete/block/heartbeat
                              └─ hermes chat -q "self-contained task prompt"
```

Keep the kernel Hermes-agnostic; the bridge is the single seam to the CLI.

## Worker loop (per task)
1. List ready tasks (`kanban list`)
2. Claim atomically (`kanban claim --ttl`) — returns the resolved workspace path
3. Heartbeat on long runs (`kanban heartbeat --note`)
4. Compose a SELF-CONTAINED prompt: title + task id + workspace + full description. `chat -q` has no session memory — every prompt must carry full context.
5. Execute via `hermes chat -q` with a generous timeout (600s; the CLI is slow to start, especially on Windows)
6. **Verify gate**: non-empty output, exit 0, no failure tokens (`[FAIL`, `FAILED`, `[FAILURE]`, `NEEDS ATTENTION`, `TRACEBACK`) — compare against `output.upper()`, case-insensitive
7. Report: `kanban complete --result <summary> --metadata <json>` OR `kanban block --kind <type> --reason`
8. Append a ledger line to the audit file (append-only, never delete)

## Kanban CLI gotchas (bite every time)
- **`--board <slug>` goes BEFORE the verb**: `hermes kanban --board default list` ✓. `hermes kanban list --board default` ✗ → "unrecognized arguments".
- **`(no matching tasks)` on an empty board is CORRECT output** — before debugging a parser, verify the board state didn't just change (tasks deleted, board switched).
- `claim` prints the workspace path; `complete` accepts `--result` / `--summary` / `--metadata` (JSON dict); `block` requires `--kind` (`capability|dependency|needs_input|transient`); `heartbeat` takes `--note`.
- Full verb surface + a known-good bridge wrapper in `references/hermes-kanban-cli.md`.

## Component verify harness (gate before ship)
Every worker component ships with a `hermes_verify_*.py` harness before it's "implemented":
- **Structural**: both modules compile AND import (W1/W2)
- **Behavior**: the verify-gate logic itself — empty→fail, clean→pass, failure-token→fail, case-insensitive
- **Bridge failure**: point the bridge's `HERMES` constant at a fake binary, assert the expected exception type (structural, no live CLI call needed)

## Pitfalls
- **Cross-module import in a component dir**: add `sys.path.insert(0, Path(__file__).resolve().parent)` so the module imports both run-directly and imported-as-module — otherwise the verify harness (which loads it as a module) fails with `ModuleNotFoundError`.
- **`patch` tool whitespace mismatch**: if fuzzy replace keeps failing on a file you wrote, rewrite programmatically via execute_code (read_file → string transform → write_file) instead of retrying the same patch.
- **Subprocess discipline**: always `capture_output`, check `returncode != 0` and raise a typed BridgeError with the stderr tail — never let a failing CLI call pass silently.
- **Survive any task**: wrap per-task processing in try/except so one poisoned task can't kill the loop; log `[ERR_*]` and continue.

## Reference
- `references/hermes-kanban-cli.md` — verified kanban CLI surface + known-good `hermes_bridge.py` patterns.
