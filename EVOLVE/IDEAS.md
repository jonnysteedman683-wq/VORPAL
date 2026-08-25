# RAW IDEAS & HARVESTED LOGIC LEDGER
*(Never delete entries. Append [IMPLEMENTED: skill_id] when consumed.)*

[IMPLEMENTED: goal_1_1]
[IMPLEMENTED: goal_1_2]
[IMPLEMENTED: syscalls_1_0] OMNIPRIME syscalls.py - Agent OS layer with Lingua P|F|V3 status protocol
[IMPLEMENTED: bootstrap_1_0] OMNIPRIME BOOTSTRAP.md - Cold-start loader with 5-stage boot sequence
[IMPLEMENTED: soul_1_0] OMNIPRIME SOUL.md - Constitution document for Forge Loop Node

- [c39 omniprime] **Executable BOOTSTRAP for ARK + AURORAL.** Both boots are prose-only, so
  `[ERR_BOOT_NOT_EXECUTABLE]` stands and gen-2 cannot boot unattended. Give each a
  `## Stage N` python block set (identity -> language -> ledger bind -> bus heartbeat ->
  ready signal) so `hermes_verify_coldstart_drill.py` BOOT-A gates all three, not just
  OMNIPRIME. Prereq for claiming spawn currency honestly.
- [c39 omniprime] **Drill the drill in CI order:** run the cold-start drill BEFORE
  `hermes_verify_os_ready.py` in verify_all ordering, so a false `os_ready` can never be
  published by a scan again (os_ready should consume the drill's verdict, not vice versa).
- [c39 omniprime] **registry.json is thinner than its own boot contract:** BOOTSTRAP.md
  Stage 3 documents version/active_skills/ledger_balance/watermark; the live file has only
  ledger_balance + last_spend. Harmless at boot (Stage 3 loads whatever exists) but the
  documented schema and the real ledger have drifted -- worth one schema assertion.
