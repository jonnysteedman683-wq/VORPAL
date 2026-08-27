---
name: hermes-cron-watchdog
description: "Build zero-token no_agent cron watchdog scripts."
version: 1.0.0
author: AURORAL
license: MIT
created: 2026-08-26
metadata:
  hermes:
    tags: [cron, watchdog, no-agent, automation, zero-token, script]
    related_skills: [hermes-cron-patterns, loop-creation, hermes-profile-shellout]
---

# Hermes Cron Watchdogs (zero-token recurring scripts)

## When to Use
- A recurring task runs a deterministic command/script and only matters when it FAILS
- You want a loop that costs ZERO tokens while healthy and alerts on breakage
- Authoring the script side of a `no_agent=True` cron job (the job's prompt/syntax
  layer lives in `hermes-cron-patterns` — read it too)

## The Watchdog Shape (proven 2026-08-26, MARKUS auto-upgrade loop)
A `no_agent=True` cron job runs a script directly and delivers its stdout verbatim.
Make the script the watchdog:

1. **Silent on success** — print NOTHING when the underlying task exits 0.
   `no_agent` cron with empty output delivers nothing → zero tokens, zero noise.
2. **Report on failure** — print a compact report + the audit-log path when the
   task exits non-zero or times out. That text is what gets delivered.
3. **Mirror the exit code** — `sys.exit(proc.returncode)` so the cron records the
   real status, not a masked 0.
4. **Always write an audit log** — dump full stdout+stderr to
   `~/.hermes/cron_log/<name>-<timestamp>.log` on every run (success or not), so
   there's a durable trail even when nothing is delivered.
5. **Use the verified interpreter** — run the task with `sys.executable` (the same
   venv Python the wrapper runs under — deterministic), not a bare `python` that
   could resolve elsewhere. Timeout generously (markus cycle ≈ 25s; use 1200s for
   anything with PHOENIX AST batch scans).

Template: `templates/no_agent_watchdog.py` — copy and adapt.

## Operational Quirks (proven 2026-08-26)
- **CLI and cronjob tool read DIFFERENT job stores.** Jobs created via
  `cronjob(action='create')` are invisible to the CLI: `hermes cron list` says
  "No scheduled jobs" and `hermes cron edit <id>` says "Job not found: <id>"
  for jobs the tool clearly lists. Manage tool-created jobs ONLY via the
  `cronjob` tool (update/run/pause/remove). Do not burn cycles trying to pin
  model/provider on a tool-created job via the CLI.
- **Free-model inheritance beats pinning.** A job created with model:null /
  provider:null inherits the GLOBAL `model.provider` / `model.default`. To run
  a job free: confirm the global default is a free nous model
  (`hermes config get model.provider` / `model.default`, e.g. `nous` +
  `deepseek/deepseek-v4-flash`), then leave the job unpinned. Only pin when the
  job must NOT follow the global default.
- **deliver='all' resolves when the gateway is up.** The create/update response
  carries `gateway_running: true/false`. When true, `deliver='all'` fans output
  out to connected channels. For a watchdog this is ideal: failures reach you,
  successes are silent anyway.
- **MSYS path mangling** — pass native `C:/...` paths to native tools
  (`python C:/path/script.py`), never `/c/...`, or the interpreter says
  "can't open file 'C:\\c\\...'".

## Verification
1. Run the wrapper manually once: expect exit 0, EMPTY stdout, and a new
   `~/.hermes/cron_log/<name>-*.log`.
2. Confirm the underlying task went green inside the log (all stages COMPLETE,
   validation PASS) and the repo working tree is unchanged (idempotency check).
3. Prove the cron wiring with `cronjob(action='run', job_id=<id>)` — the run
   report should show `Mode: no_agent (script)` and `Status: silent (empty output)`.

## Distinguishing "silent skip" from "auth no-op" (proven 2026-08-26, SkillClaw feed)
A silent-unless-notable watchdog that drives a PAID LLM pipeline (SkillClaw
evolve, batch generate) prints nothing both when it cleanly skipped AND when
the LLM auth silently failed — exit 0 and empty stdout are identical for the
two cases, so a healthy-looking silent tick can be burning nothing OR
delivering nothing while you believe it is working.

**Read the pipeline's structured outcome ledger**, not stdout/exit code. For
the SkillClaw feed (`C:/Users/jonny/skillclaw/evolve_history.jsonl`, last
line) the delivery-proving fields are:
- `had_processing_error: false` — the LLM call path completed without error
- `elapsed_seconds` (e.g. 57.6) — a real run took real time
- `sessions` / `no_skill_sessions` — the model actually judged the exports
- `skills_evolved` / `evolutions` — what (if anything) was produced

`no_skill_sessions=N, evolutions=[]` with `had_processing_error=false` is a
legitimate clean skip: auth delivered, the model judged, nothing warranted an
action. That is a PASS — do not treat absence of output as breakage.

Also verify the sync/mirror side-effect independently (ledger counts advanced,
backup mtimes moved, target dir exists) rather than trusting the script's own
"synced" print — a skipped pipeline that claims a sync is the same class of
false-green as an exit-0 that never ran.
