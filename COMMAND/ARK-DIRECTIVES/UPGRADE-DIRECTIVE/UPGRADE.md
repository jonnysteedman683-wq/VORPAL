# UPGRADE DIRECTIVE
**Binding law for how the ARK vessel improves on a fixed cadence.**

## 1. PURPOSE
Convert accumulated evolution gains into committed, hardened capability. Faithful to
DGM (arXiv 2505.22954) and RQGM (arXiv 2606.26294); see `docs/papers/MECHANISMS.md`.

## 2. CADENCE (autonomous, prompt-independent)
| Cycle | Trigger | Scope |
|-------|---------|-------|
| Micro | hourly | token opt, dead-branch prune, test hardening |
| Major | daily 05:00 | new genesis, directive review, drift reconciliation |
| Patch | on-detect | regression/missing-component repair (P-queues first) |
| **Critic-swap epoch** | **generation ∈ {1,2,4,8,16,…}** | **ε-BB FRACTURE incumbent swap [RQGM §3.5]** |

## 3. UPGRADE ORDER (strict priority queue)
1. **P1 CRITICAL** — multi-category degraded (`skill_repair/PRIORITY_1_CRITICAL/`).
2. **P2 SINGLE** — isolated regressions (`skill_repair/PRIORITY_2_SINGLE/`).
3. **CONSOLIDATION** — overlap/redundant synthesis.
4. **GENESIS** — only when queues empty AND WEST-debt within budget.

## 4. GRAPH EDGE OPTIMIZATION [GPTSwarm]
UPGRADE treats the vessel-grid as an optimizable graph. Beyond node logic, it tunes
the **edges**: inter-node communication weights, routing rules, FRACTURE↔FUSE
feedback gain. Edge optimization sampled via UCB/Thompson expansion
(node→role→task) [RQGM scheduler], not random.

## 5. HARDENING GATE (3-STEP) [DGM / auto-harness]
Every upgrade artifact passes:
1. **Eval run** — benchmark executes the artifact in a sandbox.
2. **val_score** — measured against the frozen ground-truth anchor (epoch-local).
3. **Suite promotion** — new failure-mined tests promoted into the permanent Red
   Queen suite.
A generation that cannot be broken by a harder test is promoted.

## 6. CRITIC CO-EVOLUTION CHECKPOINT [RQGM §3.5]
At power-of-two generations, UPGRADE permits an **ε-BB challenger-swap** of the
FRACTURE incumbent:
- Challenger ranked by ε-best-belief score β on the **frozen anchor**; promoted only
  if it raises β with probability 1−ε; ties favor incumbent.
- On swap → trigger **SELECTIVE ERASURE** + archive re-rank (see EVOLUTION/MEMORY).
- **Epoch-local stationarity:** benchmark/anchor scores comparable ONLY within an
  epoch; cross-epoch comparison requires the fixed anchor.

## 7. ROLLBACK
- Each upgrade = signed commit + provenance hash.
- If POST-UPGRADE FIELD drift worsens 2 gens → auto-rollback to last known-good,
  log `[ERR_ROLLBACK]`.

## 8. OPTIMIZATION BUDGET
- Upgrade may not raise `tier_1_active` total token cost beyond WEST-debt ceiling.
  EAST expansion throttled until consolidation frees budget.
