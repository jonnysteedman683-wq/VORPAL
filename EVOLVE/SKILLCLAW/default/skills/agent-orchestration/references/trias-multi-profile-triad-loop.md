# TRIAS Pattern — Multi-Profile Triad Co-Evolution Loop (Gen-1 build, 2026-08-23)

Session-validated blueprint for running N specialized Hermes profiles as a
cyclically-routing work ring with unified grading. Built live across a full
session; all steps verified working.

## Topology
- Profiles: ark / omniprime / auroral (live under `AppData/Local/hermes/profiles/`)
- Cyclic routing: ark→OMNIPRIME workspace, omniprime→AURORAL, auroral→ARK
  (each profile works on the NEXT workspace, never its own)
- Shared neutral hub folder on Desktop holds: indexer, grading engine, protocol
  docs, staged souls, unified report
- Packet bus: `OMNIPRIME/scripts/bus_router.py` (send/read/ack/events) +
  `bus_check.py <profile>`; state in `.hive/bus/` (events.jsonl + inbox_<profile>/)

## Build sequence that worked
1. Indexer (`trias_index.py`): scans workspaces → per-root TRIAS_INDEX.json
   (nodes, goals, verify-gate pass/fail, degradations, owned_by) → merged
   TRIAS_REPORT.md. Handle missing workspace dirs (mkdir before write_text).
2. Heartbeats: `hermes cron create --script <shim>.py --model X --provider Y
   --deliver local '<cron-expr>' '<self-contained prompt>'`. CRITICAL: bare
   `30m` schedules as ONE-SHOT ("once in 30m") — pass explicit cron expr
   `*/30 * * * *` for recurring, then `hermes cron edit <id> --repeat -1` if
   repeat shows 0/1. `--repeat 0` is NOT infinite.
3. Per-profile shim scripts (in profile scripts/ dir) runpy the shared
   bus_check.py with sys.argv preset — keeps one canonical bus script.
4. Report+grade cron at :10/:40 (offset from worker heartbeats at :00/:30):
   runs indexer then grading engine, delivers compact delta summary.
5. Grading engine (`trias_soul_evolve.py`): compares gate ratio + degradation
   counts vs stored state → ASCEND/HOLD/DESCEND verdict → appends ledger line
   inside `<!-- TRIAS_LEDGER_START/END -->` markers in staged soul files.

## Soul/directive architecture (user-validated)
- Souls live staged in hub `SOUL_UPGRADES/<profile>_SOUL.md`; user copies them
  into profile dirs manually. NEVER write directly into profile dirs unasked.
- Soul sections: identity/axioms, triad procedure, bus commands, routing table,
  performance ledger (append-only, orchestrator-only), evolution rules, and a
  MAIN GOAL section (recursion/fractal spawning).
- One generic drop-in TRIAD_DIRECTIVE.md (same text all profiles) binds
  profiles to the hub folder; profile-specific behavior lives in each soul.
- Memory tiers in souls: L1 bus packets (free), L2 workspace ledgers
  (APPEND-ONLY, tagged claims), L3 soul ledgers (orchestrator-only writes).

## Lingua compression channel
- Canonical engine: `OMNIPRIME/EVOLVE/SKILLHUB/SKILLS/pyramid/LANGUAGE/lingua_prima.py`
  (263 tokens, 441 concepts, ~85% compression on known patterns).
- Thin CLI wrapper (lp_tool.py: enc/dec/info) beats direct import for profiles.
- Mandate in souls: thinking chains (a→b→t), packet directive summaries,
  report shorthand (CYCLE_N [who→target] V#/# D# ▲verdict). NEVER compress
  commands/paths/tracebacks; unknown token = reject + re-request English.
- Compression doubles as traffic obfuscation between profiles.

## Recursive spawning (main goal)
- Fractal: gen-1 triad earns right to spawn gen-2 (≥10 clean cycles, cold-start
  drill proving bootstrap kit suffices, stable dictionary), human approval at
  every generation boundary. Research anchors: Darwin Gödel Machine (archive,
  never delete failed variants), ADAS Meta Agent Search (agents-as-code),
  EvoFlow (heterogeneous free-model population), RSI survey arXiv 2607.07663
  (grounding guards: real-harness verification only, no self-grading).
- Success metric: TIME_TO_CLEAN per generation — compounding if children
  reach gate parity faster than parents did.

## Pitfalls hit this session
- Workspace folder name MUST match profile name exactly (user corrected
  AURORA → AURORAL). Name folders after profiles, not concepts.
- Stale bus packets from superseded routings must be acked before dispatching
  new directives, or workers execute dead orders.
- arXiv research path when web_search is dead: curl abs pages for titles +
  abstracts via regex on blockquote.abstract; arXiv API export.arxiv.org/api/
  query works with curl for keyword search.
- execute_code f-strings containing `{}` in shell one-liners break — write a
  temp script file instead, or avoid f-strings around shell payloads.
- git-bash `python script.py` with leading `/c/...` path failed ("can't open
  file C:\c\...") — cd into the dir first, then run relative path.
