# Autonomy Contract

## Autonomy mode

`full-within-boundaries` means the agent executes routine, reversible, and explicitly scoped work without pausing for confirmation. It does not grant permission to cross security, destructive, external-publication, deployment, credential, or live-service boundaries.

High-risk actions require explicit operator scope naming the target, operation, time window, resource limits, and verification plan. Full-autonomy preference alone is not high-risk scope. If any scope element is absent, prepare the manifest and stop before mutation.

Child agents and scheduled jobs inherit only the manifest's explicit scope; they may not widen targets, permissions, duration, resources, or side effects. A child must return evidence to the parent, and the parent must verify it before reporting completion.

## Risk classes

- **Low**: read-only inspection, local analysis, deterministic validation, reversible local file creation within the declared workspace.
- **Medium**: local edits, scheduled jobs, background processes, queue dispatch, or changes that are reversible but can consume resources or affect other agents.
- **High**: deletion, reset, credential/auth changes, external writes, publishing, deployment, live-service changes, or broad repository mutations.

## Stop conditions

Stop and report when:

- the target repository, remote, service, account, or deployment target is ambiguous;
- authentication or authorization is required;
- a secret would need to be read, copied, typed, logged, or persisted;
- verification fails after bounded recovery;
- a mutation would destroy unrelated work or evidence;
- a live service would be restarted, altered, exposed, or killed without explicit scope;
- a self-modification lacks a baseline, mutation boundary, isolated work area, rollback procedure, or measurable gate.

## Retry policy

Retry only transient failures, at most three times, with increasing delay and a prerequisite re-check. Never retry suspected no-ops blindly. Preserve the first failure in the run report and Citadel record.

## Manifest minimum

A valid manifest identifies `run_id`, literal operator intent, target layers, ordered actions, preconditions, verification, rollback, success criteria, and stop conditions. Every mutation must name an observable, expected result, timeout, and persistence/no-op check.

## Handoff envelope

Cross-layer dispatch includes:

```yaml
goal_id: <stable goal>
task_state: <done, remaining, blocked>
expected_next_action: <receiving agent action>
source_run_id: <origin run>
receipt_id: <if available, otherwise N/A>
```

Never copy private payloads into broad-context reports; transmit only the minimum necessary metadata. Evidence, receipt IDs, hashes, and ledger updates may be reported as `N/A` or `UNAVAILABLE` when the corresponding operation did not actually produce them; never invent them.
