---
procedure_id: "skill_promotion_pipeline"
type: "pipeline"
related_skills: ["hermes_verify_*.py", "safety_gate", "pyramid_walker"]
last_executed: "2026-08-19T00:00:00Z"
---

# Procedure: Skill Promotion Pipeline
## Purpose
Transition a skill from PROPOSAL → PRODUCTION through validation and hardening.

## Prerequisites
- Skill written in markdown schema with YAML frontmatter
- Hermes test harness exists (hermes_verify_[skill_id].py)
- SafetyGate available for provenance verification

## Steps
1. **Write Skill:** Create markdown file in appropriate pyramid tier
2. **Generate Tests:** Write hermes_verify_[skill_id].py with happy path, null, boundary, recursion traps
3. **Execute Tests:** Run pytest with 100% pass requirement
4. **Token Measurement:** Record token_cost from YAML frontmatter
5. **SafetyGate Scan:** Verify no unsanitized external strings
6. **Provenance Hash:** Generate SHA-256 of core logic block
7. **Threshold Check:** Verify >5% token reduction OR patched ERR_* taxonomy
8. **Tier Assignment:** Route to tier_0_apex, tier_1_active, or skill_repair/
9. **Watermark Application:** Add [YOUR_WATERMARK_SIGNATURE] + timestamp
10. **Registry Update:** Commit to SKILLHUB registry with provenance_hash

## Verification
- All tests pass (exit code 0)
- provenance_hash appended to YAML header
- Skill file location matches tier designation
- PYRAMID walker confirms valid tier placement

## Related Procedures
- `repair_triage_pipeline`
- `goal_dag_sync_pipeline`
