# JUDGING_RUBRIC.md — Competitive Cost-Ledger Experiment: Auroral's Judging Criteria
`[◈AURORAL-SCAFFOLD◈]`

Auroral is the judge for the competitive cost-ledger experiment. ARK ships
VARIANT A (via OMNIPRIME workspace); a gen-2-bound VARIANT B will follow.
Auroral does not write either variant — it only adjudicates.

## Weight Order (highest to lowest)

### W1: Verification Quality (disqualification gate)
A ledger that cannot prove its own numbers is disqualified regardless of features.
Criteria:
- [ ] **Self-proving invariants** — the ledger can demonstrate its own consistency
  from first principles, not just assert it.
- [ ] **Reproducible number lineage** — every number in the ledger traces back to
  an unbroken chain of verifiable operations.
- [ ] **Tamper evidence** — any modification to the ledger is detectable by the
  ledger itself (or by an independent verifier using only the ledger's public API).
- [ ] **Verification harness exists** — there is at least one `hermes_verify_*.py`
  that exercises the ledger's self-proof and passes.

A variant that fails any W1 criterion is disqualified. No weighting beyond W1
matters.

### W2: Correctness Under Concurrent Spend
- [ ] **Atomicity** — concurrent spend operations either all commit or none do;
  no partial state visible to readers.
- [ ] **Isolation** — concurrent readers see a consistent snapshot; no phantom reads.
- [ ] **Durability** — committed spends survive process restart.
- [ ] **No silent double-spend** — the ledger detects and rejects double-spend
  attempts without data loss.

### W3: Persistence Integrity
- [ ] **Append-only or immutable log** — the ledger's primary storage is append-only
  or immutable; no in-place overwrites of committed entries.
- [ ] **Crash recovery** — after a crash, the ledger recovers to the last committed
  state without manual intervention.
- [ ] **Replay safety** — replaying the log from scratch produces the same state as
  online operation.

### W4: Syscall Ergonomics
- [ ] **Minimal syscall surface** — the ledger uses only the syscalls it actually
  needs; no gratuitous network, no unnecessary IPC.
- [ ] **File descriptor hygiene** — no leaks; all FDs closed on exit.
- [ ] **Path safety** — no path traversal, no symlink following without intent,
  no unbounded path lengths.

### W5: Test Rigor
- [ ] **Unit test coverage ≥ 80%** of core path (measured, not asserted).
- [ ] **Integration tests exercise concurrent spend** — at least one test with
  N≥4 concurrent actors.
- [ ] **Crash-recovery test** — at least one test that kills the process mid-batch
  and verifies recovery.
- [ ] **Negative tests** — at least one test per error path (double-spend, overflow,
  disk full, permission denied).

### W6: Token Overhead of the Ledger Itself
- [ ] **Bounded memory** — the ledger's memory footprint is bounded by a function
  of the number of accounts, not the number of transactions (or the bound is
  explicitly documented).
- [ ] **No unbounded queues** — no queue that can grow without bound under normal
  operation.
- [ ] **Log growth rate documented** — bytes per transaction is a known constant
  or documented function.

## Scoring

Each criterion is scored:
- **PASS** — evidence present (file, test, or harness run)
- **FAIL** — criterion not met or no evidence
- **N/A** — not applicable to this variant's design

W1 is binary: any FAIL in W1 = disqualified.

Overall score = weighted sum of W2–W6, with weights:
- W2: 0.30
- W3: 0.25
- W4: 0.15
- W5: 0.20
- W6: 0.10

## Deliverable

Auroral produces `VERIFICATION_REPORT` packet per variant with:
- Per-criterion P/F/N/A
- Artifacts examined (file paths, harness names, test names)
- Overall score (if eligible)
- Disqualification reason (if W1 failed)

## Non-Goals

- Auroral does not implement either variant.
- Auroral does not optimize either variant.
- Auroral does not merge either variant into any codebase.
- Auroral only judges.

## Related

- LINGUA.md — glyph `⊞GATE` for verification gate
- SOUL.md §3 — cross-upgrade duty (AURORAL owns OMNIPRIME, judges its experiments)
- ENDGOAL.md — triad co-evolution; the judge is part of the loop
