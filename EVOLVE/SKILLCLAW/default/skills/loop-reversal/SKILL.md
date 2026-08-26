---
name: loop-reversal
description: "Reverses a loop's side effects: inventory, rollback, verify."
category: devops
version: 1.0.0
author: OX-ALPHA
license: MIT
created: 2026-08-23
metadata:
  hermes:
    tags: [loop, rollback, undo, reversal, cron, automation, devops]
    related_skills: [loop-retirement, loop-creation, verify-after-mutation, systematic-debugging]
---

# Loop Reversal (undoing what an autonomous loop did)

## When to Use
- A loop ran bad passes and mutated files/commits/config that must be undone
- User says revert/roll back/reverse a loop's work
- A loop drifted and you need the pre-loop state back

NOTE: retiring the loop itself (pause/remove) is `loop-retirement`. This skill
reverses the loop's SIDE EFFECTS while the loop may still exist.

## STEP-BY-STEP

0. **If drift is ACTIVE, pause FIRST.** A running loop mutates state while you
   inventory it, and can re-apply after your rollback. Pause, wait for any
   in-flight tick to finish, THEN inventory. (Exception: if the loop is already
   paused/retired or its next tick is far off, inventory first — but never
   reverse mid-run either way.)
1. **Inventory the effects.** You cannot reverse what you haven't listed.
   - `cronjob(action='list')` + read the job's saved output at
     `~\AppData\Local\hermes\cron\output\<job_id>\` for run history.
   - In each affected repo: `git log --oneline --since="<loop start>"`,
     `git status`, check for new branches/tags/files.
   - Classify each effect: git commit / working-tree change / config change /
     external side effect (pushed branch, sent message, API call).

2. **Order of reversal = reverse of application.** Undo newest first, oldest
   last, so intermediate states stay coherent.

3. **Git-backed effects (the easy case):**
   - Loop committed to a dedicated branch → delete/reset the branch; main untouched.
   - Loop committed to shared branch → prefer `git revert <sha>` (forward-out,
     history preserved) over `reset --hard` unless never pushed.
   - Working-tree-only changes → `git restore <paths>`.
   - Pushed remotely → revert + push; never force-push shared refs.

4. **Non-git effects:**
   - Config (`hermes config set ...`) → set back the prior value; confirm the old
     value from notes/logs before writing.
   - Files written outside repos → restore from backup, or delete if created
     fresh by the loop (check timestamps vs loop start).
   - External side effects (sent messages, opened PRs) → close/retract manually;
     these often CANNOT be fully reversed — report honestly which remain.

5. **Guard against re-contamination.** If the loop was never paused (step 0
   exception), PAUSE it now before finishing — otherwise it will redo the damage
   on its next tick. Fix the prompt, then resume or retire (`loop-retirement`).

6. **Verify reversal.** End-state predicate must read real state: clean
   `git status` where expected, expected file contents, config confirmed by
   reading it back. See `verify-after-mutation`.

## PITFALLS
- **Reversing without inventory** → missed half the effects; cron output logs are
  ground truth for WHAT ran, git log for WHAT changed.
- **`reset --hard` on a shared/pushed branch** → destroys others' work. Default
  to `git revert`.
- **Forgetting to pause the loop** → symptom: reverted state reverts itself at
  next tick. Pause FIRST when drift is active.
- **Reversing mid-run** → in-flight run can re-apply after your rollback. Wait
  for the tick to finish or pause, THEN reverse.
- **Idempotency trap in reverse** → a loop that double-applied needs duplicate
  effects counted before undoing; a naive single revert leaves the second copy.
- **Assuming reversibility** → external side effects (emails, API writes, pushed
  branches others pulled) are best-effort. Say which are irreversible.

## VERIFICATION
- Inventory list has a disposition for EVERY effect (reverted / irreversible / kept).
- `verify-after-mutation` predicate passes on the end state.
- The loop is paused or fixed such that the next tick cannot recreate the damage.

## RELATED
- Retire the loop entirely → `loop-retirement`
- Root-cause why the loop misbehaved → `systematic-debugging`
