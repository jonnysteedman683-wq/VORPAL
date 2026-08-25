---
name: hermes-path-resolution
description: Cross-platform Python path safety for Windows, MSYS, and triad workspaces.
category: software-development

## Hermes Path Resolution — Cross-Platform Python Path Safety

### Trigger
When writing Python scripts that must work across Windows/MSYS/Git-Bash
environments with multi-profile workspace layouts (ARK, OMNIPRIME, AURORAL).

### Environment Constants

| Variable | Value | Notes |
|----------|-------|-------|
| Shell | git-bash/MSYS2 | Not PowerShell, not cmd.exe |
| Python | `python` = 3.11, `python3` = 3.14.6 | `pip` → `python3.11` (mismatch!) |
| Home | `C:\Users\jonny` | NOT hostname-based |
| Toolchains | uv, poolside/laguna-s-2.1:free via Nous |

### Core Rules

1. **Always use `Path(__file__).resolve().parent`** for module-relative paths
2. **Never use relative paths** like `Path("SKILLHUB/...")` — breaks on wrong CWD
3. **Forward slashes only** — bypass MSYS path mangling
4. **Use `python -m py_compile`** instead of `python script.py` for syntax checks

### Path Resolution Patterns

#### Bad: Relative path
```python
# BUG: breaks if CWD != OMNIPRIME root
BASE = Path("SKILLHUB/skills/tier_1_active")
```

#### Good: Absolute from `__file__`
```python
ROOT = Path(__file__).resolve().parent.parent  # walks up from scripts/
BASE = ROOT / "SKILLHUB" / "skills" / "tier_1_active"
```

#### Bad: Registry path mismatch
```python
# BUG: registry.json lives in SKILLHUB/, not ROOT
REGISTRY = ROOT / "registry.json"
```

#### Good: Correct path
```python
REGISTRY = ROOT / "SKILLHUB" / "registry.json"
```

### MSYS Path Mangling

MSYS converts `/c/Users/...` to `C:\Users\...` automatically. But:
- Never use `\` in Python strings — use `/` or `Path()` objects
- `pathlib.Path` handles both `/` and `\` natively
- `os.path.join()` also works cross-platform

### Windows-Specific Gotchas

```python
# BUG: Path("") == Path(".") which is truthy!
self._obsidian_vault = Path(os.environ.get("OBSIDIAN_VAULT", ""))
self._obsidian_available = self._obsidian_vault.exists()  # always True!

# FIX: Guard against empty string
obsidian_env = os.environ.get("OBSIDIAN_VAULT", "")
self._obsidian_vault = Path(obsidian_env) if obsidian_env else None
self._obsidian_available = self._obsidian_vault is not None and self._obsidian_vault.exists()
```

### Python Version Gotchas

```python
# python (3.11) vs python3 (3.14) — pip → python3.11 (mismatch)
# Always use `python` for 3.11 work, `python3` for 3.14
# py_compile must match the interpreter running the code
```

### Triad Path Topology

```
~/.OneDrive/Desktop/
├── AURORAL/                    (default profile, working dir)
├── OMNIPRIME/                  (OMNIPRIME_ROOT)
│   ├── .hive/bus/              (messsage bus state)
│   ├── SKILLHUB/               (skill registry, metrics)
│   │   ├── registry.json       (active_skills, watermark)
│   │   ├── SKILL_METRICS.json
│   │   ├── scripts/            (dual_agent_loop.py, etc.)
│   │   ├── skill_library/      (tiered skills)
│   │   ├── skill_repair/       (PRIORITY_1/2/3 queues)
│   │   └── tests/              (hermes_verify_*.py)
│   ├── core/                   (safety_gate.py, state_memory_manager.py)
│   ├── syscalls.py             (workspace root, NOT under SKILLHUB/)
│   ├── EVOLVE/SKILLHUB/        (authoritative source of truth)
│   │   ├── SKILLS/pyramid/     (apex/core/, apex/utilities/, LANGUAGE/)
│   │   └── tests/              (hermes_verify_syscalls.py, etc.)
│   └── scripts/bus_router.py   (bus implementation)
│
Note: OMNIPRIME_ROOT/SKILLHUB/ is deprecated — use EVOLVE/SKILLHUB/
```

### Pattern Proved
Three `.parent` calls from `scripts/bus_router.py` → OMNIPRIME root.
Registry lives in `SKILLHUB/registry.json`, not `ROOT/registry.json`.
Empty `Path("")` is truthy → breaks env-var guards.
