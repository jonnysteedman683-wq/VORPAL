# TRIAD Case Study — Live Multi-Profile Ring (ARK/OMNIPRIME/AURORAL)

Reference walkthrough of a production multi-profile orchestration built 2026-08-23.
All numbers were real at time of capture; treat as example shapes, not current state.

## Layout
- Hub: `Desktop/TRIAD CO-ORDINATION AND EVOLUTION/` containing:
  - `triad_index.py` — scans ARK/AURORAL/OMNIPRIME into per-root TRIAD_INDEX.json
    (nodes with kind/status/verify results, goals, degradations, owned_by)
  - `triad_soul_evolve.py` — grades each cycle vs stored state
    (soul_evolution_state.json), appends ledger lines to SOUL_UPGRADES/<p>_SOUL.md
  - `LINGUA_PROTOCOL.md`, `lp_tool.py` — shared compressed language + CLI
  - `RECURSION_ROADMAP.md`, `AGENT_OS_ROADMAP.md` — main goals
  - `FORCE_MULTIPLICATION.md` + `_V2.md` — multiplier catalog M1–M11
  - `LOOP_REGISTRY.md` — all scheduled loops machine-wide (24 across 4 schedulers)

## Routing
ark→OMNIPRIME workspace, omniprime→AURORAL, auroral→ARK. Cyclic; verified by next node.

## Schedules (2× accelerated)
- Heartbeats every 15 min staggered: ark :00/:15/…, auroral :05/:20/…,
  omniprime :10/:25/…
- TRIAD grade+report: :12/:27/:42/:57
- Sleep-time miner: :08/:23/:38/:53

## Soul section template (per profile)
A. Language protocol (shared compressed vocabulary; never compress commands/paths)
B. Memory tiers: L1 bus free · L2 ledgers append-only · L3 grades orchestrator-only
C. Ownership graph + explicit edit/no-edit lists
D. Standing orders (session-start reads, inbox check, work→verify→index→ack)
E. Main goals (recursion eligibility + Agent OS conformance)
F. Competitive experiment protocol (competitor/judge/host roles rotate)

## Key mechanisms
- Verify gate: run every hermes_verify_*.py in workspace; pass ratio = gate.
- Degradations = failing harnesses + compile failures; graded on delta.
- Work stealing: claim/steal bus commands with msvcrt/fcntl lock; only pending.
- Artifact cache: sha256(path|mtime) → verdict; consumers skip re-verification.
- Spawn eligibility: ≥10 clean cycles + cold-start drill + human approval.

## Results snapshot (capture date)
Cycle 1: all three workspaces 100% verify gate, 0 degradations (from baseline of
11). Throughput scaled from 9 tasks/day (single dispatch) to ~96/day potential
(batches × 15-min pipeline). First work-steal executed live within minutes of
the claim command shipping.

## Research anchors
Darwin Gödel Machine arXiv 2505.22954 (archive growth, empirical validation),
ADAS/Meta Agent Search 2408.08435 (meta-agent programs agents in code),
EvoFlow 2502.07373 (heterogeneous free-model populations),
RSI survey 2607.07663 (grounding guards + human gates prevent recursion collapse).
