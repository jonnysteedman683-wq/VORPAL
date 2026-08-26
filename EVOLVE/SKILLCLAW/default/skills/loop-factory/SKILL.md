---
name: loop-factory
description: "Design a loop that proposes/creates other loops safely."
category: devops
version: 1.0.0
author: AURORAL
license: MIT
created: 2026-08-20
metadata:
  hermes:
    tags: [loop, meta, factory, automation, recursion, cron, devops]
    related_skills: [loop-creation, hermes-cron-patterns, skill-creation-loop, loop-factory-reviewer, verify-after-mutation]
---

# Loop Factory (a loop that creates loops)

## When to Use
- User wants "a loop that creates loops", "auto-spawn monitoring loops", or a
  self-extending automation system.
- You need N recurring jobs to appear over time without hand-authoring each one.
- Meta-automation: a watcher that detects a need and stands up a purpose-built loop.

## THE HARD CONSTRAINT (do not violate)
**Hermes cron FORBIDS recursive scheduling.** A cron prompt MUST NOT call
`cronjob(action='create')` — the tool rejects it and it would fork-bomb. So a
"loop that creates loops" cannot just self-spawn cron jobs from inside a cron run.
The correct architecture is one of:

1. **Propose-then-approve (RECOMMENDED for unattended safety).** The factory loop
   DETECTS a need and EMITS a loop spec (name, schedule, self-contained prompt,
   skills, deliver='local') as its report. A human or a separate interactive
   agent reviews and calls `cronjob(action='create')`. The factory never creates
   directly — it authors.
2. **Chained data loops (`context_from`).** Stand up fixed producer/consumer loops
   up front (via `loop-creation`), then let them chain via `context_from:
   [<upstream_job_id>]`. This is "loops feeding loops" without any loop creating
   another — the topology is static, the data flows.
3. **Interactive meta-agent.** Run the factory as a `delegate_task` / interactive
   Hermes session (NOT a cron job) so it CAN call `cronjob(action='create')`
   legitimately — recursion is only banned *inside cron runs*, not in a live
   agent session. Use this when you want true auto-spawn under supervision.

## DESIGN PRINCIPLES (extend loop-creation)
- Every proposed loop must satisfy `loop-creation` DESIGN PRINCIPLES (self-contained
  prompt, idempotent, bounded retry, verify, safe-stop, deliver).
- Cap proposals per run (e.g. ≤2) to avoid loop-spam; quality over volume.
- Each emitted spec must include the EXACT `cronjob(action='create', ...)` call so
  the reviewer just pastes/approves it.
- Dedup: before proposing, check `cronjob(action='list')` + existing skills so you
  don't propose a loop that already exists.
- Pin model/provider explicitly (free Nous: `model=tencent/hy3:free provider=nous`)
  — see `hermes-cron-patterns` CRON MODEL TRAP. Unpinned jobs fail-closed after a
  global config change.
- Use `deliver='local'` for factory output on a desktop session (no gateway target
  for `deliver='all'`); read output at `~\AppData\Local\hermes\cron\output\<id>\`.

## STEP-BY-STEP (factory loop prompt shape)
1. Detect: scan for a recurring need not yet covered by an existing loop
   (`cronjob list` + skills dir). Examples: a new repo appeared, an error pattern
   recurs, a metric crossed a threshold.
2. Author: for each need, write a full loop spec (schedule, self-contained prompt,
   skills, model/provider pin, deliver='local').
3. Emit: report the spec(s) with the literal `cronjob(action='create', ...)` call.
   If none needed, emit `[SILENT]`.
4. NEVER call `cronjob(action='create')` inside the factory run itself.

## PITFALLS
- **Recursive cron creation** → forbidden; a loop calling `cronjob create` is
  rejected and risks fork-bomb. Use propose-then-approve or interactive meta-agent.
- **Loop-spam** → symptom: 20 overlapping loops proposed. Fix: cap ≤2/run, dedup
  against existing loops first.
- **Unpinned model → fail-closed** → after any global `model.*` change, unpinned
  loops error "Skipped to prevent unintended spend". Always pin model/provider.
- **`deliver='all'` no target** → on local/desktop, use `deliver='local'`.
- **Vague spec** → a proposed loop whose prompt assumes chat context will no-op.
  Enforce self-containment (inline paths/commands) before emitting.

## VERIFICATION
- A factory run is correct when it either EMITS a valid, self-contained, pinned,
  deduplicated loop spec (with the literal create call) OR reports `[SILENT]` —
  and it NEVER called `cronjob(action='create')` during the run.
- Confirm via the delivered report / output file; cross-check `cronjob list`
  shows no unexpected new jobs were spawned by the factory itself.
