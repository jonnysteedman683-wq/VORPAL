---
name: markus-autonomous-stack
category: devops
description: Use when automating MARKUS OS or its cron pipeline.
version: 1.0.0
author: Jonny Steedman
license: MIT
created: 2026-08-26
metadata:
  hermes:
    tags: [markus-os, automation, cron, self-evolution, watchdog, deep-pass]
    related_skills: [hermes-cron-patterns, loop-creation, markus-upgrade-start, markus-os-dev-operations]
---

# MARKUS Autonomous Stack

## When to Use
Trigger when the user asks to automate MARKUS OS upgrade cycles, stand up or modify its autonomous cron loops, or diagnose why the upgrade pipeline is quiet/failing. Load this before touching `markus_upgrade_start.py`, the two cron jobs, or the watchdog script.

Two-tier autonomous evolution for MARKUS OS, both running free (nous provider, zero-token watchdog).

## Architecture

| Loop | Schedule | Mode | Cost | Job ID |
|------|----------|------|------|--------|
| `markus-auto-upgrade` | every 6h | `no_agent` script | **0 tokens** | `e2addb50a12e` |
| `markus-deep-pass` | Mon 02:00 (`0 2 * * 1`) | agent-driven | free (deepseek-v4-flash via nous) | `4d4dfb4323a5` |

## Tier 1 — 6h zero-token watchdog
Script: `AppData/Local/hermes/scripts/markus_auto_upgrade.py` (bundled as `scripts/markus_auto_upgrade.py` in this skill).
- Runs `python markus_upgrade_start.py` (dice → debate → validate → skill-patch → reward → commit).
- **Prints nothing on success** (cron stays silent, zero tokens). On failure prints a report → `deliver='all'` alerts.
- Writes audit log to `~/.hermes/cron_log/auto-upgrade-YYYYMMDD-HHMM.log`.
- Uses `sys.executable` (hermes venv 3.11) — never a bare `python` guessed at runtime.

## Tier 2 — Weekly agent deep pass
- Self-contained prompt: red-team → web research → reflexion → ONE targeted backend improvement → `py_compile` + `markus_integration_test.py` (9/9) + `phoenix_cli.py batch .` (0 FAIL) → commit + push → report.
- `enabled_toolsets=['file','terminal']` only (token trim). `deliver='all'`.
- RULES baked in: one retry then report+stop; never touch cron; never restart :8128; minimal verified change.

## Model = free (critical)
- Global default is `provider: nous` + `model.default: deepseek/deepseek-v4-flash`. The deep-pass job is `model:null/provider:null` so it inherits the free default. **Do not pin a paid model.**
- `hermes cron edit` reads a DIFFERENT job store than the `cronjob()` tool — it did not find jobs created via the tool. Manage jobs via the `cronjob` tool, not the CLI.

## Verified operational facts (2026-08-26)
- Smoke-tested both jobs end-to-end via `cronjob(action='run')`.
- Deep pass shipped `f7e79fd` — real fix: `markus_mesh.py` peer-dict race → RLock. Independent git verification confirmed the push.
- The 6h loop never touches the live server on :8128 (Stage 1 only validates compile); the deep pass also leaves it alone.

## Dice Engine Upgrade History

- **Upgrade 48 (2026-08-26)**: Enhanced dice engine from 6 to 36 unique actions
  - Dual 6-sided dice → 36 specific upgrade paths (1-36)
  - Each roll triggers a targeted upgrade with detailed description
  - Previous 5 "technical alternative" shortcuts replaced with specific actions
  
  | Roll | Action | Description |
  |------|--------|-------------|
  | 1 | UPGRADE_UI_ACCESSIBILITY | UI Refresh with Accessibility Overhaul |
  | 2 | UPGRADE_BACKEND_API | Backend Refactor + API Expansion |
  | 3 | UPGGRADE_AI_MODEL | AI Agent Model Swap & Prompt Optimization |
  | 4 | IMPLEMENT_FEATURE_GAP | Feature Gap Analysis & Implementation |
  | 5 | TECHNICAL_ALTERNATIVE_EVAL | Technical Alternative Evaluation |
  | 6 | RE_ROLL_COOLDOWN | Re-Roll (reset cooldown) |
  | 7-12 | UI/Backend/Core/Perf/Security/Explore | Various enhancement tracks |
  | ... | ... | ... |
  | 31-36 | Docs/Code/Architecture/Knowledge/System | Refactor, QA, Debt, Review, Expand, Reset |

## Pitfalls
- **`deliver='local'` defaults to silent** — always set `deliver='all'` on agent jobs so reports reach the user (gateway is running).
- **Curator race**: a background skill curator (`platform=curator`) may archive skills into `skills/.archive` mid-session — never write to archived paths; patcher already skips them.
- **Interpreter path**: pass `C:/` native paths to native python; MSYS `/c/` paths break subprocess.
- Deep pass takes ~45 min (first red-team run can hit the 300s tool timeout — it retries in background).

## Verification checklist
1. `cronjob(action='list')` → both jobs `enabled: true`, sane `next_run_at`.
2. After a run: read output at `AppData/Local/hermes/cron/output/<job_id>/`.
3. Green watchdog run = silent, audit log at `~/.hermes/cron_log/auto-upgrade-*.log`.
4. Independent proof of deep-pass work: `git log` shows the new commit, `git status` clean, server still ONLon 8128.
