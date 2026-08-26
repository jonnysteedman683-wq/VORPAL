---
name: loop-retirement
description: "Retires a Hermes loop: pause, archive, remove, record."
category: devops
version: 1.0.0
author: OX-ALPHA
license: MIT
created: 2026-08-23
metadata:
  hermes:
    tags: [loop, retirement, teardown, cron, pause, remove, devops]
    related_skills: [loop-reversal, loop-creation, loop-factory-reviewer, hermes-cron-patterns]
---

# Loop Retirement (safe teardown of an autonomous loop)

## When to Use
- Loop completed its mission (terminal state reached)
- Loop is drifting / burning tokens with no value
- Replacing a loop with a better one
- User says stop/kill/retire/remove a recurring job

## ORDER MATTERS: pause → verify quiet → archive → remove → record

1. **Pause first, never straight to remove.**
   `cronjob(action='pause', job_id=<id>)`
   Pausing is reversible and stops new ticks instantly. Removing mid-flight can
   orphan an executing run whose result re-enters chat later with nowhere to go.

2. **Verify quiet.** Check `cronjob(action='list')`: job shows paused/disabled
   and no run in flight. If one is running, wait for it to finish before
   continuing (its delivery may still arrive — that's fine).

3. **Archive the evidence BEFORE removal.**
   - Saved outputs live at `~\AppData\Local\hermes\cron\output\<job_id>\`.
     Copy somewhere durable (repo notes dir, Obsidian vault) if history matters —
     removal may take these with it.
   - Capture final prompt + schedule + skills list from
     `cronjob(action='list')` so it can be recreated later without archaeology.

4. **Remove.** `cronjob(action='remove', job_id=<id>)`.
   - NEVER guess job IDs — always list first and match by name AND id; similar
     names are common (e.g. review vs upgrade cadence).

5. **Handle downstream dependents.** Any job using
   `context_from: [<removed_job>]` loses its input silently. Retire or repoint
   them in the same pass — sweep every remaining loop that consumed this one.

6. **Record the retirement.** One line where project state lives (NOTES.md /
   ledger): `<date> retired '<name>' (<job_id>): reason`. If replaced, note the
   successor's name/id.

7. **Reversal of THIS operation:** a removed job cannot be un-removed — recreate
   from the archived snapshot. That's why step 3 precedes step 4.

## RETIRE vs PAUSE decision
- **Pause** when: drift suspected but fixable, mission may resume, user said
  "stop it for now", you need a quiet window to repair side effects
  (see `loop-reversal`).
- **Remove** when: mission permanently done, superseded, or prompt rotten beyond
  a quick edit. Removal is cheap ONLY after archiving.

## PITFALLS
- **Straight remove on a running tick** → orphaned run delivers into chat after
  teardown. Pause first.
- **Deleting before archiving output** → run history gone; can't audit what the
  loop did (matters for `loop-reversal` cleanups).
- **ID guessing** → removing the wrong job. Always list-and-match.
- **Orphaned context_from consumers** → downstream loops silently no-op days
  later. Sweep for them at retirement time.
- **No retirement record** → next session wonders why a referenced loop is gone;
  one ledger line prevents the archaeology.

## VERIFICATION
- `cronjob(action='list')` no longer shows the job (or shows it disabled if only
  paused).
- Archived snapshot exists (prompt + schedule + last outputs) if history mattered.
- No remaining loop references the retired job id in `context_from`.

## RELATED
- Undo the loop's file/git side effects → `loop-reversal`
- Approve-gate for loops that create loops → `loop-factory-reviewer`
