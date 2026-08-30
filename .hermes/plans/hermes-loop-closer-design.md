# HERMES as Loop Closer
## Executive Summary

HERMES should **not** be a monolithic executor. It should be a **task orchestrator** that closes the loop between:

```
Citadel (tasks/goals) → HERMES_dispatch → MARKUS (execute) → VORPAL (verify) → Citadel (mark complete)
```

HERMES handles the *meta-work* (deciding what runs where, when to verify, when to close), while MARKUS handles the *execution work* (running code, calling models, writing results).

---

## Implemented

### 1. MARKUS `/api/vorpal/worker/dispatch` endpoint

Added to `markus_server.py`:

```python
POST /api/vorpal/worker/dispatch
{
  "task_id": "task-abc123",
  "prompt": "...",
  "mode": "FORGE|FIELD|FRACTURE",
  "model": "optional",
  "provider": "optional"
}
→ 200 {"status": "DISPATCHED", "run_id": "...", "task_id": "..."}
```

Creates a run record, checkpoints the dispatch, broadcasts SSE event, and returns.

### 2. HERMES dispatch harness

Created `hermes_verify_runtime_spine.py` with tests for:
- Health check (`GET /api/health`)
- SSE handshake
- Trace page
- Run lifecycle (create → route → resume → commit)
- Terminal state blocks resume
- Run list endpoint
- **NEW**: `/api/vorpal/worker/dispatch` dispatch

### 3. Run ledger integration

The dispatch endpoint uses `run_ledger.create_run()` and `run_ledger.checkpoint()` to track task dispatch in SQLite.

---

## Flow: Citadel → MARKUS → VORPAL

1. **HERMES scans Citadel** (via `citadel_recall.search()`) for tasks with `[ ]` unverified
2. **HERMES posts to** `POST /api/vorpal/worker/dispatch` with task data
3. **MARKUS creates run record** in `run_ledger` (status: `RECEIVED`)
4. **VORPAL worker** can claim the run (tracked via SSE events)
5. **Worker executes** via Hermes CLI (`hermes chat -q`) or direct routing
6. **Run transitions** through `VERIFYING` → `COMMITTED` (VORPAL gate)
7. **Result written back** to Citadel via `markus_citadel_bridge.write_note()`

---

## Architecture

```
                    ┌──────────────────┐
                    │  CITADEL (TASK)  │
                    └────────┬─────────┘
                             │ task_id + prompt
                             ▼
┌──────────────────┐    ┌──────────────┐
│  MARKUS SERVER   │◄──▶│  HERMES_DISPATCH  │
│  /api/vorpal/    │    │  (client lib) │
│  worker/dispatch │    └──────────────┘
└────────┬─────────┘
         │
         ▼  creates run, checkpoints, broadcasts
┌──────────────────┐
│ VORPAL WORKER    │
│ (hermes_bridge)  │
│                  │
│ verify_output()  │←── gate
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  CITADEL UPDATE  │
│  mark complete   │
└──────────────────┘
```

---

## Next Steps

1. **Implement HERMES scheduler** (`HERMES_LOOP/hermes_scheduler.py`) to:
   - Scan Citadel Tasks/ Goals/ for `[ ]` unverified
   - Dispatch via `POST /api/vorpal/worker/dispatch`
   - Write results back to Citadel on completion

2. **Tighten VORPAL-MARKUS integration:**
   - MARKUS could poll VORPAL goal pulse before allowing dispatches
   - Runs could be tied to VORPAL goal DAG nodes

3. **Add cron-scheduled scheduler** to run every N minutes
