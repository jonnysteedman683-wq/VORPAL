---
name: duo-dice-engine
description: Roll dice to pick HERMES/MARKUS upgrade or skill curation.
version: 2.0.2
author: Jonny Steedman
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [dice-engine, upgrades, markus-os, hermes, vorpal, skill-curation, triad]
    related_skills: [markus-upgrade-start, markus-autonomous-dice-engine, omnicore-skill-curation, verify-after-mutation]
---

# Triad Dice Engine — HERMES + MARKUS + VORPAL

A dice-driven upgrade selector that rolls for the next improvement across **three systems at once**: the **MARKUS OS** ecosystem (`Desktop/MARKUS-OS`, server port 8128), the **HERMES** agent/desktop ecosystem (this skill's own home), and the **VORPAL** agent core (`Desktop/VORPAL` — the consolidated brain). It turns "what should we upgrade next?" into a concrete, logged, rewarded action — and pairs every action with a **skill curation** move so each cycle also mutates the skill library.

The dice only fire on a **50% coin** (anti-thrash throttle). A **6** (or its mirrors **12**, **18**) is the **extra chance**: a **double reroll** — roll 2 more dice for more options.

## When to Use

- Jonny says "roll the dice", "dice engine", "what should we upgrade next", "give me a random upgrade target".
- Any scheduled/loop trigger that needs a stochastic next-action: cron dispatch, `loop-creation` cycle, `markus-upgrade-start` handoff.
- A **duo** cycle — "upgrade HERMES and MARKUS at the same time", "combined enhancement", "split the rolls between both".
- After an upgrade lands: record the reward (`reward` subcommand) so the engine learns.
- Don't use for: a single known bug fix (that's `systematic-debugging`), or a specific named upgrade (just do it).

## Prerequisites

- Python 3.11 (`python`). Script is stdlib-only (no numpy, no network).
- MARKUS OS repo at `Desktop/MARKUS-OS` (engine targets resolved from there).
- Roadmap log defaults to `Desktop/MARKUS-OS/HERMES UPGRADE/DICE_ROADMAP.md` (env `DICE_ROADMAP` to override).
- Reward state at `~/.hermes/dice_engine_state.json` (env `DICE_STATE` to override).

## How to Run

```bash
python scripts/dice_engine.py actions                 # print the 18-slot map
python scripts/dice_engine.py roll                    # 50% coin -> 1d18 single roll (default triad)
python scripts/dice_engine.py roll --mode triad       # combined HERMES+MARKUS+VORPAL cycle (one die each)
python scripts/dice_engine.py roll --mode duo         # combined HERMES+MARKUS cycle
python scripts/dice_engine.py roll --mode trio --vorpal  # + bias lead die toward MARKUS by VORPAL goal pulse
python scripts/dice_engine.py roll --force            # bypass the 50% coin
python scripts/dice_engine.py roll --dry-run --json   # no file writes, machine output
python scripts/dice_engine.py reward 4 0.9            # teach: slot 4 paid off 0.9
python scripts/dice_engine.py stats                   # reward table
python scripts/dice_engine.py verify                  # self-test gate (must PASS)
```

Then **execute the landed action** using its `next` pointer in the Upgrade Paths below, `python -m py_compile` any touched `.py`, and confirm the effect (health check / benchmark / page render) before closing the cycle with `reward <slot> <0.0-1.0>`.

## Upgrade Paths — the 18-slot map (read on trigger)

The full 18-slot upgrade map — every slot's system, action, concrete
target, and execute/verify command — lives in
`references/upgrade-map-and-pitfalls.md`. Load it when you roll and
need to execute the landed action. The roll mechanics (50% coin,
6/12/18 rerolls, reward learning) stay in the mode sections below.

## Duo Mode — both systems at once

`--mode duo` runs a **combined HERMES + MARKUS cycle** in one go:

1. **Lead die** `1d6`: **1–3 = HERMES** leads, **4–6 = MARKUS** leads (order logged).
2. **Duo dice split between the 2**: one action die for HERMES (slot 7–12) and one for MARKUS (slot 1–6) — the pair is split, so **both systems get one action every cycle**.
3. A **6** on either system's die = that system's **double reroll** (2 more of its own slots).

Run it, then execute **both** landed actions (one per system) before closing the cycle.

## Triad Mode — all three systems at once (default)

`--mode triad` runs a **combined HERMES + MARKUS + VORPAL cycle** in one go:

1. **Lead die** picks the lead system (1/3 chance each among HERMES, MARKUS, VORPAL).
2. **One action die per system** — the dice are split, so **all three systems get one action every cycle** (HERMES slot 7–12, MARKUS slot 1–6, VORPAL slot 13–17).
3. A **6** on any system's die = that system's **double reroll** (2 more of its own slots).

This is the default mode. Execute **all** landed actions (one per system) before closing the cycle. `--vorpal` biases the lead die toward MARKUS (the VORPAL-fed side) proportional to VORPAL's open-goal pulse.

## VORPAL Intertwining (`--vorpal`)

- The dice engine is now **bidirectionally wired to VORPAL** (the consolidated agent core at `Desktop/VORPAL`) via `markus_vorpal_bridge.py`:

- **VORPAL → MARKUS**: `vorpal_goal_pulse()` shells out to the bridge and reads VORPAL's open-goal fraction from `EVOLVE/GOALS/GOALS.md`. With `--mode duo --vorpal`, that pulse **nudges the lead die toward MARKUS** (the VORPAL-fed side) proportional to how much open work VORPAL has — so the dice steers toward the project with actual open goals.
- **MARKUS → VORPAL**: `markus_vorpal_bridge.py --snapshot` writes MARKUS's live telemetry (matrix weights, network state, server health) to `VORPAL/EVOLVE/MARKUS_TELEMETRY.json`, so VORPAL's decision layer can see what its body is doing.

The bridge (`hermes_verify_vorpal_bridge.py`, 8/8 PASS) reads GOALS/NOTES/SOUL into a `VORPALStatus` snapshot and writes the telemetry ledger. Fail-open: if VORPAL is absent, pulse = 0.0 and nothing raises.

**The `duo-dice-cycle` cron (dbf7f9a73505, daily 03:00) now rolls with `--mode triad --force --vorpal`** — every scheduled cycle covers all three systems (HERMES + MARKUS + VORPAL), biased by VORPAL's goal pulse. Its prompt includes per-system execution steps (HERMES/MARKUS/VORPAL) and the bridge-snapshot step so MARKUS telemetry flows to VORPAL on each run.

## Skill Curation Procedures (the curation die)

Every executed cycle also rolls a **curation die** (`1d6`) so the skill library evolves with the codebase — the "skill mutation" closeout from the triad doctrine:

| Die | Operation | Procedure (Hermes tools) |
|---|---|---|
| 1 | **CURATE** | `skills_list` → inventory; find stale / `[SKILL_PRUNED]` / duplicate skills; prune or consolidate with `skill_manage(action='delete', absorbed_into=…)`. Completion: index clean, no dead refs. |
| 2 | **ENHANCE** | Patch ONE skill with this cycle's lesson: `skill_manage(action='patch', old_string=…, new_string=…)`; bump `version`. Completion: patch applied, `skill_view` confirms. |
| 3 | **OPTIMISE** | Tune a description/trigger (skill-creator `run_loop`) or merge near-identical skills. Completion: trigger still fires, chars down or unchanged. |
| 4 | SKIP | No curation this cycle. |
| 5 | CURATE + ENHANCE | Run die-1 then die-2 procedures. |
| 6 | **DEEP** | CURATE + ENHANCE + OPTIMISE (the "extra chance" applied to the skill library). |

Always `skill_view(name=…)` before acting on a skill that shows `[SKILL_PRUNED]` (reload rule). Co-locate the new lesson in the skill's Pitfalls — never log-and-forget.

## Procedure

1. `python scripts/dice_engine.py roll [--mode duo] [--force]` — read the landed slot(s) + curation die.
2. Execute each landed action via its table `next` pointer; real file edits, `py_compile` on `.py`, and an observable check (health endpoint / benchmark / render).
3. Perform the curation-die operation with `skill_manage`/`memory` tools.
4. Close the cycle: `python scripts/dice_engine.py reward <slot> <0.0-1.0>` (1.0 = fully green, green harness).
5. Confirm the roadmap entry exists (`read_file` the tail of DICE_ROADMAP.md).

## Pitfalls (read on trigger)

The VERIFIED failure ledger — repo-root drift, RNG re-seeding traps,
matrix weight-formula saturation, telemetry gotchas, plugin/panel
build traps, and every other debugged upgrade — lives in
`references/upgrade-map-and-pitfalls.md`. Load it when a dice-engine
run or landed upgrade misbehaves.

## Verification

- `python scripts/dice_engine.py verify` → must print all PASS and `OVERALL: PASS` (py_compile self, all 12 slots reachable, coin ≈50%, duo always touches both systems, roadmap writable).
- After a real roll, `read_file` the tail of `DICE_ROADMAP.md` — the entry must list slots, targets, curation, and status.
- `python scripts/dice_engine.py stats` — reward table exists and updates after `reward`.
