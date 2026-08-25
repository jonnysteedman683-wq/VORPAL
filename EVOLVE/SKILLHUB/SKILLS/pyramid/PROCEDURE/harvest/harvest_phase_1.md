---
procedure_id: "harvest_phase_1"
type: "harvest"
related_skills: ["auto_steal_engine", "thors_thorns_engine", "lingua_prima"]
last_executed: "2026-08-19T20:00:00Z"
---

# Procedure: Phase 1 Code Harvest

## Targets (from memory_context)
- **Hermes-Hive main repo:** 9 vitest files, 80 tests
- **Sentinel main repo:** 49 new tests (8 hardened paths)
- **OMNICORE-A1:** safety_gate.ts, cost_router.ts, event_bus.ts, tri_agentic_kernel.ts
- **OMNIBUB:** provider handshake patterns
- **markus_* repos:** router, AST cache, obsidian sync, resilience

## Steal Patterns
1. **Hermes-Hive:** Multi-model semantic routing, intent routing chains
2. **Sentinel:** Verification engine, outcome processing
3. **OMNICORE-A1:** Tri-brain stack, safety_gate intent timestamps
4. **Markus Router:** Model selection, fallback chains
5. **Markus AST Cache:** Predictive caching, LRU eviction

## Storage
- Stolen patterns → `LANGUAGE/dictionary/harvested_patterns.json`
- Procedures → `PROCEDURE/protocols/`
- Security hardening → `utilities/thors_thorns_engine.py` (already done)
- Routing → `utilities/adaptive_model_selector.py` (already done)

## Safety
- Run Thors/Thorns on all harvested code
- Scan for prompt injection, SSRF, path traversal, code injection
- Log to Obsidian daily journal
