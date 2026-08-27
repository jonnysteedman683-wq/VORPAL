---
name: markus-os-development
category: software-development
description: Use when developing or modifying MARKUS OS modules — backend robustness, intent routing, kernel, cortex. Canonical dev conventions for the stack.
version: 1.0.0
author: Jonny Steedman
license: MIT
metadata:
  hermes:
    tags: [markus-os, backend, router, kernel, cortex, development]
    related_skills: [self-evolution-and-code-optimization, markus-os-dev-operations, markus-upgrade-start, markus-autonomous-dice-engine]
---

# MARKUS OS Development

## When to Use

- Single source of truth for model routing: `markus_brain_backend.TIER_MODELS`
  is the canonical router tier -> Nous model map; `markus_router.py` imports it.
  Never define a second model map in the router — divergence produced phantom
  `openrouter/*:free` IDs that no client could call while the brain actually
  called deepseek via Nous (telemetry learned from a model that never ran).
  Fix = one shared constant map + phantom-ID sweep
  (`grep -rn "openrouter/" --include="*.py" .`). Gate:
  `hermes_verify_markus_brain.py` G3 alignment invariant + G4 no-phantom sweep.
- Brain gate: `hermes_verify_markus_brain.py` (5 gates, opt-in live probe via
  `MARKUS_BRAIN_LIVE_PROBE=1`). Loading modules by path in a harness using
  dataclasses requires `sys.modules[spec.name] = mod` BEFORE exec_module, and
  class attributes read off the class (`R = rt.MarkusIntentRouter`).
- Server restart required after edits: `markus_server.py` imports router +
  brain backend at startup; the live PID on 8128 keeps the old module in
  memory until `python markus_server.py` is restarted.
- Cost ledger: `markus_brain_backend.py` has per-call accounting.
  `MODEL_PRICES` is the per-token USD table (verify live via the Nous
  `/models` catalog when adding a model), `record_cost()` appends a
  thread-safe JSONL entry to `markus_brain_cost_ledger.jsonl`, and
  `ask_brain()` captures usage from the API response automatically.
  `estimate_cost()` fails safe to $0 for unknown models. Check the ledger
  with `python markus_brain_backend.py --ledger`. Gate:
  `hermes_verify_brain_cost.py`.

Use when writing, fixing, or auditing MARKUS OS backend modules: `markus_server.py`,
`markus_router.py`, `markus_kernel.py`, `markus_db.py`, `markus_resilience.py`,
`markus_mesh.py`, `markus_thors.py`.

## Conventions
- Python 3.11, stdlib-first. ThreadingHTTPServer for the API surface (port 8128).
- Cortex DB lives at `markus_private/vault/markus_cortex.db` (PersistentCortexDB).
- Router decisions carry `target_model`, `tier_category`, `confidence`, `reason`.
- Every module must pass `python -m py_compile` and the integration harness
  (`markus_integration_test.py`, currently 9/9).

## Common Fix Patterns
- Handler alias / NameError after a class rename → update the `Handler =` alias mapping.
- `import error` from a module referencing a moved symbol → search the repo for the old name first.
- New SQL against the cortex → use `cortex_execute(sql, params)` for raw statements.
- Kanban worker SQL must match the LIVE board at `%LOCALAPPDATA%/hermes/kanban.db` (has `task_runs`,
  `consecutive_failures`, `last_failure_error`, `max_retries`, `claim_lock`/`claim_expires`/`worker_pid`) —
  re-check `PRAGMA table_info(tasks)` before trusting old SELECT/UPDATE shapes. Claims are absolute-deadline
  leases (`claim_expires = now+300`); stale = `claim_expires < now` (NOT `< now - max_age`).
- `_ask_markus_brain` calls the Nous inference API directly via `markus_brain_backend.ask_brain`
  (Hermes shell-out retired 2026-08-26). Tier->model map lives in `TIER_MODELS`. Brain probe:
  `python markus_brain_backend.py "Reply with exactly: BRAIN_LIVE"`.
- Obsidian Palace Bridge (`markus_obsidian_sync.py`) targets the LIVE `Documents/VORPAL Vault`
  (`Obsidian Vault` is a frozen fallback). Two daily outputs under `Journal/Markus/`:
  `*-MARKUS-CORTEX.md` (rolling top-50 digest, regenerated) and `*-MARKUS-LIVE.md`
  (append-only stream, watermark-gated via `VAULT_SYNC_LAST_TS` register — never rewrite old bullets).
  Server wiring: `GET /api/vault/sync` on-demand flush + boot catch-up + auto-sync daemon (300s) in `run_server()`.
- Windows server restart: `taskkill //PID`/`cmd //c` get mangled by MSYS — use
  `powershell -NoProfile -Command "Stop-Process -Id <pid> -Force"`, then relaunch via
  terminal(background=true) (never nohup).
- The LIVE MARKUS server runs autonomous dice/upgrade cycles that can commit in-progress
  working-tree edits as their own commit (e.g. `PAYDOWN_TECH_DEBT`). If your changes vanish from
  `git status` mid-task, check `git log` for a fresh autonomous commit — your work is usually
  swept in there, not lost. Verify with `git show <sha> --stat` before assuming damage.
- Command Deck (`markus-os.html`) audio: `AUDIO_PROFILES` map in the upgrade-8 block; every kernel
  `ProcessState` (READY/RUNNING/BLOCKED/TERMINATED/FAILED) has a chord via `playStateChime()`.
  Toggle lives in `.system-stats` (needs `pointer-events: auto` — the `.hud` container is
  `pointer-events: none`). Autoplay requires the `pointerdown` boot-chime kickstart.

## Verification
```bash
python -m py_compile markus_server.py
python markus_integration_test.py
python phoenix_cli.py batch .
```
