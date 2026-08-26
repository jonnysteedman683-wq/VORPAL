---
name: verify-after-mutation
description: "Verify resulting state after any mutating command."
category: devops
version: 1.0.0
author: AURORAL
license: MIT
created: 2026-08-20
metadata:
  hermes:
    tags: [verification, mutation, devops, safety, upgrade]
    related_skills: [hermes-upgrade-check, hermes-cron-patterns]
---

# Verify After Mutation

## When to Use
- After ANY command that mutates state (installs, updates, migrations, deletes, deploys, restarts)
- Especially when the tool reported `exit 0` / "success" but you cannot see the actual result
- When a prior step "completed" but downstream behavior suggests it didn't take

## The Core Rule
**Exit code 0 is a claim, not evidence.** A mutating command can succeed at its
scripted steps while silently skipping the step that actually mattered (locked
files, missing permissions, a guard that bailed early). Verify the EFFECT, not the
return code.

## STEP-BY-STEP
1. **Name the predicate that proves success** BEFORE running the mutation.
   - Bad: "ran the upgrade"
   - Good: "after upgrade, `hermes --version` shows v0.20.4 AND `hermes doctor` passes"
2. **Run the mutation.**
3. **Re-read state with a fresh, independent command** (not the tool's own stdout):
   - version/install: `hermes --version`, `git -C <dir> log --oneline -1`
   - file change: `ls -la --time-style=+%H:%M:%S <path>` (check mtime moved)
   - service: `curl -fsS http://localhost:<port>/health` or `hermes doctor`
   - deps: `pip show <pkg>` / `uv pip list | grep <pkg>`
4. **If the predicate fails, the mutation was partial** — do not report success.
   Diagnose why (lock, guard, missing flag) and retry with the corrected path.
5. **Record the verified result** in your response with the command that proved it.

## Worked Example (2026-08-20, Hermes upgrade)
- Ran `hermes update --backup --yes --force`; process exited 0.
- Predicate: version advances past v0.20.0.
- Verification: `hermes --version` → STILL v0.20.0.
- Conclusion: partial upgrade. The venv reinstall was skipped because the
  session held `.pyd` locks; code+launcher updated but deps did not.
- Fix: scheduled off-peak cron with `--force-venv` from a non-holding process.

## PITFALLS
- **Exit 0 = success bias** → symptom: you report "done" and it breaks later.
  Fix: always pair a mutation with a state-read that would catch a no-op.
- **Trusting the tool's own summary** → symptom: "Update complete" banner while
  version is unchanged. Fix: use an independent read.
- **mtime lies on no-op** → `ls -la` mtime didn't move = nothing wrote. Use it as
  a cheap "did this actually touch the file" check.
- **Gateway restart ≠ code applied** → a Hermes gateway can restart (launcher
  refresh) while git HEAD and deps are still old. Check `git log` + version, not
  just "process is up".

## VERIFICATION
- A mutation is verified only when its success predicate (step 1) is TRUE via an
  independent read. If you cannot state the predicate, you have not verified.

## RELATED
- Loop lifecycle skills this backbone serves: `loop-creation` (verify step),
  `loop-reversal` (reversal predicate), `loop-retirement` (teardown predicate),
  `loop-factory-reviewer` (post-create smoke run).
