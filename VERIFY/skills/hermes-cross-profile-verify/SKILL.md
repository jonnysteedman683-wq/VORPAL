---
name: hermes-cross-profile-verify
description: Orchestrate verification across ARK, OMNIPRIME, and AURORAL profiles.
category: devops

## Hermes Cross-Profile Verification Orchestrator

### Trigger
When running verification suites across multiple Hermes profiles or workspaces
that share a triad topology (ARK → OMNIPRIME → AURORAL).

### Prerequisites
- Each profile has its own `verify/` or `hermes_verify_*.py` harness directory
- OMNIPRIME has `scripts/verify_all.py` as the central orchestrator
- AURORAL has `looper/auroral_looper.py --verify` for self-audit

### Steps

1. **Compile all Python files** in each profile workspace:
```bash
cd AURORAL_ROOT && python3 -m py_compile $(find . -name "*.py" -not -path "*/__pycache__/*" -not -path "./.hive/*")
cd OMNIPRIME_ROOT && python3 -m py_compile $(find . -name "*.py" -not -path "*/__pycache__/*" -not -path "./.hive/*")
```

2. **Run individual harnesses** in each profile:
```bash
# AURORAL
python3 verify/hermes_verify_auroral_scaffold.py
python3 verify/hermes_verify_auroral_looper.py
python3 verify/hermes_verify_auroral_omniprime_skills.py
python3 verify/hermes_verify_aurora_skeleton.py

# OMNIPRIME
python3 SKILLHUB/verify_upgrade.py
python3 EVOLVE/SKILLHUB/tests/hermes_verify_syscalls.py
python3 scripts/hermes_verify_bus_atomicity.py
python3 scripts/verify_all.py
```

3. **Cross-audit** — AURORAL audits OMNIPRIME:
```bash
python3 looper/auroral_looper.py --target ../OMNIPRIME
```

4. **Verify results** — all must pass with exit code 0.

### Cross-Profile Gotchas

| Issue | Solution |
|-------|----------|
| Relative paths break on wrong CWD | Use `Path(__file__).resolve().parent` |
| Harness version checks hardcoded | Use `>=` or accept multi-value |
| Watermarks differ per profile | Accept `[◈AURORAL-SCAFFOLD◈]` OR `[OMNIPRIME-FORGE]` |
| Skill paths outside tier_1_active | Resolve from ROOT with candidate fallbacks |
| TOCTOU races in bus tests | Lock before `_locate()` |

### Pattern Proved
Cross-profile verification catches evolution mismatches: when OMNIPRIME upgrades
its registry structure, AURORAL's audit harness must adapt its assumptions.
