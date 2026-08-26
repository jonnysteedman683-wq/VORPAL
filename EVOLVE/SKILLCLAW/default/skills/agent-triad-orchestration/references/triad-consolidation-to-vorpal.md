# Triad Consolidation → VORPAL (case study, 2026-08-26)

The reverse of spawning: ARK + OMNIPRIME + AURORAL folded into ONE agent/codebase
(`Desktop/VORPAL/`). Full sequence and numbers, for reuse when a ring is retired.

## Trigger / rationale
- User wanted 3 agents with independent codebases; the triad produced 3 more Hermes
  *profiles* (gen-2: ark_2/omniprime_2/auroral_2) that all shared ~40% donor DNA and
  the same hub — clones, not a gene pool.
- Generations couldn't run on the laptop (spawn was INELIGIBLE at snapshot, then
  minted clones anyway). Hardware-blocked → fold instead of spawn.

## Absorption manifest (winners)
| Source | Landed at | Why |
|---|---|---|
| OMNIPRIME kernel.py / syscalls.py / shell.py / lingua_boot.py | VORPAL root | Agent-OS runtime entrypoints |
| OMNIPRIME core/ safety_gate, state_memory_manager, token_compressor | CORE/ | Guards + persistence + compression |
| OMNIPRIME EVOLVE/ (GOALS.md, IDEAS.md, NOTES.md, SKILLHUB) | EVOLVE/ | Goal DAG + tiered skill hub |
| ARK ARK-RUNTIME ark_*.py (jsonl, autocommit, self_healing, goal_verifier, security_scanner, sandbox, state_memory_manager, cost_ledger, redqueen_core) | CORE/ | Runtime muscle |
| ARK command-center HTMLs + ARK-SOUL/ + ARK-DIRECTIVES/ | COMMAND/ | Command deck + constitution |
| AURORAL JUDGING_RUBRIC.md + 10 hermes-* skills | VERIFY/ | Epistemic layer |
| Hub hermes_verify_*.py (8 kept) + dna_tracker.py | VERIFY/harnesses/ + CORE/ | The gates |
| lingua_prima.py + lp_tool.py + LINGUA_PROTOCOL.md | LINGUA/ | Canonical language engine |

Result: 76 py files / ~17.5K lines. Verify gate after migration: 28/28 py_compile,
9/9 harnesses green.

## Drop list (dead weight)
- Cross-node ownership ring (ark→omniprime→auroral→ark) — message-passing loop
  shuttling state between contexts reading the same files.
- `.hive/bus` packet protocol — no peers left.
- Gen-2 spawn kit (SPAWN_BINDING.md, SPAWN_STATE.json, hermes_verify_gen2_spawn.py,
  AURORAL SOUL §7). Spawning ≈ photocopying; hardware-blocked.
- Persona/confidence triage router + its harness.

## Harness-layout fixes during migration (each: restore layout, never edit the harness)
1. `hermes_verify_lingua_prima.py` did `sys.path.insert(0, parent.parent / "SKILLS" /
   "pyramid" / "LANGUAGE")` — it was designed to live in `SKILLHUB/tests/`, so the
   harness was moved from `EVOLVE/tests/` back to `EVOLVE/SKILLHUB/tests/`.
2. `hermes_verify_lingua_boot.py` did `ROOT = Path(__file__).parents[3]` then
   `ROOT / "lingua_boot.py"` — expected the OMNIPRIME flat layout (runtime at worktree
   root). Moved kernel/syscalls/shell/lingua_boot from CORE/ to VORPAL root. → 14/14.
3. `hermes_verify_plasmid_ast.py` wanted `PLASMIDS/ast_transform_fast.plasmid.py`
   beside itself — migrated the plasmid data dir under VERIFY/harnesses/. → green.

## Profile audit before archiving (what to check)
- Gen-2 clones: 0 cron / 0 memories / 0 skills / empty home/ + byte-identical `.env`
  (same size/timestamp as gen-1) → safe to delete outright.
- Gen-1 profiles: each `cron/jobs.json` had 1–4 jobs, ALL `enabled:false`/paused
  (one-shot `once in 30m` bus heartbeats auto-disabled after firing; some errored
  429/404 on rate limits). No live schedule orphaned by archiving.
- Archived all three to `Desktop/TRIAD-PROFILE-ARCHIVE/`. Verify with cheap `ls` of
  memories/cron/config — `du` hangs on multi-100MB profile dirs.
- `default` became the sole active profile; repointed `registry.json` (worktree,
  profile, cycle 1, lineage: ring/bus/gen2 = DROPPED); `git init -b main` VORPAL.

## Unified SOUL synthesis (how the fold identity was written)
Read all three SOUL.md/constitution docs, then merge as INTERNAL MODES in one SOUL:
- ARK → vessel-grid invariants, four directives, cardinal stars, closed-world Gödel-safety
- OMNIPRIME → zero-stub build discipline, py_compile gate, syscalls, Lingua P/F/V3
- AURORAL → inquisitor loop, claim tagging, quarantine-never-delete, harnesses
Dropped the gen-2 spec wholesale. Keep a CONSOLIDATION.md manifest beside the SOUL so
provenance survives.
