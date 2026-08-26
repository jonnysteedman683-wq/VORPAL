# CONSOLIDATION.md — Migration Manifest
`[◈VORPAL◈]` — generated 2026-08-26, consolidated from the triad codebases.

## 1. What was absorbed (winners)

| Source | Module / artifact | Landed at | Why it won |
|---|---|---|---|
| OMNIPRIME | `kernel.py`, `syscalls.py`, `shell.py`, `lingua_boot.py` | `CORE/` | Agent OS runtime layer |
| OMNIPRIME/core | `safety_gate.py`, `state_memory_manager.py`, `token_compressor.py` | `CORE/` | Execution guardrails + persistence + compression |
| OMNIPRIME EVOLVE | `GOALS/GOALS.md`, `IDEAS.md`, `NOTES.md` | `EVOLVE/` | The DAG — 25+ goals, all green |
| OMNIPRIME EVOLVE | `SKILLHUB/` (cost_ledger, DIRECTORY_PATHS, SKILLS pyramid) | `EVOLVE/SKILLHUB/` | Tiered skill architecture + lingua_prima |
| OMNIPRIME EVOLVE/tests | `hermes_verify_lingua_boot.py`, `hermes_verify_lingua_prima.py` | `EVOLVE/tests/` | Lingua engine gates |
| OMNIPRIME | `registry.json`, `dna_manifest.json` | `./` | Inventory + lineage |
| ARK RUNTIME | `ark_jsonl`, `ark_autocommit`, `ark_self_healing`, `ark_goal_verifier`, `ark_security_scanner`, `ark_sandbox`, `ark_state_memory_manager`, `ark_cost_ledger`, `ark_redqueen_core` | `CORE/` | Proven runtime muscle (red-queen critic, sandbox, autocommit) |
| ARK | `ark-command-center.html`, `ark-nexus.html`, `dashboard.html`, `index.html` | `COMMAND/` | Command deck / UI layer |
| ARK | `ARK-SOUL/`, `ARK-DIRECTIVES/` | `COMMAND/` | Identity + the four laws |
| AURORAL | `JUDGING_RUBRIC.md`, `skills/hermes-*` (10 skills) | `VERIFY/` | Epistemic layer — bug-hunter, verification-harness, file-lock-patterns, etc. |
| Hub | `hermes_verify_*` harnesses (8 kept) | `VERIFY/harnesses/` | The actual gates (cortex_bridge, hive_bridge, obsidian_sync, plasmid_ast, self_improvement, token_* ) |
| Hub | `dna_tracker.py` | `CORE/` | Lineage ledger engine |
| Hub | `lp_tool.py`, `LINGUA_PROTOCOL.md` | `LINGUA/` | Lingua Prima canonical engine + protocol |

## 2. What died in the absorption (deliberately dropped)

| Dropped | Why |
|---|---|
| Gen-2 spawn kit (`SPAWN_BINDING.md`, `SPAWN_STATE.json`, `hermes_verify_gen2_spawn.py`, AURORAL SOUL §7) | Spawning clones ≈ photocopying; hardware-blocked; spawn was INELIGIBLE at snapshot |
| Ownership ring + `.hive/bus` packet protocol | Message-passing between profiles reading the same files — pure token burn |
| Persona/confidence triage router (`persona_router.py`, `hermes_verify_persona_router.py`) | Multi-profile routing obsolete in single-agent mode |
| `manta_router.py`, `hive_gate.py`, `hive_bridge.py` (hub) | Peer-network / hive coordination — no peers anymore |
| OMNIPRIME tiers `tier_0_apex`…`tier_3_archived` (folders) | Consolidation merges tiers into EVOLVE/SKILLHUB; archived material kept in source tree, not duplicated |
| AURORAL `looper/`, `run_auroral.py`, `bus_adapter.py` | Peer-loop machinery; Inquisitor Gate is now an internal mode (SOUL §6) |

## 3. Provenance notes

- Files carrying `[◈OMNIPRIME-FORGE◈]` / `[◈ARK◈]` / `[◈AURORAL-SCAFFOLD◈]`
  watermarks retain them as lineage marks. New scaffolds use `[◈VORPAL◈]`.
- The original codebases are NOT deleted. ARK / OMNIPRIME / AURORAL remain on
  the Desktop as frozen reference. VORPAL is the living tree.

## 4. Known follow-ups

- [x] Full harness suite from `VERIFY/harnesses/` — **2/2 live PASS** (plasmid_ast + worker; 6 orphaned harnesses whose modules were dropped during consolidation quarantined to `EVOLVE/SKILLHUB/skill_repair/harnesses/` 2026-08-26).
- [ ] Point `registry.json` at VORPAL paths (currently references OMNIPRIME worktree)
- [ ] Rewrite GOALS.md phase headers to drop Lingua task-code ownership notation
- [ ] Decide profile strategy: drive VORPAL from `default` profile, archive gen-1 profiles
- [ ] `git init` VORPAL for provenance (SOUL invariant #3)
