---
name: hermes-cron-patterns
description: "Author Hermes cron jobs: deliver='all', off-peak runs."
category: devops
version: 1.0.0
author: AURORAL
license: MIT
created: 2026-08-20
metadata:
  hermes:
    tags: [cron, scheduling, automation, hermes]
    related_skills: [hermes-agent, hermes-upgrade-check]
---

# Hermes Cron Patterns

## When to Use
- Recurring tasks (upgrades, backups, optimization passes, digests)
- A task must run while the user is away / when no desktop session holds locks
- You need the cron's result delivered back into a chat

## STEP-BY-STEP

1. **Create**:
   ```
   cronjob(action='create', name=<id>, schedule='0 3 * * *',
           prompt=<self-contained instructions>, skills=[...], deliver='all')
   ```
   - `schedule`: cron expr or relative (`30m`, `every 2h`, ISO timestamp).
   - `prompt`: MUST be self-contained (cron runs in a FRESH session with no chat
     context). Include exact commands, verification steps, and what to report.
   - `skills`: load any skills the run needs (e.g. `hermes-upgrade-check`).
   - `deliver`: see below.

2. **deliver gotcha (proven 2026-08-20)**:
   - Default/local cron saves output to the cron log but does NOT auto-deliver
     into a CLI/TUI session (no live-delivery channel). You get NOTHING back.
   - Fix: set `deliver='all'` so the result fans out to every connected platform
     (desktop, telegram, etc.). Without it, verify via `cronjob(action='list')`
     + the saved output only.
   - Special targets: `deliver='telegram'`, `deliver='discord:#chan'`, etc.

3. **Off-peak from a fresh process (key trick)**:
   - Some tasks fail if run from the user's active session because that session
     holds locks (e.g. Hermes venv `.pyd` files). A cron job fires from a FRESH
     Hermes process with no such holders.
   - Use this for: `hermes update --force-venv`, backups of a live state.db,
     anything that needs exclusive file access. Schedule it for a quiet hour.

4. **Manage**:
   - `cronjob(action='list')` → find job_id
   - `cronjob(action='run', job_id=<id>)` → fire immediately (background; result
     re-enters conversation as a new message — do NOT poll/wait)
   - `cronjob(action='update', job_id=<id>, ...)` → change schedule/prompt/deliver
   - `cronjob(action='pause'/'resume'/'remove', job_id=<id>)`

## PITFALLS
- **Forgetting deliver='all'** → symptom: cron ran, you never saw the result.
  Fix: always set deliver unless you explicitly want local-only logging.
- **deliver='all' with no connected platform** → symptom: run succeeds but
  `last_delivery_error: "no delivery target resolved for deliver=all"`. The
  desktop/local session has no gateway-connected channel, so 'all' resolves to
  nothing. Fix: either connect a platform (telegram/discord) or use
  `deliver='local'` and read the output via `cronjob(action='list')` +
  the saved file at `~\AppData\Local\hermes\cron\output\<job_id>\`.
- **Cron agent hits a DIFFERENT model than your live chat** → symptom: cron run
  fails `HTTP 429: weekly usage limit` on Ollama/OpenRouter while your chat works
  fine on Nous free. The cron session inherits the GLOBAL `model.provider`/`model.default`
  (e.g. openrouter→gpt-5.6-luna-pro→Ollama cap), NOT your live runtime's Nous override.
  Fix: set the global default to a free model:
  `hermes config set model.provider nous` + `hermes config set model.default tencent/hy3:free`.
  Then unpinned jobs (model:null/provider:null) inherit it.
- **"fail closed" stale snapshot warning** → after changing the global model,
  `hermes config` warns that N cron jobs stored provider/model snapshots that
  differ and "will fail closed on next run." The `cronjob update` call does NOT
  accept model/provider fields (returns "No updates provided"). PRIMARY fix:
  pin existing jobs via the CLI — `hermes cron edit <job_id> --provider <p>
  --model <m>`. FALLBACK only if the CLI edit is unavailable: delete+recreate
  the job with explicit model/provider in the create call (archive output
  first — see `loop-retirement`). Verify by running once and checking the
  error is gone.
- **Non-self-contained prompt** → symptom: cron run fails or does nothing because
  it has no chat context. Fix: write the prompt as if to a stranger with the repo
  paths and commands inline.
- **Cron that recursively schedules cron** → forbidden by the tool. A cron prompt
  must never call `cronjob(action='create')`.
- **Using relative schedule ambiguously** → `30m` = every 30 min forever; for
  one-shot use an ISO timestamp or `repeat=N`.

- **Pinning model/provider on an EXISTING job (proven 2026-08-21)** →
  `cronjob(action='update')` silently ignores model keys ("No updates provided"),
  and changing the global default triggers DRIFT GUARD: jobs with cached
  provider/model snapshots "fail closed". Fix: use the CLI, which CAN pin
  existing jobs: `hermes cron edit <job_id> --provider <p> --model <m>`.
  Also: `hermes cron create` quirk — ALL options must precede the positional
  schedule+prompt args.
- **Cron inherits GLOBAL config, not chat overrides** → symptom: job runs on the
  wrong/expensive model even though your live chat uses another. Cron sessions
  read `model.provider`/`model.default` from global config; per-chat overrides do
  not propagate. Pin per-job via `hermes cron edit` when it must not drift.
- **Token optimization: monitor-mode watchdogs (proven 2026-08-24)** → for jobs
  whose script output is stable when idle (e.g. bus_check.py prints nothing on
  empty inbox), set `monitor_script=<script>` via `cronjob(action='update')`.
  Unchanged script output is hash-suppressed → NO LLM run, zero tokens per idle
  tick. The agent only wakes when the output actually changes. Baseline is
  seeded from current output at update time, so suppression starts immediately
  (`monitor_state.last_output_hash` appears in the job JSON).
- **Token optimization: enabled_toolsets restriction** → `cronjob(action='update',
  job_id=<id>, enabled_toolsets=['file','terminal',...])` caps the tool catalog
  loaded per run, cutting system-prompt/tool-definition tokens on every fire.
  Valid names come from `model_tools.get_available_toolsets()` in the hermes-agent
  package: a2a, bfl, browser, browser-cdp, browser-use, clarify, code_execution,
  computer_use, cronjob, delegation, desktop_ui, discord, discord_admin,
  feishu_doc, feishu_drive, file, homeassistant, image_gen, kanban, memory,
  project, session_search, skills, spotify, terminal, todo, tts, video,
  video_gen, vision, web, x_search. NOTE: check each prompt's actual tool calls
  before restricting; e.g. loop-factory needs `['file','cronjob']`,
  skill-creation-loop needs `['file','terminal','session_search','skills']`.

## VERIFICATION
- After create: `cronjob(action='list')` shows the job `enabled: true` with the
  expected `next_run_at`.
- After a run: result delivered per `deliver`, or retrievable via list + log.
