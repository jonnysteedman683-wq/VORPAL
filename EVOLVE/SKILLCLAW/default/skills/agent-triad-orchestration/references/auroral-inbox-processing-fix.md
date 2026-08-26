# AURORAL Inbox Processing Fix — Session 2026-08-23

## Context
AURORAL's `looper/auroral_looper.py` has an `--inbox` mode that processes pending
bus packets from the shared `.hive/bus/inbox_auroral/` directory. Three bugs caused
the Inquisitor loop to misbehave when processing ARK directives.

## Bug 1: Target profile not resolved
**Symptom**: When ARK sent a DIRECTIVE packet with `target_profile: "omniprime"`,
the AURORAL looper audited AURORAL_ROOT instead of OMNIPRIME.

**Root cause**: In `main()`, the `--inbox` branch used `target` (initialized to
`AURORAL_ROOT`) instead of reading the packet's `payload.target_profile` field.

**Fix**:
```python
# Before (broken):
report = run_inquisitor_cycle(target, pkt.get("payload", {}).get("target_profile", "unknown"))

# After (fixed):
target_profile = pkt.get("payload", {}).get("target_profile", "unknown")
if target_profile == "omniprime":
    audit_target = AURORAL_ROOT.parent / "OMNIPRIME"
elif target_profile == "auroral":
    audit_target = AURORAL_ROOT
else:
    audit_target = AURORAL_ROOT
report = run_inquisitor_cycle(audit_target, target_profile)
```

## Bug 2: log_cycle dedup spam
**Symptom**: VERIFICATION_LOG.md grew to 425 lines from ~20 inquisitor cycles.

**Root cause**: `log_cycle()` built entries with timestamps: `## <ts> | <action>\n<detail>`
and deduped by checking if the *entire entry string* was already present. Since each
call produced a unique timestamp, the dedup never fired.

**Fix**:
```python
# Before (broken):
entry = f"## {_now()} | {action}\n{detail}\n\n"
if entry in existing:
    return

# After (fixed):
entry = f"## {_now()} | {action}\n{detail}\n\n"
sig = f"| {action}\n{detail}"  # content signature without timestamp
if sig in existing:
    return
```

## Bug 3: Packets not acked
**Symptom**: All inbox packets remained `status: pending` after processing, causing
re-processing on every cycle run.

**Fix**: Added `_ack_inbox_packet()` function and call it after each packet is processed:
```python
def _ack_inbox_packet(packet_id: str) -> None:
    path = BUS_INBOX_AURORAL / f"{packet_id}.json"
    if not path.exists():
        return
    pkt = json.loads(path.read_text(encoding="utf-8"))
    pkt["status"] = "acked"
    pkt["acked_ts"] = _now()
    path.write_text(json.dumps(pkt, indent=2), encoding="utf-8")
```

## Bug 4: Verification report to hardcoded target
**Symptom**: `dispatch_verification_report` always sent to `omniprime`, even when
the packet originated from ARK.

**Fix**: Use `pkt.get("from", "ark")` as the dispatch target.

## Post-fix verification
All 4 harnesses pass:
- hermes_verify_auroral_scaffold.py: 24/24 PASS
- hermes_verify_auroral_looper.py: 11/11 PASS
- hermes_verify_auroral_omniprime_skills.py: 15/15 PASS
- hermes_verify_aurora_skeleton.py: 6/6 PASS
