# Implementation Notes: MARKUS + VORPAL + Citadel

## Deviations
- The run ledger and Citadel recall were implemented as new additive modules rather than refactoring the original indexer, minimizing regression risk.
- The Citadel query/write boundary is a local Python bridge rather than MCP; MCP remains a later adapter because the contract needed verification first.
- MARKUS runtime was started as a tracked background process on loopback for verification; it was not installed as a service.

## Discovered edge cases
- MARKUS port 8128 was closed during inspection; runtime restoration is an operational prerequisite.
- Existing repositories contain unrelated uncommitted changes; selective staging is required.
- VORPAL has `CORE/` modules but no `CORE/kernel.py`; root-level runtime files and documented paths must not be assumed interchangeable.
- Citadel indexer currently combines indexing with an auto-commit write path; read-only recall work must not invoke commits.
- ARK has been fully absorbed into VORPAL as internal modes. Its runtime modules (`ark_redqueen_core`, `ark_sandbox`, `ark_goal_verifier`, `ark_security_scanner`) now live in `CORE/`, and its command deck/UI in `COMMAND/`. ARK's unique contributions — edge optimization (tunable inter-node weights), recursive self-improvement at two levels (task + meta), Red Queen critic co-evolution, glyph language for O(1) state, and Starlight-PNS drift judging — are patterns to evaluate for adoption into the MARKUS/VORPAL spine. The triad amendment (§7 of ARK SOUL) explicitly prohibits direct runtime/state sharing — exchange happens only via provenance-hashed, FUSE-gated git artifacts.

## Questions for review
- None blocking for the first vertical proof slice.

## Handoff summary
- Deviations: 3.
- Most likely revisit: MCP adapter and service supervision remain intentionally deferred after the local bridge/runtime proof.
- Edge cases: closed runtime port, pre-existing dirty trees, VORPAL path/documentation drift, Citadel auto-commit coupling, Windows path separators in test expectations.
- Verified: MARKUS health/status/SSE, RunLedger persistence/idempotency, Citadel recall/write guard, workspace parity, MARKUS 9/9 integration.
- Next session should read this file and `.hermes/plans/markus-vorpal-citadel-upgrade.md` first.
