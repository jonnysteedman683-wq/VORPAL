---
name: agent-orchestration
description: Use when managing multiple specialized AI agents.
---

# Agent Orchestration & Local Swarm Integration

Use this skill when the task is to integrate multiple local codebases/runtimes into a unified autonomous system: Hermes + Neurocore + OMNIBUS + ARISE-style subsystems, with a shared backend, frontend controller, and safety-gated intent routing.

## Core Architecture

A robust orchestration engine consists of three primary pillars:

1.  **The Goal Manager (The Ledger):**
    - Maintains a dependency graph of atomic tasks.
    - Tracks task status (`PENDING` $\to$ `IN_PROGRESS` $\to$ `COMPLETED`/`FAILED`).
    - Ensures tasks are only "ready" when all dependencies are met.

2.  **The Agent Team (The Dispatcher):**
    - Maps specialized roles to agent instances.
    - Matches task descriptions to the most appropriate role (e.g., "Design" $\to$ Architect, "Optimize" $\to$ Hacker).
    - Handles the assignment loop: `Ready Tasks` $\to$ `Best Agent` $\to$ `Execution`.

3.  **The Specialized Roles:**
    - **Strategist:** Decomposes the root goal into the task graph (best suited for high-reasoning models like Grok or Llama 3).
    - **Architect:** Defines interfaces and system structure to prevent technical debt.
    - **Feature Dev:** Implements logic.
    - **Hacker:** Focused on performance, "breaking" the system to find bottlenecks, and unconventional optimizations.
    - **Validator:** Performs QA and verifies task completion.

## Implementation Workflow

1.  **Define the Role Enum:** Establish a strict set of roles to drive the dispatcher's logic.
2.  **Implement Goal Tracking:** Create a `GoalManager` that can add tasks with a list of dependency IDs.
3.  **Build the Role-Based Matcher:** In the `AgentTeam` class, implement a heuristic or LLM-based matcher that assigns tasks based on keywords (e.g., "verify", "implement", "plan").
4.  **Set up the Execution Loop:** 
    - Query `GoalManager` for "ready" tasks.
    - Assign to available agents.
    - Execute and update status.
    - Repeat until the root goal is marked complete.

## Hive Swarm Integration Pattern

When unifying Hermes + Neurocore + OMNIBUS-style frontends, use this proven sequence:

1.  **CJS/ESM Bridge**: Create `neurocore-bridge.cjs` in the Neurocore repo using dynamic `import('file://' + path)` from Node `require()`. Cache loaded modules to avoid repeated transpilation.
2.  **Server Wiring**: Add `/api/neurocore/*` routes to `server.js` or `server.cjs`. Keep `server.js` legacy for static file serving; add CJS shim if `package.json` has `"type": "module"`.
3.  **Frontend Dispatch**: Add `dispatch()` to `AgentSystem` class. Route through `/api/neurocore/intent` first, fall back to `/api/chat` on failure.
4.  **Auto-Connect**: In `app.js`, call `initHiveSwarmMind()` on `DOMContentLoaded` to establish the swarm connection.
5.  **Health Monitoring**: Implement `/api/neurocore/health` using `capabilities()` instead of non-existent `getHealthMetrics()`.

## Pitfalls & Lessons

- **The "Doer" Trap:** Do not let "Feature Dev" agents decide the task list. This leads to scope creep and architectural drift. Always route planning through a dedicated **Strategist**.
- **Dependency Deadlocks:** Ensure the `GoalManager` can detect circular dependencies in the task graph.
- **Context Fragmentation:** For large codebases, use a "Context Map" (ledger) to track which agent "owns" which file to avoid conflicting edits.
- **Cost Management:** Use local models (e.g., via Ollama) for the bulk of the execution/hacking, and reserve high-cost APIs (like Grok) for the initial strategic decomposition.
- **CJS/ESM Mismatch:** If `package.json` has `"type": "module"`, every `.js` file is loaded as ESM. `require()` will fail at runtime even if Node syntax checks pass. Rename backend entry files to `.cjs`, update `package.json` `main`/`scripts`, and check for other legacy `.js` files that also use `require()`.
- **Neurocore Import Path:** From OMNIBUS, Neurocore TS modules must be loaded via dynamic `import('file://' + path)` on Windows, with backslashes replaced by forward slashes. Use an absolute path to avoid `../neurocore/` resolution failures across sibling drives.
- **Missing Adapter Methods:** Do not assume `getHealthMetrics()` exists on `OmniSwarmAdapter`. Use `capabilities()` plus local `systemState` for health JSON to avoid runtime 500s.
- **Verification:** After adding `/api/neurocore/*`, run `node --check`, start the server, and curl `/api/neurocore/connect`, `/api/neurocore/intent` at high/medium/low confidence, `/api/neurocore/health`, and `/api/neurocore/emergency-stop`. Run `npm run test`; the existing Neurocore test suites are already good integration coverage.

## Multi-Profile Triad Rings (TRIAS pattern)
For running multiple Hermes profiles as a cyclically-routing work ring with
shared grading, see `references/trias-multi-profile-triad-loop.md` — covers
bus topology, heartbeat cron gotchas (one-shot vs recurring), staged-soul
architecture, Lingua compression channel, and earned recursive spawning.

## Verification
- Run a mock simulation with a known dependency chain (e.g. Design $\to$ Implement $\to$ Optimize $\to$ Verify).
- Verify that tasks are not assigned until their dependencies are `COMPLETED`.

## Hermes CLI Worker Agents (absorbed from `hermes-worker-agents`)

When the worker is a thin external agent driving Hermes through its OWN CLI primitives (instead of a custom router/mesh/server), reuse the kanban worker kernel. The kanban board is the durable queue, `hermes chat -q "<prompt>"` is the executor, cron is scheduling, `hermes send` is delivery.

- **Keep it thin**: `worker_kernel.py` (the loop) → `hermes_bridge.py` (ONLY file that calls the CLI). Keep the kernel Hermes-agnostic; the bridge is the single seam to the CLI.
- **Per-task loop**: `kanban list` → `kanban claim --ttl` (returns resolved workspace path) → heartbeat on long runs → compose a SELF-CONTAINED prompt (title + task id + workspace + full description; `chat -q` has no session memory) → execute with generous timeout (600s) → verify gate (non-empty output, exit 0, no `[FAIL`/`FAILED`/`[FAILURE]`/`NEEDS ATTENTION`/`TRACEBACK`, compare case-insensitive against `output.upper()`) → `kanban complete --result <summary> --metadata <json>` OR `kanban block --kind <type> --reason` → append a ledger line.
- **Kanban CLI gotchas**: `--board <slug>` goes BEFORE the verb (`hermes kanban --board default list`); `(no matching tasks)` on an empty board is CORRECT output; `block` requires `--kind`; `heartbeat` takes `--note`.
- **Component verify harnesses**: ship a `hermes_verify_*.py` per component before it's "implemented" — structural (compile + import), behavioral (verify-gate logic), and bridge failure (point HERMES at a fake binary, assert expected exception).
- **Cross-module import**: add `sys.path.insert(0, Path(__file__).resolve().parent)` in component dirs so harnesses load the module both run-directly and imported-as-module.
- **Subprocess discipline**: always `capture_output`, check `returncode != 0`, raise a typed BridgeError with stderr tail; wrap per-task processing in try/except so one poisoned task can't kill the loop (log `[ERR_*]`, continue).

Full verified kanban CLI surface + known-good bridge wrapper: `references/hermes-kanban-cli.md`.

