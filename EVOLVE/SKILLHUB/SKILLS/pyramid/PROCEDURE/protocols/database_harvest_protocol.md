---
procedure_id: "database_harvest_protocol"
type: "protocol"
related_skills: ["harvest_sanitizer", "safety_gate", "omni_swarm_adapter", "neurointent_types"]
last_executed: "2026-08-19T00:00:00Z"
---

# Procedure: Database Harvest Protocol
## Purpose
Systematically extract reusable code patterns from existing databases (Hermes skills, OMNIBUS, ARISE, SOUL.md) for integration into OMNICORE systems.

## Prerequisites
- Access to Hermes profile skills directory
- Read access to AEGIS/OMNIBUS/ARISE codebases
- SafetyGate verification available
- IDEAS.md ledger writable

## Steps
1. **Inventory Phase**: Catalog all available databases/repos
   - Hermes profile: `~/hermes/profiles/omnicore-base/skills/`
   - OMNIBUS: `omnicore_adapter.ts`, `omni_swarm_adapter.ts`
   - ARISE: brain modules, genome patterns
   - SOUL.md: self-ID and watermark rules
   - MARKUS-OS: resilience patterns, mesh protocols

2. **Pattern Mapping**: Identify stealable patterns per domain
   - **Routing**: omni_swarm_adapter.ts → adaptive_model_selector
   - **Persistence**: markus_db.ts → persistent_state_store.py
   - **Monitoring**: health_watchdog.ts → health_watchdog.py
   - **Self-ID**: SOUL.md dual-dice → idea_engine.py
   - **Circuit Break**: AEGIS circuit.ts → circuit_breaker.py

3. **Extraction Phase**: Pull AST-isolated logic from each source
   - Strip comments and metadata
   - Extract only functional logic
   - Tag with source attribution

4. **Sanitization Phase**: Run through SafetyGate
   - Injection scrub
   - Provenance hash generation
   - Dependency verification

5. **Quarantine Phase**: Write to IDEAS.md with attribution
   - Format: `[IDEA] pattern_name → [STOLE FROM: filepath]`
   - Mark as `[APPROVED: target_skill_id]` when integrated

6. **Integration Phase**: Apply to target skill
   - Update skill with harvested logic
   - Generate new provenance hash
   - Run hermes_verify tests

## Verification
- All harvested patterns pass SafetyGate checks
- No circular imports or conflicting dependencies
- Token cost does not increase by >5%
- Attribution properly recorded in IDEAS.md

## Related Procedures
- `steal_first_pipeline`
- `skill_promotion_pipeline`
