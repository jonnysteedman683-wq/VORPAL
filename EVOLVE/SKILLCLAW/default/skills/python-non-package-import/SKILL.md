---
name: python-non-package-import
description: Import Python modules from any file path.
license: MIT
version: "1.0.0"
compatibility: Python 3.9+
metadata:
  author: Hermes Agent
  category: software-development
  tags: ["python", "importlib", "testing"]
---

# Python Non-Package Module Import

## When to Use

- Module file exists at known path but isn't in sys.path
- Building verification harnesses hermes_verify_*.py
- Importing workspace-level modules from tests

## Core Pattern

```python
import importlib.util
from pathlib import Path

def load_module(name: str, path: Path):
    """Load a module from arbitrary file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

## Example: Verification Harness

```python
#!/usr/bin/env python3
ROOT = Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("syscalls", ROOT / "syscalls.py")
syscalls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(syscalls)
```

## Path Resolution

From `EVOLVE/SKILLHUB/tests`: `ROOT = Path(__file__).resolve().parent.parent.parent`