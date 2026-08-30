# Implementation Plan: MARKUS + VORPAL + Citadel Operational Spine

## Overview
Upgrade the existing three-part system without replacing VORPAL's constitutional model: restore the MARKUS runtime, add durable typed run/event state, improve Citadel evidence-ranked recall, add a narrow provenance-bound Citadel interface, unify local/sandbox execution boundaries, and expose a local trace view.

## Constraints
- Preserve existing uncommitted user changes; stage only files intentionally changed by this effort.
- VORPAL remains the constitutional authority and source of truth for strategic state.
- MARKUS remains the operational runtime and router.
- Citadel remains human-readable Markdown/Git knowledge storage.
- Stdlib-first; no new dependency unless a focused requirement proves it necessary.
- No unrestricted file mutation, no automatic deployment, no destructive cleanup.

## Architecture Decisions
1. Use a shared RunRecord/event contract implemented first in MARKUS with SQLite persistence and JSON-safe records.
2. Use idempotent event append and checkpoint transitions so restart recovery can resume without replaying completed side effects.
3. Keep Citadel Markdown as the source of truth; build a deterministic ranked index before considering embeddings.
4. Expose Citadel through a narrow local HTTP boundary first; MCP remains an adapter after the contract is verified.
5. Represent execution as a workspace interface with LocalWorkspace and SandboxWorkspace adapters, reusing existing MARKUS sandbox code.
6. Treat VORPAL verification as a terminal gate and project trace/evidence into Citadel only after the gate passes.

## Ordered Task List

### Phase 1: Runtime foundation
- [x] Restore MARKUS server on loopback port 8128 without altering unrelated work.
- [x] Verify `/api/health`, `/api/status`, and `/api/stream` handshake.
- [x] Add a repeatable lifecycle smoke harness that does not kill unrelated processes.

### Phase 2: Durable execution and typed events
- [x] Add `markus_run_ledger.py` with typed dataclasses, SQLite schema, legal status transitions, append-only events, checkpoints, approvals, and artifact records.
- [x] Add focused tests for idempotency, restart recovery, invalid transitions, and JSON round-tripping.
- [x] Integrate run/event emission at the MARKUS request, routing, verification, and sync boundaries.

### Checkpoint A
- [x] py_compile changed Python files.
- [x] Focused run-ledger harness passes.
- [x] MARKUS API smoke passes.
- [x] Existing bridge and integration gates remain green.


### Phase 3: Citadel recall and controlled writes
- [x] Add deterministic evidence-ranked recall using section, heading, exact-term, recency, tag, and provenance signals.
- [x] Add focused recall tests using the existing MARKUS/VORPAL notes.
- [x] Add narrow local bridge operations for search and provenance-bound note writes.
- [x] Require `source_run_id`, reason, section allowlist, and provenance metadata for writes.
- [x] Ensure path traversal and arbitrary file mutation are rejected.

### Phase 4: Portable execution
- [x] Define a small workspace protocol.
- [x] Implement LocalWorkspace and SandboxWorkspace adapters around existing MARKUS behavior.
- [x] Add a focused parity harness: same safe command/input contract, distinct execution roots, explicit result records.

### Checkpoint B
- [x] Citadel recall returns ranked paths, scores, matched terms, and evidence metadata.
- [x] Citadel write boundary rejects missing provenance and traversal.
- [x] Local/sandbox parity harness passes.
- [x] Existing VORPAL harnesses remain green.

### Phase 5: Unified trace surface
- [x] Add a read-only MARKUS trace endpoint backed by the run ledger.
- [x] Add a compact trace HTML page showing run status, event timeline, and checkpoints.
- [x] Verify a synthetic run appears end-to-end without a model call.

### Phase 6: Ledger/documentation synchronization
- [x] Update the implementation plan with verified phase state.
- [ ] Append final verified deltas to authoritative VORPAL/MARKUS/Citadel ledgers.
- [ ] Run the complete relevant verification suite and inspect final diffs.


## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Existing autonomous MARKUS process changes files | High | Inspect process/git state before each write; stage only explicit paths. |
| MARKUS import graph has optional/missing modules | High | Start with py_compile and import smoke; avoid broad refactors. |
| Existing API clients depend on payload shapes | Medium | Additive endpoints and backward-compatible fields only. |
| Citadel indexer currently auto-commits | Medium | Separate read/index operations from explicit writes; never auto-commit during read tests. |
| SQLite event replay duplicates side effects | High | Idempotency keys and checkpoint-before-side-effect policy. |
| Architecture scope becomes too large | High | Complete one vertical slice per phase; stop at checkpoints if a gate fails. |

## Definition of Done
- MARKUS health/status/SSE are operational and independently verified.
- A run can be created, advanced, checkpointed, inspected, and resumed after process restart.
- Citadel recall is ranked and testable; writes are narrow and provenance-bound.
- Local and sandbox execution share one contract and pass parity checks.
- A trace can be read from one run ID across runtime, verification, and knowledge projections.
- Existing green gates remain green; failures are fixed or explicitly reported.

## First Proof Slice
Create a synthetic run through MARKUS's local API: receive -> route -> checkpoint -> verify-pass -> emit trace. The check must prove that the run ledger survives reopening its SQLite connection and that the trace endpoint returns the same run ID and ordered events.
