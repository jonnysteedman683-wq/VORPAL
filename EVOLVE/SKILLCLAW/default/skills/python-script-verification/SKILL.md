---
name: python-script-verification
description: >-
  Python dev pitfalls: py_compile, MSYS paths, imports, test-compat.
license: MIT
version: "1.0.0"
compatibility: Python 3.11+, Windows/MSYS, Linux, macOS
metadata:
  author: Hermes Agent
  category: software-development
  tags: ["python", "verification", "cross-platform", "msys", "syntax", "py_compile"]
---

# Python Script Verification

## When to Use

Use when:
- Writing a Python script that will be run repeatedly (CLI tool, automation engine, verification script)
- Script will run on Windows with MSYS2/Cygwin bash
- Script needs to be syntax-validated before use
- Script handles file paths that may come from shell environment variables or command substitution

## Steps

### 1. Write the script

Standard Python script structure:
- `from __future__ import annotations` for forward references
- Type hints where useful
- CLI via argparse or click
- Main guard: `if __name__ == "__main__"`
- Errors as custom exception classes inheriting from a base

### 2. Syntax-check before trusting

```bash
python3 -m py_compile script.py && echo "SYNTAX OK"
```

Catches syntax errors (unclosed strings, missing colons, indentation errors, duplicate arguments) without executing the script. Always run this before trusting a newly written script.

### 3. Handle cross-platform paths

When a script receives paths from MSYS2/Cygwin bash (e.g., `$PWD`, `$(pwd)`, or env vars), the path may be in MSYS format (`/c/Users/...`) which Python's `Path` resolves differently on Windows.

See `references/msys-path-pitfall.md` for the full case and fixes.

**Quick rule**: prefer inline Python with explicit `Path(r"C:\...")` over passing paths through MSYS bash variables. If you must receive paths from bash, resolve them in Python before use.

### 4. Run and verify

- Execute with expected inputs
- Check exit code
- Verify outputs against expectations
- Clean up temp files

## Pitfalls (read on trigger)

The deep-dive failure ledger — double-triple-quote syntax, AST
docstring changes, overflow guards, export/import schema mismatch,
PYTHONPATH venv shadowing, pure-function side effects, signed-delta
inversion, fuzzy-patch splicing, heredoc escape normalization,
hostname-baked tests, missing DB methods — lives in
`references/deep-pitfalls.md`. Load it when a verification script or
harness misbehaves. The core steps and quick rules stay above.

## Verification Checklist

- [ ] `py_compile` passes with no syntax errors
- [ ] Script runs with `--help` or equivalent and produces expected output
- [ ] Cross-platform path handling tested with known MSYS paths
- [ ] Edge cases (empty input, missing files, invalid args) handled gracefully
- [ ] Custom exceptions have clear messages
- [ ] CLI argument parsing works (argparse/click)
- [ ] Idempotency markers or guards where relevant

## References

- `references/msys-path-pitfall.md` — MSYS/Cygwin path resolution case from this session
- `references/syntax-pitfalls.md` — docstring and syntax trap reference

## Non-package module import (absorbed from `python-non-package-import`)

Load a module from an arbitrary file path that isn't on `sys.path` (verification harnesses, workspace-level modules imported from tests):

```python
import importlib.util
from pathlib import Path

def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
```

Example harness usage: `ROOT = Path(__file__).resolve().parent.parent.parent` then
`syscalls = load_module("syscalls", ROOT / "syscalls.py")`. Full worked example: `references/syscalls-import-example.md`.

## Test/module compatibility debugging (absorbed from `python-test-compatibility-debugging`)

When tests fail with `ImportError`/`TypeError` on functions that "should exist", the root cause is an API-surface mismatch between the test and the module — not a one-line problem.

6-step flow:
1. **Read the test** to extract the expected API surface (names, signatures, return shapes).
2. **Read the module** to see what's actually implemented (renamed functions, missing functions, signature drift).
3. **Bridge the gap**: Option A add a wrapper alias (`def count_tokens(...): return token_count(...)`); Option B add default parameters for divergent call signatures (`def detect_bloat(current_tokens=None, prior_tokens=None, ...)`).
4. **Match state file paths**: test `setUp` must clean the SAME file the module writes (e.g. `token_ledger.json` vs `skill_token_usage.jsonl` mismatch leaks stale data).
5. **Fix the two high-recurrence pitfalls**:
   - `hashlib.sha256(str)` → `TypeError: Strings must be encoded before hashing`. Fix: `hashlib.sha256(json.dumps(rec, sort_keys=True, default=str).encode("utf-8")).hexdigest()`.
   - JSONL newline bug: `f.write(line + "\n")` writes a literal backslash-n → the file reads as ONE line and appears to hold 1 entry. Fix: `f.write(line + "
")` (real newline).
6. **Verify with the full suite** (`pytest tests/ -v --tb=short`), not just the previously-failing tests.

Full session transcript of the 15-test fix: `references/session-notes.md`.

