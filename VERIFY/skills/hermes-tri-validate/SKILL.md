---
name: hermes-tri-validate
description: Triad co-evolution verification — cross-audit and self-audit loop.
category: devops

## Hermes Tri-Validate — Triad Co-Evolution Verification Loop

### Trigger
When running inquisitor cycles across the ARK → OMNIPRIME → AURORAL triad
to verify that all three profiles are mutually consistent and all harnesses pass.

### Triad Topology

```
ARK (orchestrator) → dispatches goals, manages cron schedules
  ↓ owns ↓
AURORAL (backend) → DAG manager, execution & repair
  ↓ owns ↓
OMNIPRIME (forge) → workspace backend, skill evolution
  ↓ owns ↓
ARK (cycle complete)
```

### The Inquisitor Cycle

```python
def run_inquisitor_cycle(target_root: Path, profile: str = "auroral"):
    """
    Phase 1: Scan claims ledger (registry.json) for stale/verified/degraded
    Phase 2: Run all verification harnesses in target
    Phase 3: Cross-check claims vs harness results
    Phase 4: Dispatch report to target's inbox

    Returns: dict with summary, claims, harness_results
    """
    # 1. Load registry
    reg = json.loads((target_root / "registry.json").read_text())

    # 2. Extract claims from registry
    claims = extract_claims(reg)  # {id, text, status, stale_low}

    # 3. Run harnesses
    harness_results = run_all_harnesses(target_root)

    # 4. Audit claims against harness results
    stale = [c for c in claims if c["stale_low"]]
    verified = [c for c in claims if c["verified"]]
    degraded = [c for c in claims if c["degraded"]]

    summary = {
        "total_claims": len(claims),
        "verified": len(verified),
        "degraded": len(degraded),
        "stale_low": len(stale),
        "harnesses_run": len(harness_results),
        "all_pass": all(r["exit_code"] == 0 for r in harness_results),
    }

    return {"summary": summary, "claims": claims, "harness_results": harness_results}
```

### Cross-Profile Target Resolution

```python
def resolve_target(profile: str) -> Path:
    """Map profile name to workspace root."""
    if profile == "omniprime":
        return (AURORAL_ROOT / ".." / "OMNIPRIME").resolve()
    elif profile == "ark":
        return (AURORAL_ROOT / ".." / "ARK").resolve()
    else:  # "auroral" — self
        return AURORAL_ROOT
```

### Self-Audit vs Cross-Audit

| Mode | Target | Expected | Command |
|------|--------|----------|---------|
| Self-audit | AURORAL | 59 claims, 18 stale_low | `python3 looper/auroral_looper.py` |
| Cross-audit | OMNIPRIME | 37 claims, 0 stale | `python3 looper/auroral_looper.py --target ../OMNIPRIME` |

### Dispatch Report Pattern

```python
def dispatch_verification_report(report: dict, to_profile: str):
    """Send verification report as a packet to another profile's inbox."""
    pkt = {
        "id": Path(__file__).stem + "_" + datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8],
        "ts": _now(),
        "from": "auroral",
        "to": to_profile,
        "type": "VERIFICATION_REPORT",
        "payload": report,
        "status": "pending",
    }
    inbox = BUS / f"inbox_{to_profile}"
    inbox.mkdir(parents=True, exist_ok=True)
    path = inbox / f"{pkt['id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pkt, f, indent=2)
```

### Verification Gate

```
Phase 3: Epistemic Verification Gate
- No file marked [IMPLEMENTED] in GOALS.md without:
  1. PASSING AST check (python -m py_compile)
  2. GREEN hermes_verify_*.py harness
```

### CLI Flags

```bash
# Self-audit
python3 looper/auroral_looper.py

# Cross-audit OMNIPRIME
python3 looper/auroral_looper.py --target ../OMNIPRIME

# Run all harnesses only
python3 looper/auroral_looper.py --verify

# Run single harness
python3 looper/auroral_looper.py --harness hermes_verify_auroral_scaffold.py

# Inbox mode (consume packets from another profile)
python3 looper/auroral_looper.py --inbox --target omniprime
```

### Full Triad Run

```
1. AURORAL self-audit → all harnesses green
2. AURORAL cross-audit OMNIPRIME → all harnesses green  
3. OMNIPRIME verify_upgrade.py → PASS
4. OMNIPRIME verify_all.py → 18/18 PASS
5. Dispatch verification report to OMNIPRIME inbox
6. Update: GOALS.md, NOTES.md, registry.json, TRIAD_INDEX.json
```

### Pattern Proved
The inquisitor cycle closes the loop: scan claims → run harnesses → audit
discrepancies → dispatch report. The key invariant: claims with `[IMPLEMENTED]`
tag must have green harnesses proving it. If OMNIPRIME evolves its structure,
AURORAL's cross-audit harness must adapt its path/watermark assumptions.
