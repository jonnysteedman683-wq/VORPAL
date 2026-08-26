---
name: loop-creation
description: "Stand up recurring Hermes loops (cron + verify + safe-stop)."
category: devops
version: 1.0.0
author: AURORAL
license: MIT
created: 2026-08-20
metadata:
  hermes:
    tags: [loop, cron, automation, self-improvement, recurring, devops]
    related_skills: [hermes-cron-patterns, verify-after-mutation]
---

# Loop Creation (recurring autonomous Hermes loops)

## When to Use
- User wants a task to repeat on a cadence (upgrade, optimize, review, digest, monitor)
- Standing up a 24/7 autonomous refinement/optimization loop
- Chaining a data-collect loop into a processing loop
- Designing a loop that must be safe to leave running unattended

NOTE: For raw cron authoring syntax/flags, see `hermes-cron-patterns`. This skill
is the DESIGN layer — what makes a loop correct, safe, and self-aware.

## DESIGN PRINCIPLES (apply before writing the prompt)

1. **Self-contained prompt.** The loop fires in a FRESH session with zero chat
   context. Inline every path, command, model/provider, and success predicate.
   A loop that assumes "you remember last time" will silently no-op.

2. **Idempotency.** Re-running must not double-apply or corrupt state.
   - Use git idempotent ops; prefer `git pull --ff-only` over `git merge`.
   - Guard with a state file / last-run marker so a re-fire skips if already done.
   - Upgrades: `hermes update` is idempotent; a raw `git reset --hard` is not.

3. **Bounded retry.** One retry on failure, then REPORT and STOP. Never an
   unbounded retry loop (the loop itself is the cadence — don't nest another).

4. **Verify inside the loop.** End the prompt with a verification step that reads
   real state, not the tool's stdout. See `verify-after-mutation`. If the
   predicate fails, the loop should say so in its delivery — not claim success.

5. **Safe-stop / auto-pause.** A loop that completes its mission should pause
   itself (`cronjob(action='pause')`) or flip a flag. Loops that run forever
   "just in case" burn tokens and risk drift. Prefer `repeat=N` for one-shot-ish
   jobs or a clear terminal condition.

6. **Deliver the result.** Set `deliver` so the loop's finding reaches you:
   `deliver='local'` on desktop/local sessions (read output at
   `~\AppData\Local\hermes\cron\output\<job_id>\`) — `deliver='all'` resolves to
   nothing there; use it only with a gateway-connected platform (see
   `hermes-cron-patterns`). A loop with no delivery is a black hole.

7. **Never recursively schedule.** A loop prompt MUST NOT call
   `cronjob(action='create')`. The tool forbids it and it would fork-bomb.

## CHAINING LOOPS
Use `context_from: [<upstream_job_id>]` so job B receives job A's latest output
as context. Pattern:
- Job A (collector, `every 30m`): gathers data, writes a stable-shape summary.
- Job B (processor, `every 1h`, `context_from=[A]`): consumes A's output, acts.
Both must emit STABLE output (no timestamps/random ordering) or every tick looks
"changed" and wastes a run.

## STEP-BY-STEP (creation)
1. Define the loop's single job + success predicate (from DESIGN principles).
2. Write the self-contained prompt (commands + verify + report + safe-stop).
3. `cronjob(action='create', name=<id>, schedule=<expr>, prompt=<...>,
   skills=[...], deliver='all')`.
4. `cronjob(action='run', job_id=<id>)` once to smoke-test immediately (result
   re-enters as a new message — do not poll).
5. Inspect the test run's output; if it no-ops or errors, fix the prompt and re-run.
6. Leave it scheduled; set `repeat=N` or a pause condition if it has an end state.

## REAL AEGIS EXAMPLES (from user's setup)
- `continuous-upgrade-refinement` — `every 30m`, runs upgrade/refinement passes.
- `hermes-review-ag-cadence` — `every 30m`, review cadence.
- `hermes-offpeak-upgrade` (this session) — `0 3 * * *`, `hermes update
  --force-venv --yes --backup` from a fresh process to dodge venv `.pyd` locks.

All enforce a safety gate: `npm test` + `tsc --noEmit` + zero forbidden patterns
before any merge/apply.

## END OF LIFE
When a loop finishes its mission or drifts: self-pause per principle 5, then
hand off to `loop-retirement` (pause → archive → remove → record) for teardown,
or `loop-reversal` first if its side effects must be undone.

## PITFALLS
- **No delivery** → symptom: loop ran for days, you never saw output.
  Fix: set `deliver` per your session type at creation (`hermes-cron-patterns`
  deliver gotcha).
- **Non-idempotent step** → symptom: re-fire duplicates commits / corrupts state.
  Fix: guard with state marker; prefer ff-only pulls.
- **Recursive scheduling** → forbidden; a loop must never create cron jobs.
- **Unbounded inner retry** → symptom: a stuck step hammers the API every tick.
  Fix: one retry, then report+stop.
- **Prompt assumes context** → symptom: loop fails because it references "the
  repo we discussed". Fix: inline absolute paths and commands.
- **Lock-holding** → if the loop needs exclusive file access (e.g. venv update),
  run it off-peak from a fresh process (cron is already fresh) — see
  `hermes-cron-patterns` off-peak trick.

## VERIFICATION
- Smoke test via `cronjob(action='run')` returns a result that proves the
  predicate (e.g. "version now v0.20.4" / "0 findings, paused").
- `cronjob(action='list')` shows the loop `enabled: true` with sane `next_run_at`.
- A correctly designed loop leaves a trail: its delivery states what it did AND
  whether the verify step passed.
