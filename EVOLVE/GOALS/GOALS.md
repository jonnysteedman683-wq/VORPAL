# OMNICORE STRATEGIC ARCHITECTURE (DAG)

## Lingua Task Codes (a->b->t form)
Per CYCLE_4_LINGUA_EMBED_OM (packet 0d2a20888508). Each goal title carries a
triad-native Lingua task code `a->b->t`: `a`=phase, `b`=goal index, `t`=tier status
(1=apex,2=active,3=stagnant,4=archived,0=complete/proposal). Syscalls return
Lingua status P|F|V3 (see syscalls.py `LinguaStatus`).


## PHASE 1: CORE INFRASTRUCTURE (Foundations)
- [x] **[a1->b1->t0] GOAL_1.1:** Triad State Memory Abstraction
  - [STATUS: tier_1_active] (Skill: `state_memory_manager`)
  - [IMPLEMENTED: state_memory_manager]
- [x] **[a1->b2->t2] GOAL_1.2:** External LLM/API Handshake Protocol
  - [STATUS: tier_0_apex] (Skill: `provider_handshake`)

## PHASE 2: EVOLUTION INFRASTRUCTURE (EVOLVE layer)
- [x] **[a2->b1->t1] GOAL_2.1:** Initialize Evolutionary Workspace
  - [STATUS: COMPLETE] (Folder: `./EVOLVE/{GOALS,SKILLHUB,TESTS}`)
- [x] **[a2->b2->t0] GOAL_2.2:** Populate EVOLVE/GOALS.md
  - [STATUS: tier_0_apex] (Location: `./EVOLVE/GOALS/GOALS.md`)
- [x] **[a2->b3->t1] GOAL_2.3:** Digital Pyramid File Structure
  - [STATUS: tier_0_apex] (Location: `./EVOLVE/SKILLHUB/SKILLS/pyramid/`)
  - [IMPLEMENTED: pyramid_walker]
- [x] **[a2->b4->t1] GOAL_2.4:** Directory Paths & PATHLEX Language
  - [STATUS: COMPLETE] (Location: `./EVOLVE/SKILLHUB/DIRECTORY_PATHS/`)

## PHASE 3: RESILIENCE PATTERN ENGINE (Patterns from AEGIS/Hermes)
- [x] **[a3->b1->t0] GOAL_3.1:** Circuit Breaker Subsystem
  - [STATUS: tier_0_apex] (Skill: `circuit_breaker`)
  - [IMPLEMENTED: circuit_breaker]
- [x] **[a3->b2->t1] GOAL_3.2:** Health Watchdog Monitor
  - [STATUS: tier_1_active] (Skill: `health_watchdog`)
  - [IMPLEMENTED: health_watchdog]
  - [UNLOCKS: GOAL_6.1 - HIVE Integration Bridge now unblocked
- [x] **[a3->b3->t1] GOAL_3.3:** Pattern Library Documentation
  - [STATUS: COMPLETE] (Location: `./EVOLVE/SKILLHUB/DIRECTORY_PATHS/PATTERN_LIBRARY.md`)
- [x] **[a3->b4->t0] GOAL_3.4:** Auto Debugger (Self-Correction Compiler)
  - [STATUS: tier_0_apex] (Skill: `auto_debugger`)
  - [IMPLEMENTED: auto_debugger]
- [x] **[a3->b5->t1] GOAL_3.5:** Self-Healing Orchestrator
  - [STATUS: tier_0_apex] (Skill: `self_healing_orchestrator`)
  - [IMPLEMENTED: self_healing_orchestrator]

## PHASE 4: SKILL ENGINE & LOOP CREATION
- [x] **[a4->b1->t1] GOAL_4.1:** Auto Loop Creation Engine
  - [STATUS: tier_0_apex] (Skill: `loop_creator`)
  - [IMPLEMENTED: loop_creator]
- [x] **[a4->b2->t1] GOAL_4.2:** Adaptive Model Selector (Stolen Patterns)
  - [STATUS: tier_1_active] (Skill: `adaptive_model_selector`)
  - [STOLEN FROM: cost_router.ts + dispatcher.ts — semantic routing + stream selection]

## PHASE 5: STRATEGIC INFRASTRUCTURE (Hacked from Databases)
- [x] **[a5->b1->t2] GOAL_5.1:** Persistent State Engine (SQLite FTS5)
  - [STATUS: tier_0_apex] (Skill: `persistent_state_store`)
  - [IMPLEMENTED: persistent_state_store]
  - [STOLEN FROM: markus_db.py - SQLite L3 cortex with FTS5 indexing]
- [x] **[a5->b2->t1] GOAL_5.2:** Idea Engine (Dual-Dice + Personality)
  - [STATUS: tier_0_apex] (Skill: `idea_engine`)
  - [IMPLEMENTED: idea_engine]
  - [STOLEN FROM: SOUL.md + tri_agentic_kernel.ts - personality traits + watermark rules]
- [x] **[a5->b3->t1] GOAL_5.3:** Skills Engine (Loadable Framework)
  - [STATUS: tier_1_active] (Skill: `skills_engine`)
  - [IMPLEMENTED: skills_engine]
  - STOLEN FROM: Hermes SKILL.md schema + Hermes Tool Format
  - v1.0: discovers 7/7 real pyramid SKILL.md files, validates 7/7 clean, Hermes-style list/view render
- [x] **[a5->b4->t0] GOAL_5.4:** PROCEDURE Library
  - [STATUS: COMPLETE] (Location: `./EVOLVE/SKILLHUB/SKILLS/pyramid/PROCEDURE/`)
  - [IMPLEMENTED: procedure_library]
- [x] **[a5->b5->t0] GOAL_5.5:** OMNICORE Language Development
  - [STATUS: tier_0_apex] (Skill: `lingua_prima`)
  - [IMPLEMENTED: lingua_prima]
  - [STOLEN FROM: PATHLEX + ARISE signal ripples + SOUL.md + neurocore feature mapping]
  - v4.1: 205 tokens + 115 Unicode symbols + 29 compounds + 10 macros + 17 signals = 359 concepts
- [x] **[a5->b6->t1] GOAL_5.6:** Harvested Patterns Database
  - [STATUS: COMPLETE] (Location: `./EVOLVE/SKILLHUB/SKILLS/pyramid/PROCEDURE/protocols/harvested_patterns_database.md`)
  - [STOLEN FROM: 10 OMNICORE/OMNIBUS databases across A1/A2/A3 layers]
- [x] **[a5->b7->t0] GOAL_5.7:** Auto-Steal Engine (24/7 Pattern Harvesting)
  - [STATUS: tier_0_apex] (Skill: `auto_steal_engine`)
  - [IMPLEMENTED: auto_steal_engine]
  - [STOLEN FROM: markus_router.py + markus_ast_cache.py + idea_engine.py]
  - v1.2: 124x loop speedup, 359 concepts, dual-persistence with Obsidian
  - [STOLEN FROM: markus_obsidian_sync.py — SQLite L3 → markdown tables]

- [x] **[a5->b8->t1] GOAL_5.8:** Security Hardening — Thors/Thorns Retaliation Engine
  - [STATUS: tier_0_apex] (Skill: `thors_thorns_engine`)
  - [IMPLEMENTED: thors_thorns_engine]
  - 12 attack types, 5 countermeasure types, audit logging

- [x] **[a5->b9->t1] GOAL_5.9:** Defensive Engine — Bug Traceback Capture
  - [STATUS: tier_0_apex] (Skill: `defensive_engine`)
  - [IMPLEMENTED: defensive_engine]
  - Bug traceback capture, retry-with-backoff, error taxonomy (ERR_*)

- [x] **[a5->b10->t1] GOAL_5.10:** Tri-Agentic Kernel — Python Port
  - [STATUS: tier_0_apex] (Skill: `tri_agentic_kernel`)
  - [IMPLEMENTED: tri_agentic_kernel]
  - Full A1/A2/A3/Tri-brain architecture ported from TypeScript

- [x] **[a5->b11->t1] GOAL_5.11:** Pipeline Skills — Full Co-Evolution Pipeline
  - [STATUS: tier_0_apex] (Skill: `pipeline_skills`)
  - [IMPLEMENTED: pipeline_skills]
  - Full pipeline: scan → evaluate → route → harvest → execute → audit
  - 5 pipeline skills: process_intent, security_audit, code_review, tri_agent_debate, defensive_execute
  - 12 tests passing, 111 individual assertions

- [x] **[a5->b12->t1] GOAL_5.12:** Code Harvest Phase 1
  - [STATUS: tier_0_apex]
  - 12 TypeScript files stolen + ported from OMNICORE-A1
  - 84 tests passing across 12 test suites

- [x] **[a5->b13->t1] GOAL_5.13:** Prompt Randomizer Engine (Bilingual + Dice)
  - [STATUS: tier_0_apex] (Skill: `prompt_randomizer`)
  - [IMPLEMENTED: prompt_randomizer]
  - Ingested English + Lingua Prima encoded concepts, integrated with auto-dice roller
  - 6 dice categories (upgrade UI/backend/AI, find missing, tech alt, reroll)
  - 12 tests passing, 111 individual assertions

- [x] **[a5->b14->t1] GOAL_5.14:** Thors/Thorns Security Engine Upgrade
  - [STATUS: tier_0_apex] (Skill: `thors_thorns_engine`)
  - [IMPLEMENTED: thors_thorns_engine]
  - Upgraded v1.0 → v1.1: 5 additional attack types (XSS, SQLi, CmdInj, XXE, OpenRedirect, CSRF, InfoDisc)
  - NEW: Honeypot traps, IP reputation with decay, base64 payload scanning, whitelist, metrics dashboard
  - 22 tests (10 new), all passing

## PHASE 6: FUTURE EXPANSION
- [x] **[a6->b1->t1] GOAL_6.1:** HIVE Integration Bridge
  - [STATUS: tier_1_active] (Skill: `hive_integration_bridge`)
  - [IMPLEMENTED: hive_integration_bridge]
  - STOLEN FROM: hive_swarm_adapter.ts + p2p_state_registry.ts + tri_agentic_kernel.ts
- [x] **[a6->b2->t1] GOAL_6.2:** ARISE Swarm Integration
  - [STATUS: tier_1_active] (Skill: `arise_swarm_integration`)
  - [IMPLEMENTED: arise_swarm_integration]
  - STOLEN FROM: ARISE brain + hive_integration_bridge.py + p2p_state_registry.py + event_bus.py
  - v1.0: reproduction-as-primary-goal, cold-start T2 gate, throttled collection, generation fold cap (12)
- [x] **[a6->b3->t1] GOAL_6.3:** EVENT BUS Enhancement (Typed Emission)
  - [STATUS: tier_1_active] (Skill: `event_bus`)
  - [IMPLEMENTED: event_bus]
  - STOLEN FROM: event_bus.ts - typed event dispatch with error isolation
- [x] **[a6->b4->t1] GOAL_6.4:** P2P State Registry (Decentralized Sync)
  - [STATUS: tier_1_active] (Skill: `p2p_state_registry`)
  - [IMPLEMENTED: p2p_state_registry]
  - STOLEN FROM: p2p_state_registry.ts - weighted consensus, reputation scoring
- [x] **[a6->b5->t0] GOAL_6.5:** Harness-Integrity Gate (Anti-Drift Verification)
  - [STATUS: tier_0_apex] (Skill: `verify_all`)
  - [IMPLEMENTED: verify_all]
  - OWNED BY: auroral (triad cross-ownership, ENDGOAL.md §2)
  - v1.0: `scripts/verify_all.py` runs all `hermes_verify_*.py` and FAILS any
    harness that returns exit 0 with EMPTY stdout — catches false-green no-op
    harnesses (the D4-class rot found in the 2026-08-23 audit: 1 silent no-op
    + 8 broken gates, now 15/15 green). Exit code 0/1 → cron/CI ready.

- [x] **[a6->b6->t1] GOAL_6.6:** Generational Fold Gates (3→6→9/12 → fold → 3)
  - [STATUS: tier_1_active] (Skill: `fold_gate_monitor`)
  - [IMPLEMENTED: fold_gate_monitor]
  - Reference: `agent-triad-orchestration/references/generational-fold-plan.md`
  - Dual trigger: G1 headcount ≥9 (cap 12) AND G2 maturity — whichever SECOND:
    - **GATE_G1_HEADCOUNT**: live agent roster count ≥9
    - **GATE_G2_CLEAN_CYCLES**: ≥10 clean gate cycles this generation,
      zero open degradations (grade ledger)
    - **GATE_G2B_DIALECT**: dialect ledger clean, no unmerged tokens pending
      M4 audit
    - **GATE_G2C_CHILDREN**: every spawned triad's next instance passed
      cold-start drill OR archived-with-lessons
  - On all gates green → CONVERGENCE_FOLD protocol: freeze → distill all
    retiring profiles → merge canon (codebases→skills→dialect→Hermes config)
    → re-baseline (verdict-free first cycle) → boot gen N+1 at 3 agents
    with HUMAN_GATE mandatory at the boundary.
  - Hive-mind tiers wired alongside: T1 per-triad shared memory from boot;
    T2 universal hive write-access ONLY after a triad reproduces a passing
    child (reproduction before communion).
  - v1.0 `fold_gate_monitor.py` evaluates all 4 gates, reads HIVE roster +
    ARISE population feeds, triggers CONVERGENCE_FOLD, enforces HUMAN_GATE.
    Verified 14/14 harness + full-stack integration (fold_ready=True).
  - [BLOCKED BY: GOAL_6.1] → **RESOLVED** (HIVE bridge provides the roster feed)

<!--

  Schema Notes:
  - Update [STATUS] on promotion/demotion.
  - Append [IMPLEMENTED: skill_id] when a goal is committed to SKILLHUB/.
  - Maintain strict dependency ordering via [BLOCKED BY].
-->
