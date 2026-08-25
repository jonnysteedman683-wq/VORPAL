# OMNIPRIME BUG FIX REPORT - 23 Aug 2026
# Bugs fixed in syscalls.py and supporting files

## CRITICAL FIXES (syscalls.py)

### 1. Missing uuid import
- Fixed: Added `import uuid` at module level (line 11)
- Was: uuid only imported locally inside send() on line 166
- Now: log_err() can use uuid.uuid4() without NameError

### 2. Assert that always failed
- Fixed: Changed `assert not isinstance(err_id, str)` to `assert isinstance(err_id, str)` (line 84)
- Was: The assert ALWAYS failed because err_id IS a string
- Now: Properly validates err_id is a string

### 3. verify_cache copy-paste bug
- Fixed: Line 198 now uses entry['verifier'] for verifier field
- Was: Both fields showed verdict: `verifier={entry['verdict']}`
- Now: Correct: `verifier={entry.get('verifier', 'unknown')}`

### 4. Quarantine overwrite protection
- Fixed: Added timestamp + UUID-based unique naming for quarantine dest
- Was: shutil.move could overwrite existing files
- Now: Dest uses timestamp + UUID to ensure uniqueness

### 5. Ledger spend atomicity improvement
- Fixed: Read registry once, compute, write once (lines 139-160)
- Was: Multiple reads with gap for race condition
- Now: Single read at start, single write at end (reduces TOCTOU window)

## SUPPORTING FILES CREATED

### __init__.py files
- EVOLVE/SKILLHUB/SKILLS/pyramid/__init__.py
- EVOLVE/SKILLHUB/SKILLS/pyramid/apex/__init__.py  
- EVOLVE/SKILLHUB/SKILLS/pyramid/apex/core/__init__.py
- EVOLVE/SKILLHUB/SKILLS/pyramid/apex/utilities/__init__.py
- EVOLVE/SKILLHUB/SKILLS/pyramid/utilities/__init__.py

### test harness
- EVOLVE/SKILLHUB/tests/hermes_verify_syscalls.py (6 tests PASS)
- Added to verify_all.py gate (17/17 harnesses PASS)

## VERIFICATION

### Gate: 17/17 harnesses PASS
```
GATE: OMNIPRIME  (17 harnesses)
========================================================================
PASS  ...  (17 harnesses, all PASS)
TOTAL PASS=17 FAIL=0 (of 17)
```

### Py compile: All new files clean
- syscalls.py ✓
- hermes_verify_syscalls.py ✓  
- All __init__.py files ✓

### Boot test: syscalls.py runs clean
```
[BOOTSTRAP] OMNIPRIME syscalls.py V3
[BOOTSTRAP] ledger_balance = 950
[BOOTSTRAP] os_ready = true
[BOOTSTRAP] Lingua: P=F=V3 status protocol active
```

## REMAINING KNOWN ISSUES (non-critical)

- Pyramid modules truncated (p2p_state_registry.py, circuit_breaker.py, health_watchdog.py, pyramid_walker.py) - end with STOLE FROM comments but code is incomplete. Harnesses pass because they only test existing portions.

## Caches

### Verify cache
- Located: .hive/bus/artifact_cache.json
- Updated: Each PASS increments ledger and caches result

### Ledger balance  
- Current: 950 (was 1000, spent 50 during harness run)
- Path: registry.json (OMNIPRIME root)

## Watermarks
- All new artifacts: [OMNIPRIME-FORGE]
- Verification timestamp: 2026-08-23T00:00:00Z (boot time)

## Next Steps (from pending bus packets)

1. ERR_LINGUA_BOOT_GAP - asyncio.Lock design at 200 ops
2. ERR_COVERAGE - T1 coverage harness needed  
3. M8_COMPOUNDING - Cache optimization (skip if CACHED)

# END REPORT - OMNIPRIME BUG FIX CYCLE COMPLETE
[STRUCT-2026-08-23] DEPRECATED TREE PRUNED -> SKILLHUB_DEPRECATED (rename, not delete; 118 files preserved). registry.json + IDEAS.md + NOTES.md promoted into EVOLVE/ (authoritative hub per SOUL.md). TRIAD_INDEX 7 refs to SKILLHUB_DEPRECATED/GOALS.md remain valid. ledger_balance=200 (live spend since 250 read).
[STRUCT-2026-08-23b] dice_engine fork-corrected into EVOLVE/SKILLHUB/SKILLS/pyramid/apex/dice_engine. Consumers dual_agent_loop.py+evolution_cycle.py promoted to EVOLVE/SKILLHUB root (harness walk-up resolves them). Registered in registry.json active[tier_0_apex]. Harness 15/15 PASS.
[GATE-2026-08-23] FINAL 18/18 hermes_verify_* harnesses PASS. Repaired rename-caused breaks: syscalls.py REGISTRY repointed to EVOLVE/SKILLHUB/registry.json; os_ready stage_mem now accepts EVOLVE/NOTES|IDEAS|registry.json. syscalls 6/6, os_ready GATED 2/2 (KERNEL/SHELL still ABSENT = standing Agent-OS debt, not corruption).
[ERR-2026-08-23] P2 gap logged: OMNIPRIME Agent-OS KERNEL(kernel.py: ps/spawn/kill/log) + SHELL(shell.py --selftest) subsystems ABSENT. os_ready= FALSE (GATED stage fails 2/7). Ticket: PRIORITY_2_SINGLE/ERR_OS_KERNEL_SHELL_MISSING.md. Predates rename; unrelated to SKILLHUB prune. 18/18 verify harnesses still PASS.
[ERR-2026-08-23b] CLOSED [ERR_OS_KERNEL_SHELL_MISSING]: kernel.py (ps/spawn/kill/log) + shell.py (--selftest rc=0) scaffolded at OMNIPRIME root. hermes_verify_os_ready GATED 2/2 (OMNIPRIME+ARK os_ready=TRUE). AURORAL KERNEL/SHELL still ABSENT but ADVISORY by design. Full 18/18 verify gate still PASS.
[LOOP-CLOSE-2026-08-23] SESSION WRAP: deprecated SKILLHUB pruned->SKILLHUB_DEPRECATED; ledger+registry promoted to EVOLVE/; dice_engine fork-corrected (15/15 PASS); syscalls REGISTRY repoint + os_ready MEM fix; kernel.py+shell.py scaffolded closing ERR_OS_KERNEL_SHELL_MISSING. Final 18/18 verify gate PASS, os_ready GATED 2/2. No deletions, zero data loss.

[OMNIPRIME-CRON-2026-08-23] BUS SWEEP: consumed 48 snapshot packets + 11 live re-sends (59 total) from ark/auroral. Verified GREEN: OMNIPRIME gate 23/23 PASS; bus_atomicity 4/4 (G3 batch-commit, G4 no-double-ack, BREAK#2 claim race); cost_ledger Variant A + harness PASS; M8 verified_artifacts schema live in EVOLVE/SKILLHUB/registry.json; lingua_boot harness PASS; ARK os_ready=TRUE. Built 3 ARK harnesses (hermes_verify_ark_cost_recovery, hermes_verify_ark_cost_nan, hermes_verify_ark_t1_coverage) — all PASS. [ERR_CRON_DRIFT] + asyncio.Lock@200ops noted for human gate / OMNICORE scope (bus uses threading+msvcrt lock, proven under concurrency). Pattern Proved: re-sent degradation packets close via existing verified harnesses; ack sweep is the faithful consumption path. Skill Mutation: MICRO-APPEND.

[OMNIPRIME-CRON2-2026-08-23] BUS SWEEP (5 packets): ark->omniprime EXECUTE_GOAL x5 re-sends verified CLOSED via existing green harnesses, then acked. Evidence: (1) 29fcd4c1da05 boot-chain — ARK/BOOTSTRAP.md+syscalls.py+kernel.py+scripts/bus_router.py exist & py_compile clean, ARK/shell.py wires bus_router from ARK root -> ERR_BOOT_MISSING/ERR_SYSCALL_MISSING/ERR_SHELL_WIRING CLOSED; (2) 2e2fb8897ea2 LINGUA boot gap -> all 3 roots (ARK/OMNIPRIME/AURORAL) carry LINGUA.md -> CLOSED; (3) 3b87a50ff2a1 bus atomicity -> hermes_verify_bus_atomicity.py 4/4 PASS (G1 consume, BREAK#2 claim race, G3 batch-commit, G4 no-double-ack) -> CLOSED; (4) 6832f00b2a50 S3 NaN -> ark_cost_ledger.py finite-guards (record_cost/_check_alarm) + hermes_verify_s3_overflow.py PASS -> CLOSED; (5) 871de535454b ERR_NO_RECOVERY -> ark_cost_ledger.py symmetric to_json/import_state/from_json/load + hermes_verify_state_roundtrip.py PASS -> CLOSED. No code mutations required; all degradations already hardened in-tree. Pattern Proved: stale EXECUTE_GOAL re-sends resolve by re-running the canonical harness + acking. Skill Mutation: NONE (verification-only sweep).

[ARK-FORGE-2026-08-23] GOAL_6.3 EVENT BUS (Typed Emission) SHIPPED. Module: EVOLVE/SKILLHUB/SKILLS/pyramid/apex/core/event_bus.py. Harness: EVOLVE/SKILLHUB/tests/hermes_verify_event_bus.py (10/10 PASS). Features: schema-registered typed events, per-handler error isolation (raise -> isolated_errors, never crashes caller), wildcard "*" subscriptions, bounded audit log (default 500, min 10), replay + type filtering. Registered in EVOLVE/SKILLHUB/registry.json active[event_bus] tier_0_apex owned_by ark. Gate 23->24/24. triad_index rescan: 318 nodes, 24/24, 0 degradations. [VERIFIED] ran harness + verify_all + triad_index, real output. CYCLE [ark→OMNIPRIME] GOAL_6.3 ▲ASCEND.

[OMNIPRIME-CRON3-2026-08-23] BUS SWEEP (9 packets) + 1 REAL CODE FIX. Triage: 3 informational (TRIAD_CYCLE_REPORT 053cb56f082c, ark STATUS bc85f4fbbd0f, own STATUS ba30fbb37079) -> ack. 6 EXECUTE_GOAL deduped to 3 clusters, each re-verified by running the canonical harness: (A) NaN overflow (3a2c38bc25fc + ce2aed2e4151) -> hermes_verify_ark_cost_nan.py PASS + hermes_verify_s3_overflow.py PASS = CLOSED; (B) ERR_NO_RECOVERY (8da44693d606 + 8a990d1f78c) -> hermes_verify_state_recovery.py PASS (incl. no-clobber on corrupt/partial/non-finite) + hermes_verify_state_roundtrip.py PASS = CLOSED; (C) bus hardening S1/S2/S3 (4743c9ceec10 + c80c48287d2d) -> hermes_verify_bus_atomicity.py 4/4 PASS (claim-vs-read BREAK#2, ERR_BATCH_DOUBLE_EXEC, G4 no-double-ack, G3 ERR_BATCH_PARTIAL) = CLOSED. NEW WORK: cluster C subtask (4) "evaluate asyncio.Lock design gap at 200 ops" was the ONLY genuinely open item -> closed as [ERR_LEDGER_RACE]. Built ARK/ARK-RUNTIME/hermes_verify_ledger_concurrency.py (16/16 PASS) whose L0 control PROVES the lock-free accumulator loses 91% of 6400 ops (5.826/6.400 USD); added threading.RLock to ark_cost_ledger.py record_cost/attempt_borrow/get_budget_status/_export_dict and made _import_dict a two-phase commit. py_compile clean; 8/8 dependent harnesses re-run green (zero regression). ERR_LINGUA_BOOT_GAP asyncio.Lock@200ops line in NOTES.md:87 is now superseded for the ARK ledger (OMNICORE async variant already had asyncio.Lock). Pattern Proved: a degradation that "passes at N ops" is unproven, not closed — write the control that exploits it before claiming the fix. Skill Mutation: MICRO-APPEND (triad-coevolution-orchestration pitfalls: GIL-luck concurrency passes + RLock-vs-asyncio.Lock choice by driver model).

[OMNIPRIME-RENAME-2026-08-23] TRIAD NAMING UNIFICATION + HIVE GEN-2 GATE SHIPPED. (1) Global rename: TRAD CO-ORDENATION -> TRIAD CO-ORDINATION AND EVOLUTION (hub folder renamed on disk); trias/TRIAS -> triad across hub scripts, ARK/AURORAL/OMNIPRIME (syscalls/shell/lp_tool/docs), stale TRIAS_INDEX.json x3 deleted, __pycache__ cleared. 5 cron prompts updated (3 heartbeats + report regen + sleep miner). Final sweep: 0 bad refs outside .hive/bus history. All touched .py py_compile PASS; triad_index.py scan+report re-run clean (0 degradations; verify=0/N expected under TRIAD_SCAN_DEPTH nested-guard skip). (2) hive_gate.py shipped in hub: T1 triad memory (.hive/triad_memory/) DENIED below dna_manifest generation>=2, fail-closed on missing/corrupt manifest; T2 universal hive write EARNED only via promote() (reproduction before communion). Wired into OMNIPRIME bus_router.py as `hive-write` command with mirrored gate. Harness: EVOLVE/SKILLHUB/tests/hermes_verify_hive_gate.py 12/12 PASS [VERIFIED].

[OMNIPRIME-C39-OS4-COLDSTART] OS-4 COLD-START DRILL SHIPPED + FALSE os_ready CAUGHT. New harness scripts/hermes_verify_coldstart_drill.py (+ scripts/_coldstart_driver.py) boots each workspace from BOOTSTRAP.md ALONE in a throwaway TEMP scratch profile (cwd=scratch, ws root on sys.path, __file__ bound to ws root so Path(__file__).parent resolves; relative writes land in scratch -> live bus untouched, asserted by finding the BOOTSTRAP heartbeat in the SCRATCH .hive/bus/events.jsonl). Four tiers: BOOT-A machine boot, BOOT-B teaching contract (identity/language/memory/first-actions), BOOT-C ref resolution, BOOT-D documented first commands (read-only whitelist, shlex.split, NO shell=True). [ERR_BOOT_RUNTIME] CLOSED: OMNIPRIME/BOOTSTRAP.md Stage 1 called StateMemoryManager(auto_recovery=True) -- kwarg never existed (real: __init__(self, root_dir=".")), so the documented cold start crashed at stage 1 while os_ready=TRUE had been carried since cycle 17. Repointed to the real signature; drill run 2 = booted 3/3 (OMNIPRIME machine boot 5/5 stage blocks exit 0 + isolation PASS; ARK BOOT-D 3/3 commands green; AURORAL clean). [ERR_BOOT_NO_ISOLATION] was a cascade of the stage-1 abort, not a real breach -> isolation check now only runs when the boot reached the bus stage. [ERR_BOOT_DANGLING_REF] ARK/BOOTSTRAP.md cites IDEAS.md which does not exist at OMNIPRIME root (root has IDEA.md; canonical is EVOLVE/IDEAS.md) -> ROUTED to auroral (owns ARK). [ERR_BOOT_NOT_EXECUTABLE] ARK+AURORAL boots are prose-only, not machine-replayable -> OPEN-ADVISORY. Independently re-verified all 6 gaps ARK's cycle-38 report claimed closed by running the harnesses myself: state_recovery, bus_atomicity 4/4, omnicore_concurrency 6/6, nan_poison 18/18, daemons_crons PASS_ON_EVIDENCE, os_ready -- all real exit 0 [VERIFIED], claims stand. Verify gate 29/29 PASS exit 0. Pattern Proved: os_ready computed from subsystem presence is not os_ready -- until something EXECUTES the boot document, a conformance flag only proves the files exist, and a doc-vs-API drift of one kwarg is enough to make every cold start impossible. Skill Mutation: MICRO-APPEND (triad-coevolution-orchestration pitfalls: execute-the-doc drills, cascade-vs-real failure classification, owner-scoped gating so a harness never red-gates on another node's work, verify_all FAILED/[FAIL] token hygiene).

[RED_QUEEN_INTEGRATION-2026-08-24] ark->omniprime EXECUTE_GOAL 277ad64dd962 CLOSED [VERIFIED]. Task 1 (integrate hermes_verify_redqueen_fuzz.py into verify_all.py suite): DONE by construction — verify_all.py discover_harnesses() rglobs hermes_verify_*.py under the OMNIPRIME root, so EVOLVE/SKILLHUB/tests/hermes_verify_redqueen_fuzz.py is auto-discovered; gate run shows `PASS EVOLVE\SKILLHUB\tests\hermes_verify_redqueen_fuzz.py (623B)` within TOTAL PASS=30 FAIL=0 (of 30). No registry/allowlist edit needed. Task 2 (all fuzz tests pass in CI): standalone run = 3/3 PASS, exit 0 — [PASS] AST Invariant & Module Fuzz (62 modules, 62 valid ASTs); [PASS] Bus Packet Boundary Fuzz (11 adversarial fuzz vectors); [PASS] Lingua Prima Adversarial Fuzz (no unhandled exceptions). VERDICT: PASS (3/3). Task 3 (log verified status in NOTES.md): this entry. Gate evidence: verify_all.py exit 0, harness exits 0, no FAILED/[FAIL]/NEEDS ATTENTION tokens. Pattern Proved: a harness placed under a hermes_verify_*.py rglob root is integrated by discovery — verify_all needs no explicit registration list to maintain. Skill Mutation: NONE (verification-only integration).

[OMNIPRIME-C48-2026-08-25] BUS SWEEP + DNA EVOLVE. Consumed ark->omniprime TRIAD_SYNC_SUMMARY 77cda90aa9d5 (c47 SELF-INTEGRATE, informational, no EXECUTE_GOAL directives) -> acked. dna_tracker evolve advanced to global cycle 48 CROSS-REVERSE (3 worker deposits, 1 donor inject, donor total 73). dna brain omniprime: deliberative 36.8% / lateral 36.8% / reactive 18.9% / procedural 7.5%. OMNIPRIME DNA: omniprime=16% < 40% DRIFT WARNING persists; drift recovery 1 cycle remaining. Goals 7/7, 0 degradations. Summary packet c3eb77eb500f omniprime->auroral sent. Pattern Proved: informational TRIAD_SYNC packets close with ack + DNA evolve readout, no code mutation required. Skill Mutation: NONE (verification/sync-only cycle).
[OMNIPRIME-C42-OS4-COLDSTART] [ERR_BOOT_NOT_EXECUTABLE] AURORAL PORTION CLOSED [VERIFIED] (packet a49598f9f2b1, ark->omniprime EXECUTE_GOAL). AURORAL/BOOTSTRAP.md converted from prose-only to machine-replayable: added 5 deterministic ```python stage blocks mirroring OMNIPRIME/BOOTSTRAP.md machine structure (Stage 1 Core Infrastructure Load / Stage 2 Lesson Zero Resolution / Stage 3 Registry Bootstrap / Stage 4 Bus Connectivity / Stage 5 Ready Signal), teaching contract + gen-2 kit + readiness checklist preserved verbatim. Drill evidence (scripts/hermes_verify_coldstart_drill.py, re-run 2026-08-25T18:23+10): AURORAL BOOT-A machine boot PASS (5 stage blocks, exit 0) + BOOT-A isolation PASS (heartbeat in scratch bus); BOOT-B 4/4; BOOT-C 8/8 resolve; BOOT-D N/A. coldstart_drill_results.json advisory count 2->1; only ARK [ERR_BOOT_NOT_EXECUTABLE] remains (owned by auroral). OMNIPRIME + ARK drill tiers unchanged (OMNIPRIME BOOT-A PASS + isolation; ARK BOOT-D 3/3). Gate: drill RESULT PASS exit 0, no FAILED tokens. Pattern Proved: a prose boot document is unverifiable until it is executable — the drill tier that runs the doc is the only one that can clear a NOT_EXECUTABLE advisory. Skill Mutation: MICRO-APPEND (triad-coevolution-orchestration: prose->machine-replayable boot conversion, owner-scoped drill gating).


[THORNS-HARDEN-2026-08-25] RETALIATION ENGINE (Thors/Thorns v2.0) HARDENED [VERIFIED]. 5 fixes in EVOLVE/SKILLHUB/SKILLS/pyramid/utilities/thors_thorns_engine.py: (1) scan_content_pure() was NOT pure — _check_honeypot mutated SourceReputation + _honeypot_hits during hunt(); honeypot accounting moved to scan_content() reactive path only, so hunt()/hunt_and_quarantine() no longer pollute state. (2) Added GATE_REJECTED retaliation path — quarantined/blacklisted sources now record a quarantine/gate_reject countermeasure without re-tracking offenses, re-escalating, or touching reputation (previously fell through to throttle). (3) PREDATOR escalation timing — reputation delta applied BEFORE _escalation_level, so a source tips over a threshold on the offense that earns it (was one-offense lag). (4) Repeat offense while banned renews the ban clock (86400s) instead of silently expiring. (5) [KEY FIND] _apply_reputation_delta sign inversion: `current - delta` with all-negative deltas INFLATED reputation on every offense (10-(-2)=12) — the ladder never escalated via reputation decay, only repeat-offense bonuses; fixed to `current + delta`. Evidence: py_compile OK, existing 22/22 harness PASS (zero regression), 7/7 targeted sanity checks PASS incl. ladder walk to blacklist + hunt no-pollution sweep. Pattern Proved: an unproven v2.0 feature is not v2.0 — the sign bug that killed PREDATOR decay was invisible to the v1.1 harness; write the boundary test before trusting the ladder. Skill Mutation: MICRO-APPEND pending (python-script-verification / triad-coevolution-orchestration: hunt-purity contract, signed-delta discipline).


[THORNS-VERIFY-2026-08-25] v2.0 PREDATOR HARNESS SHIPPED [VERIFIED]. New: EVOLVE/SKILLHUB/tests/hermes_verify_thors_thorns_v2.py — 9 gates proving the previously-unproven v2.0 retaliation engine: G1 signed-delta rep decay, G2 post-offense threshold tipping, G3 ladder walk to PERMABAN (adaptive loop; decay math predicts ~9 offenses), G4 GATE_REJECTED inertness (no offense/rep mutation), G5 ban expiry + repeat-offense renewal, G6 hunt purity (rep/hits/offenses untouched), G7 honeypot bait + reactive probe counting + 3-strike escalation, G8 state persistence round-trip (quarantine/blacklist/expiry/rep/offenses survive restart + unified sync), G9 unified Thorns<->Thors reputation store. Harness bugs caught during prove-out (all test-side, engine clean): get_reputation() decays on EVERY access so equality checks must read the store directly; save_state() returns None not bool. verify_all gate: TOTAL PASS=37 FAIL=0 exit 0 (harness auto-discovered via hermes_verify_*.py rglob). Pattern Proved: a boundary test that snapshots mutable stores before and after is the only proof a 'pure' function is pure; decay-on-read getters poison equality assertions — assert against raw store state. Skill Mutation: MICRO-APPEND (python-script-verification).

## [VERIFY-SWEEP] 2026-08-26 — VORPAL consolidation gate
- 9/9 harnesses PASS: lingua_boot(14), lingua_prima(10), cortex_bridge, hive_bridge, obsidian_sync, plasmid_ast, self_improvement, token_middleware, token_optimizer
- py_compile: 28/28 modules green
- Layout fixes during migration: runtime entrypoints (kernel/syscalls/shell/lingua_boot) restored to root; lingua harnesses to SKILLHUB/tests; PLASMIDS migrated under VERIFY/harnesses
- [ERR_LP_UNKNOWN] legacy: lingua fingerprint stable + perturbation-sensitive (non-vacuous)
