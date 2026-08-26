---
name: duo-dice-engine
description: Roll dice to pick HERMES/MARKUS upgrade or skill curation.
version: 1.0.4
author: Jonny Steedman
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [dice-engine, upgrades, markus-os, hermes, skill-curation, duo]
    related_skills: [markus-upgrade-start, markus-autonomous-dice-engine, omnicore-skill-curation, verify-after-mutation]
---

# Duo Dice Engine — HERMES + MARKUS

A dice-driven upgrade selector that rolls for the next improvement across **two systems at once**: the **MARKUS OS** ecosystem (`Desktop/MARKUS-OS`, server port 8128) and the **HERMES** agent/desktop ecosystem (this skill's own home). It turns "what should we upgrade next?" into a concrete, logged, rewarded action — and pairs every action with a **skill curation** move so each cycle also mutates the skill library.

The dice only fire on a **50% coin** (anti-thrash throttle). A **6** (or its mirror **12**) is the **extra chance**: a **double reroll** — roll 2 more dice for more options.

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
python scripts/dice_engine.py actions                 # print the 12-slot map
python scripts/dice_engine.py roll                    # 50% coin -> 1d12 single roll
python scripts/dice_engine.py roll --mode duo         # combined HERMES+MARKUS cycle
python scripts/dice_engine.py roll --force            # bypass the 50% coin
python scripts/dice_engine.py roll --dry-run --json   # no file writes, machine output
python scripts/dice_engine.py reward 4 0.9            # teach: slot 4 paid off 0.9
python scripts/dice_engine.py stats                   # reward table
python scripts/dice_engine.py verify                  # self-test gate (must PASS)
```

Then **execute the landed action** using its `next` pointer in the Upgrade Paths below, `python -m py_compile` any touched `.py`, and confirm the effect (health check / benchmark / page render) before closing the cycle with `reward <slot> <0.0-1.0>`.

## Upgrade Paths — the 12-slot map

| Slot | System | Action | Concrete target | Execute |
|---|---|---|---|---|
| 1 | MARKUS | Upgrade MARKUS UI | `markus_chat.html`, `markus-os.html`, `the-orb.html`, `memory-palace.html`, `hack-console.html` | Refresh accessibility/contrast/keyboard-nav; smoke-test via `launch_markus_app.py` |
| 2 | MARKUS | Upgrade MARKUS backend | `markus_server.py` (8128), `markus_kernel.py`, `markus_router.py`, `phoenix_*.py` | Refactor + expand API; `py_compile`; restart; `curl localhost:8128/api/health` |
| 3 | MARKUS | Upgrade MARKUS frontend | `electron-main.js`, `electron-preload.js`, `package.json`, `hive-core/` frontend, `markus-os-electron/` | Electron/JS layer work; npm install per `package.json`; electron smoke test |
| 4 | MARKUS | Optimise MARKUS process | `markus_latency_multi_upgrade.py`, `markus_task_dag.py`, `markus_devswarm.py`, `markus_resilience.py`, cron/schtasks | `python markus_benchmark.py`; profile hot paths; tune worker pools/DAG |
| 5 | MARKUS | Research MARKUS paths → roadmap | `markus_web_research.py` | Run research; append findings to `research/evolutionary_loop_roadmap.md` + DICE_ROADMAP |
| 6 | MARKUS | **Double reroll** | engine | Roll 2 more dice → 2 more MARKUS options |
| 7 | HERMES | Upgrade HERMES UI | Hermes desktop: theme tokens, panes, chat surface | Follow `hermes-desktop-plugins` skill; edit theme/panes; build a pane plugin |
| 8 | HERMES | Upgrade HERMES backend | `hermes config` CLI: providers, models, gateway, MCP, cron | Load `hermes-agent` skill; `hermes config set …`; audit MCP (`setup_mcp`); review cron (`cronjob`) |
| 9 | HERMES | Upgrade HERMES frontend | `hermes-desktop-plugins`, preview widgets, `::preview{file=…}` pages | Build/extend a desktop plugin or inline chat widget |
| 10 | HERMES | Optimise HERMES process | tool batching, memory hygiene, skill loading, `adaptive-model-switcher` routing | Batch calls; prune memory via `memory`; audit `skills_list`; run model-latency bench |
| 11 | HERMES | Research HERMES paths → roadmap | hermes docs `https://hermes-agent.nousresearch.com/docs` + `web_search` | Read `hermes-agent` skill + docs; research new capabilities; log to DICE_ROADMAP |
| 12 | HERMES | **Double reroll** | engine | Roll 2 more dice → 2 more HERMES options |

**Mechanics (refined from spec):**
- **50% trigger**: each roll starts with a coin flip; fail = "STAYED" (logged, no action). `--force` bypasses.
- **6 = the extra chance**: rolling 6 (MARKUS) or 12 (HERMES) gives a **double reroll** — 2 extra dice = 2 more options. Sub-rolls never re-trigger (bounded at 2 extra actions per cycle).
- **Reward learning**: mark a landed action's payoff with `reward <slot> <value>`; the engine ε-greedy (ε=0.3) biases toward high-reward slots (same pattern as `markus_dice_engine.py`).

## Duo Mode — both systems at once

`--mode duo` runs a **combined HERMES + MARKUS cycle** in one go:

1. **Lead die** `1d6`: **1–3 = HERMES** leads, **4–6 = MARKUS** leads (order logged).
2. **Duo dice split between the 2**: one action die for HERMES (slot 7–12) and one for MARKUS (slot 1–6) — the pair is split, so **both systems get one action every cycle**.
3. A **6** on either system's die = that system's **double reroll** (2 more of its own slots).

Run it, then execute **both** landed actions (one per system) before closing the cycle.

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

## Pitfalls

- **`markus_web_research.py` is offline (stub web search)**: the live web-search hook is a `pass`; it runs against the pre-indexed `RESEARCH_KNOWLEDGE_BASE`. No network needed — verify with `python markus_web_research.py` printing `Web Research Engine Test: PASSED` (exit 0), then append the topics/findings/effort table to `research/evolutionary_loop_roadmap.md` + `DICE_ROADMAP.md` yourself (the script only prints, it does not write files).
- **adaptive-model-switcher router is selector-only in `recommend` mode**: `dispatch_applied: false` in `state.json`; full MCP integration requires the `mcp` package (not installed → `mcp package is required`). `test_adaptive_router.py` (8/8) and `test_mcp_protocol.py` still pass as the verification gate for slot 10.
- **Repo root drift**: `markus-upgrade-start` claims MARKUS OS lives at `Desktop/New folder`, but the verified root is `Desktop/MARKUS-OS` (85 files, incl. `markus_server.py`). Always resolve targets from `Desktop/MARKUS-OS`.
- **A failed cycle must NOT update rewards** — reward only what you verified (mirrors the existing engine's rule).
- **6/12 sub-rolls are bounded**: a reroll never cascades more than 2 extra actions, so a long run can't explode.
- **Session cache**: the new skill isn't visible to `skill_view` until the next session (loader caches at start).
- **Windows/MSYS**: run via `python` (3.11), never `python3` (which maps to 3.14). Pass native `C:/…` paths to scripts if invoked from git-bash.
- **`random.Random` has no `randbelow`** — that's a `secrets` method. A `(rng or secrets).randbelow(n)` dispatch crashes under a seeded RNG. Use the script's `_rbelow(rng, n)` helper (`rng.randrange(n)` vs `secrets.randbelow(n)`).
- **Never re-seed inside a test loop**: `for _ in range(N): resolve_single(_rng(seed), …)` rebuilds the same seeded RNG every iteration, so every roll is identical and coverage checks fail with a single slot hit. Hoist `rng = _rng(seed)` above the loop.
- **Nested quotes in f-strings**: `f"{'PASS' if x else 'STAYED' (note)}"` is a SyntaxError. Keep the whole alternative inside one quoted literal.
- **[VERIFIED 2026-08-26]** Live run: verify gate 5/5 PASS, coin measured 0.492 over 2000 flips, duo touched both systems in 2000/2000 cycles, slot 6/12 rerolls yielded exactly 2 extra options, roadmap appended at `Desktop/MARKUS-OS/HERMES UPGRADE/DICE_ROADMAP.md`.
- **[VERIFIED 2026-08-26 live roll]** MARKUS slot 3 = real frontend hardening win: `electron-main.js` had `contextIsolation: false` and `electron-preload.js` exposed a raw `window.ipcRenderer = require('electron').ipcRenderer` that no HTML even used. Fix: `contextIsolation: true` + `sandbox: true`, replace the preload with a `contextBridge.exposeInMainWorld` minimal safe API. Verify with `node --check electron-main.js && node --check electron-preload.js` + `python -c "import json;json.load(open('package.json'))"` (no electron launch needed).
- **`grep SKILL_PRUNED` false positives**: the reload-rule prose ("Always `skill_view` before acting on a skill that shows `[SKILL_PRUNED]`") makes `grep -rl SKILL_PRUNED` hit healthy skills. When auditing for pruned skills, exclude matches that are just the reload-rule sentence, or grep the actual frontmatter `status:` field.
- **[VERIFIED 2026-08-26 upgrade]** `markus_adaptive_matrix.py` reliability scoring landed 6/6 harness PASS: sliding-window recency-decayed `reliability_score [0,1]`, 3-consecutive-failure circuit-break (60s open, 0.1x weight suppression), state persisted to `markus_adaptive_state.json`. Two harness gotchas: (1) `consecutive_failures == N` assertions must use `>= N` when a model already accumulated failures earlier in the test (they compound); (2) `importlib` direct-load of a module whose dataclasses reference `cls.__module__` crashes with `AttributeError: 'NoneType' object has no attribute '__dict__'` unless you register `sys.modules[spec.name] = mod` before `exec_module`. Persistence is a feature but test runs pollute the state file — `rm markus_adaptive_state.json` before a clean production start.
- **[VERIFIED 2026-08-26 upgrade]** `markus_web_research.py` research slot now persists real artifacts: `research_and_report()` writes a full-finding report to `research/evolutionary_loop_roadmap.md`, and `research_technical_alternative()` accepts `live_findings=` so the orchestrating agent can feed real `web_search` results through the old `try: pass` stub. Harness `hermes_verify_web_research.py` 6/6 PASS. Two pitfalls found: (1) `write_to_roadmap` must `Path(...)`-coerce `report_path` — passing a `str` crashes with `AttributeError: 'str' object has no attribute 'parent'`; (2) `generate_improvement_proposal` only surfaces top-3 recommendations, so live findings classified into `patterns` were silently dropped from the artifact — persist the FULL `result['findings']` list in `write_to_roadmap`, not just the proposal. The `--report <topic>` CLI mode writes to the real roadmap; the self-test writes to a temp path and asserts read-back.

## Verification

- `python scripts/dice_engine.py verify` → must print all PASS and `OVERALL: PASS` (py_compile self, all 12 slots reachable, coin ≈50%, duo always touches both systems, roadmap writable).
- After a real roll, `read_file` the tail of `DICE_ROADMAP.md` — the entry must list slots, targets, curation, and status.
- `python scripts/dice_engine.py stats` — reward table exists and updates after `reward`.
