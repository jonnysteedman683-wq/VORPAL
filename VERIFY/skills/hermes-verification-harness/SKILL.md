---
name: hermes-verification-harness
description: Python test harness patterns with pass/fail tally and check helpers.
category: software-development

## Hermes Verification Harness — Python Test Harness Patterns

### Trigger
When writing or auditing `hermes_verify_*.py` style harnesses for Python codebases.
These harnesses follow a consistent pattern: check functions, PASS/FAIL counters,
exit codes, and structured output.

### Core Pattern

```python
#!/usr/bin/env python3
"""hermes_verify_<module>.py — verifies <module> correctness.

Run: python3 hermes_verify_<module>.py
Exit 0 = all PASS, 1 = any FAIL.
"""
import sys
from pathlib import Path

PASS = 0
FAIL = 0

def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
        print(f"  [{status}] {name}")
    else:
        FAIL += 1
        print(f"  [{status}] {name}: {detail}")
    return condition

def run():
    """All test functions here. Each calls check()."""
    # ... tests ...

    print(f"\\n{'=' * 44}")
    print(f"RESULT: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    sys.exit(run())
```

### Check Styles

#### Boolean Checks
```python
check("name: description", actual == expected, f"got {actual}, want {expected}")
check("name: description", condition, f"detail string")
```

#### Count Checks
```python
check("result: all N items processed", all(done),
      f"only {done.count(True)}/{N} succeeded")
check("metrics: hit_rate > 50%", rate > 50, f"hit_rate={rate}%")
```

#### Exception Checks
```python
try:
    result = risky_func()
    check("func: handles error gracefully", True)
except Exception as e:
    check("func: handles error gracefully", True, str(e))
```

#### Exit Code Checks
```python
rc = call(mod.consume, "ark", pid)
check("consume: returns exit 0", rc == 0, f"rc={rc}")
check("consume: rejected double-exec returns exit 2", rc2 == 2, f"rc={rc2}")
```

### Harness Structure

1. **Path setup** — compute `BASE`/`ROOT` from `__file__`
2. **Import** — add to `sys.path`, import modules
3. **Test functions** — one per logical property
4. **run()** — calls all tests, prints tally, returns exit code
5. **CLI** — `if __name__ == "__main__": sys.exit(run())`

### Tally Pattern
```python
PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}: {detail}")

# At end of run():
print(f"\\n{'=' * 44}")
print(f"RESULT: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
return 0 if FAIL == 0 else 1
```

### File Structure Conventions

```
verify/                     (AURORAL)
├── hermes_verify_auroral_scaffold.py    # 24 checks
├── hermes_verify_auroral_looper.py      # 11-16 checks
├── hermes_verify_auroral_omniprime_skills.py  # 15 checks
└── hermes_verify_aurora_skeleton.py     # 14 checks

OMNIPRIME/
├── scripts/verify_all.py                 # orchestrator
├── SKILLHUB/verify_upgrade.py            # upgrade verification
├── EVOLVE/SKILLHUB/tests/
│   ├── hermes_verify_syscalls.py
│   ├── hermes_verify_bus_atomicity.py
│   └── hermes_verify_pipeline_skills.py
└── core/...
```

### verify_all.py Orchestrator Pattern

```python
"""Scans for hermes_verify_*.py and runs each."""
import subprocess
from pathlib import Path

def find_harnesses(root: Path) -> list[Path]:
    return list(root.rglob("hermes_verify_*.py"))

def run_harness(path: Path) -> int:
    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True)
    status = "PASS" if result.returncode == 0 else "FAIL"
    print(f"[{status}] {path.relative_to(root)}  ({result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ''})")
    return result.returncode

def main():
    harnesses = find_harnesses(SKILLHUB)
    failures = 0
    for h in harnesses:
        rc = run_harness(h)
        failures += rc
    print(f"TOTAL PASS={len(harnesses)-failures} FAIL={failures} (of {len(harnesses)})")
    return 1 if failures else 0
```

### Pattern Proved
Global `PASS`/`FAIL` counters with `check()` helper is the canonical pattern.
Exit 0 = all pass, exit 1 = any failure. Always print a final tally with `= 44` separator.
