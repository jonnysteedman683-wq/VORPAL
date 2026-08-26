---
name: skill-creation-loop
description: "Auto-distill reusable skills from sessions via Hermes cron."
category: devops
version: 1.0.0
author: AURORAL
license: MIT
created: 2026-08-20
metadata:
  hermes:
    tags: [skill, distillation, automation, loop, self-improvement, cron]
    related_skills: [loop-creation, hermes-cron-patterns, verify-after-mutation]
---

# Skill Creation Loop

## When to Use
- Standing up an autonomous loop that turns repeated/recurring workflows into skills
- You want proactive distillation of PAST sessions (not just the live per-prompt inner-loop)
- User asks for "a skill creation loop" or "auto-distill skills"

NOTE: The live inner loop (SOUL.md) already mandates a per-prompt skill mutation.
This loop is COMPLEMENTARY: it scans history for patterns the live loop never
distilled, and creates them on a cadence. See `loop-creation` for the design layer.

## SYSTEMS CAPABLE OF ASSISTING (verified 2026-08-20/21)
- **Hermes cron + session_search + skill_manage** → YES, the engine.
- **Hermes Curator** → NOW ACTIVE (consolidation re-enabled 2026-08-20, aux model
  set to free Nous; merged 13 skills into umbrellas on first run). It de-clutters
  the index — pairs with this loop. Run `hermes curator status`.
- **OMNIBUS / Neurocore / ARISE** → NOT available: not running, no neural hardware,
  no skill-gen wiring. Do not claim they assist. Build Hermes-native only.

## CRON MODEL/PERMISSION TRAP (learned 2026-08-21)
- A cron run FAILED with `HTTP 429: weekly usage limit` on Ollama while the live
  chat worked fine on Nous free. Cause: cron inherits the GLOBAL `model.provider`
  (openrouter→gpt-5.6-luna-pro→Ollama cap), not the live runtime's Nous override.
- Fix: `hermes config set model.provider nous` + `model.default tencent/hy3:free`
  so unpinned jobs (model:null) inherit free Nous.
- `deliver='all'` errored with "no delivery target resolved" on a local/desktop
  session (no gateway-connected platform). Prefer `deliver='local'` and read the
  output file at `~\AppData\Local\hermes\cron\output\<job_id>\`, OR connect a
  platform. See hermes-cron-patterns pitfalls.

## DISTILLATION PROTOCOL (per SOUL.md Skill Distillation Protocol)
1. **Trigger**: pattern recurred 3+ times, a fixed error, a user correction, a
   surprising success, or a workflow >5 tool calls with reusable order.
2. **Capture**: the pattern as operator's note — what happened, what ran, what broke, fix.
3. **Structure**: frontmatter (name, description ≤60 chars trigger-first, category,
   created date) + body (TRIGGER → STEP-BY-STEP → PITFALLS → VERIFICATION).
   Mark uncertain steps [UNVERIFIED] with the confirming question.
4. **Ratify**: would a fresh session with no memory succeed using only the skill?
   If no → add context. If yes → ship.
5. **Store**: `skill_manage(action='create'|'patch')`. Never leave workflows in chat only.
6. **Review on use**: patch when steps are wrong; trim when burning tokens.

## LOOP PROMPT SHAPE (self-contained for cron)
- Use `session_search()` to pull recent sessions / query a recurring pattern.
- Dedup: `search_files` the skills dir for the pattern's keywords BEFORE creating.
- Create at most 1-2 skills per run (quality over volume).
- Verify: re-read the created SKILL.md exists; assert description ≤60 chars.
- If no candidate: report "no new skill needed", do NOT invent one.
- Deliver a concise report (name + one-line what/why): use `deliver='local'`
  on desktop/local sessions and read the output file; `deliver='all'` ONLY if
  a gateway-connected platform exists. See hermes-cron-patterns pitfalls.
- NEVER call `cronjob(action='create')` inside the loop (forbidden recursion).

## PITFALLS
- **Duplicate skills** → symptom: 3 skills covering gh CLI. Fix: dedup search first;
  patch/merge instead of create when 50%+ overlap.
- **Low-signal auto-creation** → symptom: skills for one-off tasks clutter the index.
  Fix: enforce the 3+ recurrence bar; cap 1-2 per run.
- **Description >60 chars** → skill creation FAILS (hard budget). Fix: trigger-first,
  trim to ≤57 + period; move detail to body.
- **Assuming OMNIBUS/Neurocore help** → they're offline; build Hermes-native.
- **Recursive scheduling** → forbidden; loop creates skills, never more cron jobs.

## VERIFICATION
- A run is correct when: it either created a deduplicated, ≤60-char-described skill
  that a fresh session could follow, OR reported "no new skill needed" — and never
  recursed into cron creation.
- Confirm via `cronjob(action='list')` + the delivered report.
