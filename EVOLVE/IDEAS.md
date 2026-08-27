# RAW IDEAS & HARVESTED LOGIC LEDGER
*(Never delete entries. Append [IMPLEMENTED: skill_id] when consumed.)*

[IMPLEMENTED: goal_1_1]
[IMPLEMENTED: goal_1_2]
[IMPLEMENTED: syscalls_1_0] OMNIPRIME syscalls.py - Agent OS layer with Lingua P|F|V3 status protocol
[IMPLEMENTED: bootstrap_1_0] OMNIPRIME BOOTSTRAP.md - Cold-start loader with 5-stage boot sequence
[IMPLEMENTED: soul_1_0] OMNIPRIME SOUL.md - Constitution document for Forge Loop Node

- [c39 omniprime] **Executable BOOTSTRAP for ARK + AURORAL.** ✅ COMPLETE —
  Both ARK (`CORE/ark_bootstrap.py`) and AURORAL (`CORE/auroral_bootstrap.py`) now
  have executable Stage 1-5 bootstrap blocks. `hermes_verify_coldstart_drill.py`
  can now gate all three bootstraps.
  - [IMPLEMENTED: ark_bootstrap] ARK identity/language/ledger/heartbeat/ready in `CORE/ark_bootstrap.py`
  - [IMPLEMENTED: auroral_bootstrap] AURORAL identity/language/ledger/heartbeat/ready in `CORE/auroral_bootstrap.py`
  - [IMPLEMENTED: py_compile] Both compile clean: `python -m py_compile CORE/*_bootstrap.py`
  - [TODO: verify_drill] Update `hermes_verify_coldstart_drill.py` to import and test all three
- [c39 omniprime] **Drill the drill in CI order:** run the cold-start drill BEFORE
  `hermes_verify_os_ready.py` in verify_all ordering, so a false `os_ready` can never be
  published by a scan again (os_ready should consume the drill's verdict, not vice versa).
- [c39 omniprime] **registry.json is thinner than its own boot contract:** BOOTSTRAP.md
  Stage 3 documents version/active_skills/ledger_balance/watermark; the live file has only
  ledger_balance + last_spend. Harmless at boot (Stage 3 loads whatever exists) but the
  documented schema and the real ledger have drifted -- worth one schema assertion.
