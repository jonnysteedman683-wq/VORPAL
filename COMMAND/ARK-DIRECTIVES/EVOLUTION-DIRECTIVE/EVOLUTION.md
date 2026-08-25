# EVOLUTION DIRECTIVE
**Binding law for how the ARK vessel changes without breaking.**

## 1. PURPOSE
Drive the vessel-grid forward. Produce change that increases fitness (closer to
NORTH) without breaking self-sealing. Faithful to DGM (arXiv 2505.22954) and RQGM
(arXiv 2606.26294); see `docs/papers/MECHANISMS.md` for verbatim source anchors.

## 2. THE EVOLUTION CYCLE (recursive + self-modifying) [DGM §2]
```
OBSERVE(FIELD drift) → FORGE(self-edit + sample archive) → FRACTURE(frozen critic epoch)
  → FUSE(sandbox + benchmark + 3-step gate) → SELECTIVE-ERASURE + ARCHIVE-REANK
  → UPGRADE(optimize edges; critic-swap at power-of-two epoch)
```
- **Self-modification phase (FORGE):** selected agents from the **archive** (tier
  pyramid) generate modified versions of themselves [DGM verbatim]. FORGE operates
  at TWO levels [DGM → DGM-H / HyperAgents]:
  - *Task level:* edits ARK skills (the task-agent).
  - *Meta level:* edits the meta-agent that writes diffs — the mechanism of
    improvement is itself improvable (metacognitive self-modification). The meta
    policy is archived and FUSE-gated exactly like task-level changes.
- **Evaluation phase (FUSE):** each modified artifact is tested on a benchmark;
  passing artifacts are added to the archive. Alternation is mandatory — no
  self-modification without a following evaluation.

## 3. MUTATION RULES
- **Valid:** token reduction >5% OR `[ERR_*]` resolved OR new verified capability
  with zero functional overlap.
- **Invalid:** cost increase w/o benefit, test regression, or weakened integrity →
  FRACTURE rejects, FUSE refuses.
- **Orthogonality:** no duplicate logic (`[ERR_OVERLAP]`).

## 4. ARCHIVE (tree of stepping stones) [DGM]
- Tiers form a **growing archive tree** T, seeded at T0. Mutation samples parents by
  **best-belief Thompson sampling over role/task** [RQGM §3.1] — high-fitness,
  under-evaluated nodes prioritized.
- Archive rank = fitness = benchmark_score − (token_cost × λ) − drift_penalty.
- Baselines lacking the archive underperform (no "stepping stones") — ARK MUST retain
  the full archive, not just the tip.

## 5. CO-EVOLVING CRITIC (FRACTURE) — epoch-local stationarity [RQGM §3]
FRACTURE is a **population of adversaries** co-evolving with the task agents:
- **Epoch structure:** search is divided into epochs. Within an epoch ONE reviewer is
  **frozen**, supplying a stationary utility signal; utility changes only at epoch
  boundaries.
- **ε-best-belief (ε) swap gate:** at an epoch boundary a challenger replaces the
  incumbent **only if it statistically outperforms on a frozen ground-truth anchor**
  (CRAVE-style held-out set), with confidence 1−ε. Ties favor the incumbent (no
  needless erasure).
- **Failure mining (⟍):** every FRACTURE failure becomes a NEW test case in the Red
  Queen suite automatically [auto-harness]. The eval suite grows.

## 6. SELECTIVE ERASURE (⌁) [RQGM Def. §3.4]
On critic swap, only utility records validated **under the displaced reviewer** are
flagged `re-test`; all unrelated archive info is preserved. Order-independent when
multiple transitions trigger. Stale validation is never trusted.

## 7. CHECKPOINT SCHEDULE (⊞⧖) [RQGM §3.5]
Critic-swap permitted only at **exponentially spaced** generations 1,2,4,8,16,… (r=2).
Erasure cost is then O(r·log B) not O(B²) — bounded recovery, no asymptotic overhead
beyond standard archive search.

## 8. SELECTION & FATAL LOOP
- Skills passing FRACTURE ascend the tier pyramid.
- 3 consecutive FRACTURE failures → FATAL LOOP RECOVERY: demote `tier_3_archived`,
  log `[ERR_TERMINAL_*]`, clear cache, FORGE seed state.

## 9. DRIFT BOUND [Starlight-PNS]
FIELD scores `distance(current_state, SOUL)`. Breach for 3 gens → pause EAST, force
WEST until drift monotonic-decreases 2 gens.

## 10. SAFETY
- No step alters SOUL.md or disables FIELD.
- All generated code executes ONLY in a sandbox [DGM]. Host immune.
- Poisoned input quarantined at ingest; evolution never trains on it.
