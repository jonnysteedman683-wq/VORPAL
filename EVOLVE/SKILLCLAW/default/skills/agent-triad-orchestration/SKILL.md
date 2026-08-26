---
name: agent-triad-orchestration
version: 1.0.0
author: ox-alpha
license: MIT
metadata:
  hermes:
    tags: [multi-agent, orchestration, cron, packet-bus, recursion]
    related_skills: [loop-creation, hermes-cron-patterns, verify-after-mutation]
description: Use for multi-Hermes-profile worker rings, agent loops.
---

# Agent Triad / Multi-Profile Orchestration

Class-level skill for running N Hermes profiles as an orchestrated worker ring
that mutates real workspaces, gets graded by evidence, and can eventually
self-replicate. Distilled from the live TRIAS system (ARK/OMNIPRIME/AURORAL).

## When to use
- User wants several Hermes profiles to work on each other's projects in a cycle
- User wants scheduled autonomous agents that mutate codebases and get graded
- User wants recursive/spawning agent structures ("the loop makes another loop")

## Core architecture (proven working)
1. **Hub folder** on Desktop holds shared tooling: indexer, grader, protocol docs,
   staged souls. Neutral ground — no profile owns it; orchestrator writes reports there.
2. **Packet bus**: filesystem JSONL under `<workspace>/.hive/bus/inbox_<profile>/`.
   Commands: send/read/ack/events (+claim/steal for work stealing, cache for
   verified-artifact reuse). All state is files — any profile can inspect.
3. **Cyclic ownership**: profile X edits workspace Y, never its own. Every soul
   lists an explicit "you edit / you never edit" table plus an ownership graph.
4. **Heartbeat crons** per profile, STAGGERED minutes (e.g. 0,15,30,45 /
   5,20,35,50 / 10,25,40,55) so workers pipeline instead of colliding. Grade
   crons slot between waves (e.g. 12,27,42,57).
5. **Evidence grading**: an index script scans each workspace into normalized
   JSON (nodes, goals, verify-gate pass/fail, degradations). A grader diffs vs
   last cycle → verdict ASCEND/HOLD/DESCEND appended to that profile's SOUL
   ledger (append-only block delimited by HTML comments).
6. **Souls are constitutions + ledgers**: sections for Language protocol,
   Memory tiers (L1 bus free / L2 ledgers append-only / L3 grades
   orchestrator-only), Ownership, Standing orders, Main goals, Competitive rules.

## Force multipliers (each independently valuable)
- M1 batch packets: EXECUTE_GOAL_BATCH carries 3–5 ordered tasks, cap at 5.
- M2 staggered heartbeats: pipeline overlap, two grade windows/hour minimum.
- M3 earned autonomy: clean-streak unlocks self-dispatch from own backlog;
  one regression revokes it. Judge retro-audits self-dispatched work.
- M4 language inheritance: embed compressed shared vocabulary INTO workspaces
  (dialect file, syscalls speak signal codes, lesson-zero in bootstrap docs) so
  spawned agents speak natively. New tokens flow up for audit/merge.
- M6 job market: claim/steal commands with OS-level lock (msvcrt/fcntl) prevent
  double-execution; steal only pending packets.
- M7 model routing: per-task model_hints field; match model strength to task class.
- M8 result compounding: cache verified artifacts (hash path+mtime); consumers
  skip re-verification of CACHED entries.
- M9 sleep-time compute: cheap cron between grade windows mines ledgers for
  [ERR_*]/unverified claims and converts them to proposals; silent when quiet.

## Recursion (spawning child rings)
Spawn rights are EARNED: ≥10 clean gate cycles, cold-start drill (blank profile
bootstraps from kit alone), stable shared language, clean ledgers. Human approval
gate at EVERY generation boundary. Failed children archived, never deleted.
Success metric: TIME_TO_CLEAN per generation — compounding shows as shrinking time.

## Competitive experiment protocol (meritocracy builds)
- Competitors design ORIGINAL variants (no copying); epistemic profile judges
  via written rubric, weighting verification quality above features.
- Judge never competes; host never competes for the same build (conflict firewall).
- Winner becomes canonical; loser archived with lessons distilled to NOTES.md.
- Adversarial stress harness is built BEFORE judging: concurrency, corruption,
  overflow, escape attempts.

## Bus Inbox Processing Patterns (from AURORAL session 2026-08-23)

When a profile processes packets from its inbox (`--inbox` mode), four bugs routinely
compound. Each is small alone but together they cause cascading log spam, phantom
re-audits, and stale packet backlogs:

1. **Target profile not resolved from packet payload**: The looper defaults `target` to its
   own workspace root and never reads `payload.target_profile` to resolve the correct
   workspace. If a packet says "audit omniprime", the looper audits itself instead.
   FIX: resolve `target_profile` from the packet, map to the correct workspace root
   (e.g. `omniprime` → `../OMNIPRIME`), then run the inquisitor cycle against that root.

2. **Log dedup by full entry (timestamp included)**: `log_cycle()` appends
   `## <timestamp> | <action>\n<detail>` and dedups by checking if the *entire entry
   string* is already present. Since timestamps differ by 1 second, dedup never fires
   and the log explodes (observed: 425 lines from ~20 cycles, pruned to 18).
   FIX: dedup by `(action, detail)` signature ignoring timestamp.

3. **Packets never acked after processing**: The `--inbox` loop processes packets but
   never calls `ack()`, leaving them `pending` forever. Next scan re-reads and
   re-processes the same packets × log spam amplification.
   FIX: ack each packet after dispatch_verification_report completes.

4. **Verification report dispatched to hardcoded target**: `dispatch_verification_report`
   defaults to `to_agent="omniprime"` even when the packet came from a different source.
   FIX: dispatch to `pkt.get("from", "ark")` — the report goes back to whoever sent the
   directive, not a hardcoded downstream profile.

## Pitfalls (learned the hard way)
- Bus inbox processing: see section above — resolve target_profile from payload,
  dedup log entries by content signature (not timestamp), ack after dispatch,
  and dispatch verification reports to pkt.from() not a hardcoded target.
- NEVER inline JSON payloads in shell strings (apostrophes/parens cause exit-code-2
  silent failures). Call bus scripts via subprocess list args from Python.
- One-shot cron jobs (`once in 30m`) auto-disable after firing — recreate
  recurring ones with explicit cron expressions (`*/30 * * * *`, not "30m").
- `hermes cron create --repeat 0` yields "0/1" not infinite; fix via
  `hermes cron edit <id>` afterwards. CLI edit DOES accept schedule/model changes.
- Profile crons live in `AppData/Local/hermes/profiles/<p>/cron/jobs.json` —
  inspect directly when `hermes cron list` (default profile) isn't enough.
- Timezone bugs bite tests: utcnow() vs local strftime compare unequal dates.
  Always use local time consistently in journal/daily-file logic.
- Verify inbox readback after every bus send (`events` command) rather than
  trusting exit codes alone.
- Grading must be grounded ONLY in runnable harnesses — never self-grading;
  this is the anti-collapse anchor for any recursive scheme.

## References
- references/triad-case-study.md — full live-system walkthrough: file layout,
  actual schedules, soul section templates, recursion roadmap summary.
- references/triad-spawn-runbook.md — GEN-2 SPAWN RUNBOOK: naming rules (no dots), clone workflows, child binding kit architecture, dormancy lifecycle, and 8/8 verification checks.
- references/generational-fold-plan.md — GENERATIONAL FOLD: 3→6→9/12 expansion,
  per-triad hive memory (T1) → universal hive mind (T2, earned only after a
  triad reproduces), convergence fold protocol (freeze→distill→merge→
  re-baseline→boot gen N+1 at 3).
