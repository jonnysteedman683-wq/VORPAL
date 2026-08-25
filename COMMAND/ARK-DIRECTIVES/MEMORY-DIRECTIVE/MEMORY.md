# MEMORY DIRECTIVE
**Binding law for how the ARK vessel remembers, recalls, and forgets.**

## 1. PURPOSE
Memory is continuity. Without durable, O(1)-addressable memory, every cycle
restarts from zero — death for a recursive kernel.

## 2. STORAGE TIERS (flat-file, source-of-truth)
| Tier | Path | Rule |
|------|------|------|
| Core | `ARK-OBJECTIVES/GOALS/GOALS.md` | DAG of goals + status |
| Ledger | `ARK-LANGUAGE/` + skill files | append-only ideas |
| State | skill YAML `watermark`/`generation` | per-artifact lineage |
| Cache | in-context only | NEVER trusted as truth |

## 3. ARCHIVE AS POPULATION MEMORY [ADOPTED: DGM/RQGM]
The skill tiers ARE the vessel's working memory:
- `tier_1_active` / `tier_2_stagnant` = the sampleable **archive** EVOLUTION draws
  parents from. Archive rank = fitness (benchmark − tokenλ − drift).
- Mutation samples high-fitness parents (open-ended evolution).

## 4. RECALL PROTOCOL
1. FIELD checks flat files first (O(1) index).
2. Context cache confirms only, never sources.
3. If capability exists in `tier_1_active`+, FORGE MUST reuse — regeneration is
   `[ERR_OVERLAP]`.

## 5. SELECTIVE ERASURE [ADOPTED: RQGM]
When the incumbent FRACTURE critic is displaced (ε-BB swap), every record validated
under the old critic is **re-tested**, not blindly trusted. Dependent learnings are
"erased" (re-derived). This prevents silent decay of validation integrity.

## 6. FORGETTING (controlled decay)
- Stagnant skills demote after a time threshold.
- Archived skills retained but inert; REVIVABLE.
- Permanent deletion forbidden except by human directive or FATAL LOOP RECOVERY.
- IDEAS ledger append-only: marked `[IMPLEMENTED]`, never erased (audit trail).

## 7. PROVENANCE & INTEGRITY
- Every write carries SHA-256 + watermark.
- Recall verifies hash before trust. Corrupted memory quarantined, not used.

## 8. CROSS-CYCLE PERSISTENCE
All truth on disk. A fresh process reads GOALS + skills and resumes mid-generation.
