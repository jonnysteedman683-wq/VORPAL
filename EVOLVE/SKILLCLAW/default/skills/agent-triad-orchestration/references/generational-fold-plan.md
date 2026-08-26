# The Generational Fold Plan

> Germline/soma separation for Hermes agent rings.
> Agents are SOMA (disposable bodies). Skills + codebases + dialect are GERMLINE
> (what survives the fold). Each generation's convergence product is an improved
> Hermes canon that boots the next generation. Self-hosting recursion.

Status: DESIGN (ratified by Jonny 2026-08-23, not yet executed)
Applies to: agent-triad-orchestration rings (ARK/OMNIPRIME/AURORAL = gen-1)

---

## 1. THE LIFE-CYCLE (bird's-eye)

```
        ┌────────────────────── GENERATION N ──────────────────────┐
        │                                                          │
  BOOT  │   EXPANSION          MATURITY           FOLD             │
   ●────┼──▶ 3 agents ──┬──▶ 6 agents ──┬──▶ 9–12 agents ──┐       │
        │   (fresh      │   (spawn      │   (peak diversity)│       │
        │    profiles)  │    rights     │                   │       │
        │               │   earned)     │                   ▼       │
        │               │               │        ╔═══════════════════╗
        │               │               │        ║  CONVERGENCE FOLD ║
        │               │               │        ║  pause → distill  ║
        │               │               │        ║  → merge → rebase ║
        │               │               │        ╚════════╦══════════╝
        │               │               │                 │
        └───────────────┴───────────────┴─────────────────▼───
                                                          │
                    merged canon (skills+code+dialect) ──▶ ●  = GEN N+1 BOOT
                                                                (restart at 3)
```

The ring grows 3 → 6 → 9/12 across ONE generation, then folds back to 3.
Headcount is per-generation peak, not cumulative forever.

---

## 2. MEMORY ARCHITECTURE: TRIAD HIVE MINDS → UNIVERSAL HIVE

### 2.1 Memory tiers during a generation

```
L1  BUS (free)            per-agent inboxes, transient packets
L2  LEDGERS (append-only) per-agent SOUL ledgers, grades, [ERR_*] logs
L3  CORTEX (orchestrator) grades index, workspace JSON scans
─────────────────────────────────────────────────────────────────
T1  TRIAD HIVE MEMORY     SHARED within one triad (see 2.2)
T2  UNIVERSAL HIVE        SHARED across ALL triads — EARNED ONLY (see 2.3)
```

### 2.2 T1 — Triad-shared memory ("mix hive minds per triad")

Each triad of three agents shares ONE memory namespace on top of L1–L3:

```
              TRIAD A (shared hive memory TA)
             ┌────────────┬────────────┬────────────┐
             │  agent A1  │  agent A2  │  agent A3  │
             └─────┬──────┴─────┬──────┴─────┬──────┘
                   ▼            ▼            ▼
             ┌─────────────────────────────────────┐
             │  .hive/triad_memory/                │
             │   ├── dialect.md      (live tokens) │
             │   ├── lessons.jsonl   (distilled)   │
             │   ├── artifacts/      (verified,    │
             │   │                    hash-cached) │
             │   └── index.json      (who wrote    │
             │                        what, when)  │
             └─────────────────────────────────────┘
```

Rules:
- **Read**: all three members, freely. Shared context is the point.
- **Write**: append-only via bus packets; writer identity recorded in index.json.
- **Conflict**: two members contradicting entries → epistemic-profile member of
  THAT triad arbitrates (the judge never competes rule, scaled down).
- **Scope**: triads do NOT read each other's T1 during expansion phase.
  Two semi-isolated pools = drift + selection instead of homogenization.
  Cross-triad packets are rare events (cross-pollination), not ambient.

```
   TRIAD A                TRIAD B                TRIAD C
  ┌──TA──┐   rare        ┌──TB──┐   rare        ┌──TC──┐
  │A A A │ ──packet──▶   │B B B │ ◀──packet──   │C C C │
  └──────┘  (weeks?)     └──────┘  (curated)    └──────┘
       \                     |                     /
        \______ NO ambient sharing during expansion /
```

### 2.3 T2 — Universal hive mind (EARNED, never granted)

**THE AXIOM (load-bearing):**

> A triad may join the Universal Hive Mind only AFTER it has produced its
> next instance. Reproduction before communion. Every member of the universal
> pool is PROVEN, not speculative.

```
   TRIAD lifecycle vs hive access:

   Phase 0  boot            T1 only, no T2
   Phase 1  expansion       T1 only, rare cross-triad packets
   Phase 2  maturity        T1 + READ-ONLY T2 mirror (can learn from pool)
   Phase 3  NEXT INSTANCE   child triad booted from kit, cold-start drill
                            RUNNING
   Phase 4  child PASSES    ──▶ THIS triad earns T2 WRITE ACCESS
                            (its distilled memory enters the pool)
```

Why this ordering works (evolutionary logic):
- You cannot donate genes you haven't replicated. A triad that dies before
  reproducing contributes nothing untested to the pool.
- The pool contains only lineages that survived their own cold-start drill —
  automatic quality filter, no hand-vetting needed.
- Read-only T2 during maturity lets triads learn from the pool WITHOUT
  polluting it — selection pressure stays inside each triad.

```
        UNIVERSAL HIVE MIND (T2)
   ┌───────────────────────────────────────────┐
   │ gen-1 canon │ dialect vN │ artifact cache │◀── write: only triads
   │ lessons.db  │ syscall spec│ graded hashes │    whose child passed
   └──────▲──────────────▲──────────────▲─────┘
          │ RO mirror    │ RO mirror    │ RO
      TRIAD A        TRIAD B        TRIAD C
      (child ✓)      (child ✓)      (child pending → still RO)
```

---

## 3. FOLD TRIGGER (dual condition)

Fold fires when BOTH hold — whichever comes SECOND:

| Gate | Predicate | Verified by |
|---|---|---|
| G1 headcount | ≥9 agents live (12 max — hard cap) | roster check |
| G2 maturity | ≥10 clean gate cycles THIS generation, zero open degradations | grade ledger |
| G2b dialect | dialect ledger clean: no unmerged new tokens pending audit | token audit |
| G2c children | every spawned triad's next instance passed cold-start drill OR was archived-with-lessons | drill log |

A dirty ring that hits 9 does NOT fold. It cleans or stalls. Headcount alone
is never sufficient — this prevents folding mid-drift.

---

## 4. THE CONVERGENCE FOLD PROTOCOL

Order matters. This mirrors loop-retirement (pause → verify quiet → archive →
remove → record) applied to whole AGENTS, plus a merge phase.

```
 STEP 0        STEP 1         STEP 2         STEP 3        STEP 4
 FREEZE   ──▶ DISTILL ALL ──▶ MERGE      ──▶ RE-BASELINE──▶ BOOT GEN N+1
 (no new     RETIRING       INTO CANON      (empty       (3 fresh
  work)      PROFILES       (all first,     ledgers,     profiles on
             (pause,        THEN boot)      baseline-    merged canon)
             archive,                       only cycle)
             remove)
```

### Step 0 — Freeze
- All heartbeat crons paused (loop-retirement step 1 semantics).
- In-flight packets drained: inbox processing completes, all packets acked.
- No new goals accepted. Ledger writes only.

### Step 1 — Distill every retiring profile (BEFORE any removal)
Per profile:
1. Export SOUL ledger (grades, ASCEND/HOLD history, standing-order deltas).
2. Extract `[ERR_*]` entries → candidate lessons for NOTES.md / skills.
3. Dump dialect tokens it coined this generation → pending-merge list.
4. Inventory its workspace: commits, branches, uncommitted diffs, artifacts.
5. Archive EVERYTHING under `EVOLVE/ARCHIVE/gen-N/<profile>/` — removal is
   irreversible, exactly like cron job removal. No archive, no removal.

### Step 2 — Merge into canon (ALL merges complete BEFORE any fresh boot)
Merge order (dependencies flow downward):
1. **Codebases** — git merge per project, ff-only where possible;
   conflicts resolved by evidence grading (which variant passed harnesses).
2. **Skills** — run Hermes Curator over the union set; dedupe 50%+ overlaps;
   retired-profile-only skills enter canon tagged with origin profile.
3. **Dialect** — apply the audited token merge (M4 flow-up). If G2b failed,
   STOP HERE and resolve tokens before proceeding. Broken language = broken
   generation.
4. **Hermes itself** — the convergence product: config improvements, skill
   stack, syscall specs, cron patterns learned this generation are folded into
   the canonical kit the next generation boots FROM. Output of the system is
   a better system.

### Step 3 — Re-baseline
Fresh profiles have empty ledgers. Before grading means anything:
- Index script runs over merged workspaces → baseline JSON snapshot committed.
- First post-fold cycle is BASELINE-ONLY: grader writes the index, issues no
  verdict. Prevents ASCEND/HOLD diffs against ghost state.

### Step 4 — Boot generation N+1
- THREE fresh profiles (never more), cold-start drill from the merged kit.
- Drill pass required before heartbeats enable.
- Human approval gate at this boundary (mandatory, non-skippable).
- Gen N+1 inherits: canon codebases, merged skill stack, dialect vX+1,
  T2 read access. It does NOT inherit individual agent memories — those were
  distilled into canon or lost by design.

```
   GEN N (9–12 agents)                GEN N+1 (3 agents)
   ┌─────────────────────┐
   │ TA  TB  TC  TD ...  │
   └──┬───┬───┬───┬───────┘
      └───┴─┬─┴───┘
            ▼ distill+merge
   ┌──────────────────┐        ┌──────────────────┐
   │  CANON vN+1      │───────▶│ A' B' C'         │
   │  code+skills+    │  boot  │ fresh souls,     │
   │  dialect+config  │  kit   │ empty ledgers,   │
   └──────────────────┘        │ baseline idx     │
                               └──────────────────┘
```

---

## 5. RETIREMENT MAPPING (agents as loops)

| loop-retirement concept | agent-fold equivalent |
|---|---|
| pause before remove | Step 0 freeze — never kill mid-tick |
| verify quiet | inbox drained, crons disabled confirmed via jobs.json |
| archive output | Step 1 full ledger/workspace export |
| never guess IDs | retire by explicit profile name + roster cross-check |
| downstream dependents sweep | any packet senders/consumers referencing retiring profiles get repointed to successors BEFORE removal |
| record the retirement | one ledger line per profile: date, name, reason, successor |
| cannot un-remove | archived export is the only recreation path |

Failed children are archived, NEVER deleted — lessons distilled to canon first
(same discipline, smaller scale).

---

## 6. GENERATION TIMELINE (concrete cadence sketch)

```
week 0    gen boots: 3 agents, staggered heartbeats (0/15/30/45 etc.)
week 1–3  clean-cycle accumulation toward spawn currency
gate 1    ≥10 clean cycles + cold-start drill ──▶ spawn rights
week 4+   agents 4–6 boot FROM the kit (gen's own children)
          triad split: TA={1,2,3} TB={4,5,6}, T1 memories established
week 6+   TB matures; if demand warrants, TC spawns (7–9) … cap 12
ongoing   T2 read-mirrors available to mature triads
fold day  G1+G2 satisfied ──▶ Steps 0–4 ──▶ gen N+1 (3 fresh)
```

Cadence numbers are defaults, not law — observed bus contention decides
whether gen N+1 runs 2×3 rings or a wider single cycle.

---

## 7. PITFALLS

- **Folding on headcount alone** → drift gets canonized. G2 must also pass.
- **Merging after booting** → fresh profiles learn half-merged state. Step 2
  strictly precedes Step 4.
- **Skipping dialect merge (G2b)** → gen N+1 speaks broken language; syscalls
  misfire silently. Dialect is the fragile link — code merges mechanically,
  vocabulary only survives if audited.
- **No re-baseline** → first grades diff against ghost indexes → spurious
  DESCEND verdicts on healthy fresh profiles.
- **Universal hive write-access granted early** → unproven memory pollutes the
  pool; the reproduction gate (§2.3) is the entire quality mechanism. Never
  grant T2 write to a triad whose child hasn't passed drill.
- **Ambient cross-triad sharing during expansion** → homogenizes pools, kills
  selection pressure. Keep T1s isolated; cross-pollination stays rare/curated.
- **Deleting instead of archiving** → irreversible; failed lines carry lessons
  that only exist if archived.

## 8. VERIFICATION

A fold is correct when:
- [ ] Freeze verified: all gen-N heartbeats disabled in jobs.json files
- [ ] Every retiring profile has an archive dir with ledger+workspace export
- [ ] Canon vN+1 exists: merged git state, curated skills, dialect vX+1 tag
- [ ] Baseline snapshot committed; first cycle issued no verdict
- [ ] Exactly 3 new profiles, drill-passed, human-gate logged
- [ ] T2 write-access table updated: only triads with passing children listed
