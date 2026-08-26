# Syscalls.py Import Example

## Context

When verifying `syscalls.py` located at workspace root from a test harness in `EVOLVE/SKILLHUB/tests/`, direct import fails:

```
ModuleNotFoundError: No module named 'syscalls'
```

## Solution

```python
import sys
import importlib.util
from pathlib import Path

# Compute workspace root from test location
# tests -> SKILLHUB -> EVOLVE -> OMNIPRIME
ROOT = Path(__file__).resolve().parent.parent.parent

# Dynamic load of syscalls module
spec = importlib.util.spec_from_file_location("syscalls", ROOT / "syscalls.py")
syscalls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(syscalls)

# Now syscalls.verify(), syscalls.ledger_balance() etc. work
```

## Usage in Verification Harness

```python
#!/usr/bin/env python3
"""Hermes Verification: Syscalls v1.0"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("syscalls", ROOT / "syscalls.py")
syscalls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(syscalls)

def test_verify():
    result = syscalls.verify(Path(__file__))
    assert result in ("P", "V3")
    print("[PASS] verify()")

if __name__ == "__main__":
    test_verify()
    print("RESULT: PASS")
    sys.exit(0)
```