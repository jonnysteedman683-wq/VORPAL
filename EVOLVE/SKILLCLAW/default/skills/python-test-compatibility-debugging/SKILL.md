---
name: python-test-compatibility-debugging
description: "Fix ImportError tests expecting APIs the module lacks."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [debugging, testing, python, error-handling, pytest]
    related_skills: [systematic-debugging, test-driven-development, autonomous-coding-workflow]
---

# Python Test Compatibility Debugging

## Overview

When a Python test suite fails with `ImportError` or `TypeError` on functions that
"should exist", the root cause is usually an API surface mismatch between the test
file and the module under test. This skill captures the debugging flow and two
high-recurrence Python pitfalls discovered while bridging test/module API gaps.

## When to Use

- Tests fail with `ImportError: cannot import name 'X' from 'module'`
- Tests call functions with a different signature than the implementation
- Test `setUp` cleans the wrong state file, causing cross-test contamination
- JSONL-based state storage silently loses entries

## The 6-Step Flow

### 1. Read the Test to Extract the Expected API Surface

Don't treat `ImportError` as a one-line problem. Read the full test file to understand:
- What functions are expected to exist
- What parameters they accept (positional vs keyword, defaults)
- What return value shape the assertions check

### 2. Read the Module to See What's Implemented

Compare the test's imports against the module's actual function names. Look for:
- Functions that exist under a different name (e.g. `tune_skill_edges` vs `tune_edge`)
- Functions missing entirely
- Signature differences (e.g. required positional args where the test passes `None`)

### 3. Bridge the Gap

**Option A: Add a wrapper.**
```python
def count_tokens(code: str) -> int:
    """Count tokens in code. Alias for token_count."""
    return token_count(code)
```

**Option B: Add default parameters for divergent call signatures.**
```python
def detect_bloat(current_tokens=None, prior_tokens=None,
                 threshold=0.2, threshold_percent=None):
    if current_tokens is None:
        # ledger-scan mode
        return get_bloat_records(threshold_percent or 10.0)
    # direct comparison mode (legacy)
    if prior_tokens is None or prior_tokens == 0:
        return False
    return (current_tokens - prior_tokens) / prior_tokens > threshold
```

### 4. Match State File Paths

Ensure the test's `setUp` cleans the same file the module writes to. A mismatch
(e.g. `token_ledger.json` vs `skill_token_usage.jsonl`) causes stale data to leak
between test classes.

### 5. Fix the Two High-Recurrence Pitfalls

#### hashlib.sha256 requires bytes (Python 3)

```python
# WRONG:
rec["hash"] = hashlib.sha256(json.dumps(rec, sort_keys=True)).hexdigest()

# CORRECT:
rec["hash"] = hashlib.sha256(
    json.dumps(rec, sort_keys=True, default=str).encode("utf-8")
).hexdigest()
```
**Symptom**: `TypeError: Strings must be encoded before hashing`

#### JSONL newline escaping bug

```python
# WRONG — writes literal backslash+n:
f.write(line + "\\n")

# CORRECT — writes a real newline:
f.write(line + "\n")
```
**Symptom**: `for line in f` reads the entire file as one line. The ledger
appears to store only 1 entry no matter how many `log_*` calls are made.
Downstream reads find 0 entries, causing `detect_bloat` to return `[]`
even when history exists.

### 6. Verify with Full Test Suite

```bash
pytest tests/ -v --tb=short
```
Run the entire suite, not just the previously-failing tests, to confirm the
compatibility layer doesn't introduce regressions.

## Checklist

- [ ] Read full test file to understand expected API surface
- [ ] Read module to identify what's implemented vs. expected
- [ ] Add missing functions as wrappers or implementations
- [ ] Use default parameters for divergent call signatures
- [ ] Match state file paths between tests and module
- [ ] Fix `hashlib.sha256` calls to use `.encode("utf-8")`
- [ ] Fix JSONL writes to use real `\n` newlines (not `\\n`)
- [ ] Run full test suite to confirm no regressions

## PITFALLS

| Symptom | Root cause | Fix |
|---------|------------|-----|
| `TypeError: Strings must be encoded before hashing` | `hashlib.sha256(str_input)` | Add `.encode("utf-8")` |
| JSONL file appears to hold only 1 entry | `f.write(line + "\\n")` writes literal `\n` | Use `"\n"` |
| `detect_bloat(None)` returns `[]` despite logged history | JSONL newline bug corrupts file | Fix newline + clean state files |
| `ImportError: cannot import name X` | Function not implemented in module | Add wrapper or implementation |
| `TypeError: missing 1 required positional argument` | Test passes `None` for a required arg | Add `=None` default |
| Cross-test contamination | Test setUp cleans wrong state file | Match exact filename |

## References

- [[Session notes from ARK debug session, 2026-08-20](/references/session-notes.md)] —
  Full transcript of the 15-test fix, including the exact diff and verification output.