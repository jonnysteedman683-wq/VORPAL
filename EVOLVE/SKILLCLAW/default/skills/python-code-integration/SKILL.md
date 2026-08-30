---
name: python-code-integration
description: "Integrate external code: path handling, imports, provenance."
version: "1.0.0"
author: VORPAL
license: MIT
created: 2026-08-28
metadata:
  hermes:
    tags: [python, code-reuse, sys-path, msys, imports, integration]
    related_skills: [python-script-verification, stealable-code-recon]
---

# Python Code Integration

## When to Use

- Integrating stolen/external Python modules into a project
- Building `sys.path` dynamically to import from sibling directories
- Handling MSYS/Cygwin path mangling on Windows
- Setting up graceful degradation for optional dependencies
- Establishing code provenance for reused code

## Steps

### 1. Build paths with `os.path`, not `Path.resolve()`

In MSYS/Cygwin environments, `Path(__file__).resolve().parent` produces broken
paths like `C:\c\Users\...` that fail `os.path.exists()` silently. Always use
`os.path` for building module paths:

```python
import os
_mod_dir = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_mod_dir)
sys.path.insert(0, os.path.join(_parent, "VORPAL", "CORE"))
```

NOT: `sys.path.insert(0, str(Path(__file__).resolve().parent / "CORE"))` — this
produces `C:\c\Users\...` and the import fails with `ModuleNotFoundError` even
when the directory exists.

### 2. Add the PARENT dir to `sys.path`, not the package dir

When importing a package, add its parent directory to `sys.path`, not the
package directory itself:

```python
# CORRECT
sys.path.insert(0, "/VORPAL/CORE")
from llm_circuit_breaker import CircuitBreaker

# WRONG
sys.path.insert(0, "/VORPAL/CORE/llm_circuit_breaker")
# Python looks for /VORPAL/CORE/llm_circuit_breaker/llm_circuit_breaker/__init__.py
```

### 3. Use relative imports inside the package

When a package is loaded via `sys.path` insert of its parent, the package's
`__init__.py` must use relative imports:

```python
# CORRECT — relative imports
from .breaker import CircuitBreaker
from .predicates import anthropic

# WRONG — absolute imports fail when loaded via sys.path insert
from llm_circuit_breaker.breaker import CircuitBreaker
```

### 4. Integrate with graceful degradation

Never make runtime depend on a stolen import — the system must boot without it:

```python
try:
    from llm_circuit_breaker import CircuitBreaker, BreakerConfig, predicates
    _HAS_BREAKER = True
except Exception:
    _HAS_BREAKER = False
```

Use `_HAS_BREAKER` guards and keep the original logic as fallback.

### 5. Expose config via env vars

Make stolen module behavior tunable without code changes:

```python
import os
if _HAS_BREAKER:
    _brain_breaker = CircuitBreaker(BreakerConfig(
        failure_threshold=int(os.environ.get("MARKUS_CB_THRESHOLD", "3")),
        recovery_timeout_s=float(os.environ.get("MARKUS_CB_RECOVERY_S", "30.0")),
        half_open_max_calls=1,
    ))
```

### 6. Watermark stolen code for provenance

Add `[◈VORPAL◈]` watermarks to docstrings and file headers:

```python
"""
[◈VORPAL◈] Adapted from MukundaKatta/llm-circuit-breaker-py (MIT).
Thread-safe Closed/Open/HalfOpen state machine for provider-aware routing.
"""
```

## Pitfalls

- **MSYS path mangling**: `Path.resolve()` produces `C:\c\...` — use `os.path.abspath`
- **Absolute imports in stolen packages**: Use relative imports (`.breaker`) when the package is loaded via `sys.path` insert
- **Package dir vs parent dir on path**: Add parent dir, not package dir
- **Hard dependency on stolen code**: Always guard with `_HAS_X = True/False`
- **Missing env-var config**: Expose thresholds via env vars, not hardcoded

## Verification

```bash
# Test the import works
python -c "import sys; sys.path.insert(0, '<parent>'); from <pkg> import <Thing>; print('OK')"

# Test graceful degradation
python -c "import <module>; print(f'breaker available: {module._HAS_BREAKER}')"

# Test the full integration
python -m py_compile <integrated_module>.py
```
