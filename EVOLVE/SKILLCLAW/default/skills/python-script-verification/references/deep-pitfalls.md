# Python script verification — deep-dive pitfalls

Load this file when a Python verification script or harness misbehaves
in one of the ways catalogued here. The core steps and quick rules
stay in `SKILL.md`; this is the failure ledger. Each entry names the
symptom, root cause, fix, and prevention.

## Pitfalls

- Self-referential harness trap: a harness testing a scanner/linter embeds
  trigger strings in its own source. Give the scanner an explicit fixture
  marker (e.g. `gate_rot_guard:selftest`) that exempts marked files, and put
  the marker in BOTH docstring and code so any importer is covered too.

### Double-triple-quote syntax error

**Symptom**: `SyntaxError: unterminated string literal` at a docstring line.

**Cause**: Writing `"""text.""""` — three opening quotes, three closing quotes, then an extra `"`. Python reads this as `"""` (open docstring) + `"` (start of a new string that never closes).

**Fix**: Remove the extra quote. Docstrings are exactly `"""text."""` — three quotes on each side, no extras.

**Prevention**: After writing any file with docstrings, run `py_compile` immediately. The error will show the exact line.

See `references/syntax-pitfalls.md` for more.

### Python 3.11+ AST docstring check

**Symptom**: `AttributeError: 'Constant' object has no attribute 's'` or similar when stripping docstrings/comments via AST.

**Cause**: In Python 3.11+/3.14, `ast.Str`, `ast.Num`, and `ast.Bytes` were removed; string literals are now `ast.Constant`. Walkers that special-case `ast.Str` will miss every docstring.

**Fix**: match `ast.Constant` and check `isinstance(node.value, str)`. Example:
```python
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        # docstring/string literal
```

### Overflow guard for numeric conversions

**Symptom**: `OverflowError: int too large to convert to float` during cost/size arithmetic.

**Cause**: Calling `float(huge_int * rate)` or `float(huge_int / 1000.0 * cost_per_1k)` with values that exceed float range.

**Fix**: wrap the conversion in `try/except Exception` and fallback to `0.0`, then keep the existing non-finite/negative guard:
```python
try:
    cost_usd = float((entry.token_count / 1000.0) * entry.model_cost_per_1k)
except Exception:
    cost_usd = 0.0
if not math.isfinite(cost_usd) or cost_usd < 0.0:
    cost_usd = 0.0
```

### Round-trip export/import schema mismatch

**Symptom**: `LedgerCorruptionError: missing tiers/budgets` even though `to_json()` exists.

**Cause**: `to_json()` was serializing a read-oriented view (`get_budget_status()`), not the write schema `import_state()` expects (`tiers` + `budgets` with nested fields).

**Fix**: implement a private `_export_dict()` that returns exactly the schema `import_state()` consumes, and have `to_json()` serialize that. This makes state recovery deterministic and testable.

### Hermes PYTHONPATH shadows a project venv (C-extension ABI mismatch)

**Symptom**: running a project's own venv python inside a Hermes `terminal` call fails with
`Importing the numpy C-extensions failed ... compiled module files exist, but seem
incompatible with either python 'cpython-314'` and lists `*.cp311-win_amd64.pyd`.
The venv looks broken — but `pip list` inside it shows correct, matching versions.

**Cause**: Hermes exports `PYTHONPATH` containing its OWN agent venv:
`C:\Users\jonny\AppData\Local\hermes\hermes-agent;...\hermes-agent\venv\Lib\site-packages`.
`PYTHONPATH` entries are inserted into `sys.path` BEFORE the target venv's
`site-packages`, so a project venv on a different Python (3.14) imports the Hermes
venv's cp311-built numpy. `include-system-site-packages = false` does NOT protect
you — that only blocks the base prefix, never `PYTHONPATH`.

**Diagnose** (proves shadowing rather than a broken venv):
```bash
venv/Scripts/python.exe -c "import importlib.util as u;print(u.find_spec('numpy').origin)"
echo "[$PYTHONPATH]"
```
If the origin is under `hermes-agent\venv`, it is shadowing, not corruption.

**Fix**: strip `PYTHONPATH` for that invocation — do not touch the venv.
```bash
env -u PYTHONPATH venv/Scripts/python.exe -m pytest -q
```

**Prevention**: always run project-venv Pythons via `env -u PYTHONPATH` from Hermes
when the project venv's Python version differs from the Hermes agent venv's.
Never "repair" a venv on this symptom alone — you would reinstall correct packages
over correct packages and the failure would persist.

### "Pure" scan/check functions must be side-effect-free on ALL helper paths

**Symptom**: a function documented as "pure — no side effects" (e.g. `scan_content_pure()`
for a read-only hunt sweep) quietly mutates shared state — reputation stores, hit
counters, caches — because one of its helper calls (`_check_honeypot()`) had the
mutation buried inside it.

**Cause**: the side effect lives in a helper that the pure path ALSO calls, so the
"pure" entry point is only pure by docstring.

**Fix**: make the detector/checker genuinely pure (return the finding, mutate nothing),
and apply side effects in the reactive path only (`scan_content()`), driven by the
returned threat's countermeasure tag.

**Prevention**: after labeling any method "pure", audit EVERY helper it calls for
mutations, and write a boundary test that snapshots the mutable stores before the
call and asserts they are unchanged after — that test is what catches a helper-level
side effect a pure-by-name function hides.

### Signed-delta discipline (inverted penalty bug)

**Symptom**: the escalation/penalty ladder never fires — reputation rises on offense
instead of decaying.

**Cause**: `apply_delta(source, delta)` implemented as `current - delta` while every
caller passes a NEGATIVE delta (`rep_delta = -2.0`), so `10 - (-2) = 12`. The
convention (delta is signed) contradicts the math (function assumes unsigned damage).

**Fix**: pick ONE convention and make the function match the callers — signed deltas
mean `current + delta`. Assert the invariant in a boundary test: after one offense
the source's reputation must be strictly lower than before.

**Prevention**: when a "delta" is threaded through a pipeline, grep the call sites and
confirm sign conventions match the arithmetic. A function that works for its happy-path
test but inverts under real negative inputs is invisible until you test the boundary.

### py_compile is your friend

`python3 -m py_compile script.py` checks syntax without executing. Run it:
- After writing any .py file
- Before trusting a script you just created
- In CI gates for Python code

It catches syntax issues without running the code. Fast, safe, non-destructive.

### Fuzzy-match patches can splice inside a triple-quoted SQL/string block
**Symptom**: after an otherwise-correct find/replace edit, lint reports
`SyntaxError: unterminated triple-quoted string literal` or `IndentationError`
a few lines below the intended change.

**Cause**: string-replacement tools match loosely; when `old_string` ends inside
or adjacent to a `"""..."""` block (common in code with inline SQL), the
replacement can close the block early and leave orphaned fragments of the
original text (`""", (limit,))`, misindented returns) behind.

**Fix**: read the damaged region (`sed -n` / read_file) immediately, remove the
orphaned fragments in 1–2 follow-up patches, and re-run py_compile until clean.
Never leave a file half-patched while moving on.

**Prevention**: for edits near triple-quoted strings, include the ENTIRE logical
block (full SQL statement plus its surrounding call) as `old_string`, not just
the tail line. Always run py_compile right after each patch — the tool's own
lint report names new errors introduced by that edit.

### Heredoc block-replaces fail on escape normalization — splice by anchor, don't match whole blocks
**Symptom**: a Python heredoc that reads a file and runs several
`assert old_block in s; s = s.replace(old_block, new_block)` edits fails on
ONE block with `AssertionError` even though every fragment of that block is
visibly present in the file (and the other blocks in the same script succeed).

**Cause**: `\n` sequences inside the file's source can be normalized to `\\n`
when the block is transported through the heredoc/terminal layer (or the
script's own escape handling), so the exact full-block string in your script
no longer equals the on-disk bytes. One `\\n` vs `\n` at position 1296 breaks
an exact-match `old_string` that otherwise looks right.

**Fix**: don't rewrite whole blocks verbatim. For each block, assert on a
SMALL unique anchor (`assert 'def fanout(objective' in s`), then splice by
index:
```python
start = s.find("def fanout(objective")
end = s.find("def main()")
assert start != -1 and end != -1 and start < end
s = s[:start] + s[end:]
```
Keep exact-match `replace()` only for short, escape-free snippets (a single
CLI branch, a one-line const). This also survives future edits inside the
block body without re-verifying every character.

**Prevention**: when a multi-block edit fails mid-way, print
`s[s.find(start_anchor):][:60]` + `repr()` to diff the transported text
against your expectation instead of re-typing the whole block — the diff at
the first divergence names the escape normalization instantly.

### Hostname/username baked into test assertions
**Symptom**: a subsystem test fails on every machine except the author's — e.g.
an expected `node_id` of `"integration-test-node-arkwindows"` when the actual
hostname is different.

**Cause**: test assertions baked in a hostname/username/port observed at write
time instead of computing it live.

**Fix**: derive identity at runtime:
```python
expected = f"{node_name}-{socket.gethostname()}".lower()
```
and remember to add `import socket` (a missing import surfaces only when the
test path finally runs).

### Missing generic execute method on a shared DB wrapper
**Symptom**: `AttributeError: 'PersistentCortexDB' object has no attribute
'cortex_execute'` from a satellite module trying to create its own tables.

**Cause**: module written against a richer API than the shared DB class exposes.

**Fix**: add one small generic method to the DB class rather than editing every
caller:
```python
def cortex_execute(self, sql: str, params: tuple = ()) -> None:
    with self._get_connection() as conn:
        conn.execute(sql, params)
        conn.commit()
```
Verify by instantiating the dependent engine directly — a clean init with no
warning line proves the tables now create.
