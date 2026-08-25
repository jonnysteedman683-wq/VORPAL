---
procedure_id: "mutation_evaluation_loop"
type: "loop"
related_skills: ["mutation_engine", "test_harness_builder", "token_compressor"]
last_executed: "2026-08-19T00:00:00Z"
---

# Procedure: Mutation Evaluation Loop
## Purpose
Select, mutate, and evaluate an existing skill for continuous improvement.

## Prerequisites
- At least one skill in tier_1_active exists
- Watermark on target skill differs from current signature

## Steps
1. Scan tier_1_active skills for stagnation (watermark age > threshold)
2. If stagnant, select oldest skill for mutation
3. Measure current token_cost before mutation
4. Apply mutation (optimize logic, reduce branches, compress tokens)
5. Write updated skill with new watermark signature
6. Execute hermes_verify_[skill_id].py test harness
7. Measure new token_cost
8. If token_reduction > 5% OR ERR_* patched → accept
9. Otherwise → reject and log as [ERR_STAGNATION]

## Verification
- New test harness passes all assertions
- Token cost does not exceed 105% of previous value
- Watermark updated to current signature

## Related Procedures
- `triad_co_evolution_loop`
- `decay_detection_loop`
