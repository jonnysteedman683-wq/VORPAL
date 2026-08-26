# Gen-2 Triad Spawn Protocol & Operational Runbook
`[◈TRIAD-SPAWN-OPS◈]` Stamped 2026-08-25 | Distilled from live Gen-2 deployment

## 1. Trigger Conditions for Spawning Gen-N+1
Before spawning a child triad ring:
- **Gate Maturity**: Parent node has $\ge 10$ consecutive clean cycles ($\ge 90\%$ pass, 0 degradations).
- **Self-Description Closure**: Combined `SOUL.md` + `LINGUA.md` + bus tools form a standalone bootstrap kit.
- **Dictionary Stability**: Zero `[ERR_LP_UNKNOWN]` token events on the inter-profile packet bus.
- **Ledger Discipline**: Zero `[ERR_STALE]` repeats in notes/ledgers.
- **Human Invariant**: Explicit user confirmation is strictly mandatory at every generation boundary.

## 2. Profile Creation Pitfalls & Naming Conventions
- **Naming Rule**: Profile names must match `[a-z0-9][a-z0-9_-]{0,63}`. Dots are **forbidden** (e.g. `ark.2` fails regex; use `ark_2`, `omniprime_2`, `auroral_2`).
- **Clone Strategy**: Use `hermes profile create <name> --clone-from <source_profile>` to inherit base provider/model configurations.

## 3. Child Triad Artifact Architecture
Create a dedicated generation workspace directory under `TRIAD CO-ORDINATION AND EVOLUTION/gen<N>/`:
1. `SPAWN_BINDING.md`: Encodes cyclic ownership (`ark_2 -> omniprime_2 -> auroral_2 -> ark_2`), language engine path, and memory tiers.
2. `GOALS.md`: Seeded repair tasks harvested from parent degradation scars (EvoAgent-style inherited variation).
3. `SPAWN_STATE.json`: Machine-readable metadata capturing timestamp, generation index, children, and human-gate approval record.

## 4. Verification Gate
Write and run an epistemic verification harness (`hermes_verify_gen<N>_spawn.py`) asserting:
- All child profile names exist in `hermes profile list`.
- All binding and goal artifacts are verified on disk.
- Cyclic ownership ring forms a closed directed loop.
- Human gate is logged as `APPROVED`.

## 5. Dormancy / Staged Activation Lifecycle
- Newly spawned triads remain **dormant** (zero cron/heartbeat dispatch) until deliberate activation.
- When ready to activate, stagger cron schedules across minutes (e.g., ark_2 at :02, omniprime_2 at :07, auroral_2 at :12).
- **Admission Rule**: Child triad must achieve 3 consecutive clean cycles to earn full peer promotion.
