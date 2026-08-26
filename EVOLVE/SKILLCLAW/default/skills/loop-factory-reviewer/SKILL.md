---
name: loop-factory-reviewer
description: "Review loop-factory proposals and one-click approve them."
category: devops
version: 1.0.0
author: AURORAL
license: MIT
created: 2026-08-20
metadata:
  hermes:
    tags: [loop, factory, review, approve, automation, meta, devops]
    related_skills: [loop-factory, loop-creation, hermes-cron-patterns, verify-after-mutation]
---

# Loop Factory Reviewer (one-click approval tier)

## WHEN TO USE (trigger)
- `loop-factory` ran and you want to action its proposals.
- User says "review loop proposals" / "approve loops" / "check pending loops".
- You are the LIVE session (or a delegate_task) — the only context allowed to
  call `cronjob(action='create')`. Trigger this skill on that user request.

## PENDING SOURCE
`C:\Users\jonny\AppData\Local\hermes\loop-factory-pending.json`
(JSON array of {name, schedule, prompt, skills, model, provider, deliver}).
Empty array `[]` means the factory found no gaps (nothing to review).

## STEP-BY-STEP (reviewer protocol)
1. **Read** the pending file. If missing or `[]`, report "no pending proposals"
   and stop.
2. **Validate** each spec against `loop-creation` DESIGN PRINCIPLES:
   - prompt self-contained (inline paths/commands, no chat-context assumptions)?
   - model/provider pinned (free Nous: `tencent/hy3:free` / `nous`)?
   - deduped against `cronjob(action='list')` + skills dir?
   - capped (≤2 per factory run)?
   - has a safe-stop / verify step?
   Reject or flag any spec failing these; explain why.
3. **Present** to the user as a numbered list, each with a one-line what/why and
   its schedule. Offer: "approve all", "approve #N", or "reject #N".
4. **On approval** (user clicks / says yes), call
   `cronjob(action='create', name=..., schedule=..., prompt=..., skills=[...],
   deliver='local')` for each approved spec.
   This is allowed because you are an INTERACTIVE agent, not a cron run.
   NOTE: `cronjob create` takes NO model/provider fields — passing them is a
   silent no-op. The job inherits global config; if it must be pinned, run the
   CLI immediately after create: `hermes cron edit <job_id> --provider nous
   --model tencent/hy3:free`, then confirm via one smoke run
   (`verify-after-mutation`).
5. **Clean up**: after processing, write `[]` back to the pending file so the same
   proposals are not re-reviewed next session.

## WHY A SEPARATE INTERACTIVE AGENT (not cron)
- Hermes forbids recursive scheduling: a cron prompt MUST NOT call
  `cronjob(action='create')`. So the factory PROPOSES (writes pending file); the
  reviewer (interactive) APPROVES+CREATES. This splits "generate" from "instantiate"
  and keeps a human/agent click in the loop — no silent loop-spam.

## PITFALLS
- **Trying to create from cron** → rejected + fork-bomb risk. Only the interactive
  reviewer creates.
- **Stale pending file** → symptom: same proposals reappear. Fix: write `[]` after
  processing (step 5).
- **Unpinned model → fail-closed** → always pin `model=tencent/hy3:free
  provider=nous` in the created job (see hermes-cron-patterns CRON MODEL TRAP).
- **Approving a non-self-contained prompt** → the loop will no-op. Enforce
  self-containment during validation (step 2).

## VERIFICATION
- A review cycle is correct when: pending file read, each spec validated, approved
  ones created via `cronjob create` (visible in `cronjob list`), and pending file
  reset to `[]`. Rejecting leaves no new job and resets the file.
