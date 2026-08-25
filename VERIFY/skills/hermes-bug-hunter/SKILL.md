---
name: hermes-bug-hunter
description: Use for scanning Python codebases for latent bugs.
category: software-development

## Hermes Bug Hunter — Systematic Latent Bug Scan

### Trigger
When scanning Python codebases for correctness bugs that pass type-checking
but fail under concurrency, edge cases, or evolution.

### Scan Checklist

1. **Bare except** — `grep -rn "except\s*:" .` — swallows KeyboardInterrupt.
2. **File paths** — `grep -rn "open(\|\.read_text\|\.write_text" .` — missing encoding or with-block.
3. **Path resolution** — `Path("relative/...")` or wrong ROOT join — use `__file__.resolve().parent`.
4. **TOCTOU** — `_locate()` or `exists()` outside locks — acquire lock before checking.
5. **Encoding** — `f.write(line + "\\n")` produces literal backslash-n; real newline is `+ "\n"`. `sha256(s)` needs `.encode("utf-8")`.
6. **Logic** — `x if cond else x` — both branches identical, dead ternary.
7. **Hardcoded counts** in harnesses — use `>= N`.
8. **Incomplete globs** — only one subdir, only `.json` — iterate all.

### Priority Tiers
- CRITICAL: TOCTOU, wrong file path
- HIGH: swallowed exceptions, silent data loss
- MEDIUM: hardcoded counts, non-atomic writes
- LOW: dead code, late imports

### Verification
```bash
python3 -m py_compile $(find . -name "*.py" -not -path "*/__pycache__/*")
python3 scripts/verify_all.py
```

### Pattern Proved
Latent bugs hide in bare excepts and TOCTOU races — always scan these first.
