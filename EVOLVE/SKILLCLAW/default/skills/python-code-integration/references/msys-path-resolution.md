# MSYS Path Resolution: `Path.resolve()` vs `os.path.abspath()`

## The Problem

In MSYS/Cygwin environments, `pathlib.Path(__file__).resolve().parent` produces broken
paths like `C:\c\Users\...` that fail `os.path.exists()` silently:

```python
from pathlib import Path
# In MSYS, __file__ might be something like /c/Users/jonny/.../module.py
p = Path(__file__).resolve().parent
print(p)          # C:\c\Users\jonny\...\  (broken!)
print(p.exists()) # False — the path doesn't exist
```

This happens because MSYS paths start with `/c/` which Python interprets as a relative
path component `c` under the current drive.

## When It Bites

This specifically affects `sys.path` manipulation for importing sibling packages:

```python
# BROKEN — produces C:\c\Users\...
sys.path.insert(0, str(Path(__file__).resolve().parent / "CORE"))

# WORKS — produces C:\Users\...
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "CORE"))
```

## The Fix

Always use `os.path` for building module paths in MSYS:

```python
import os

# Get the directory containing the current file
_mod_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory
_parent = os.path.dirname(_mod_dir)

# Build a path to a sibling directory
_vorpal_core = os.path.join(_parent, "VORPAL", "CORE")

# Add to sys.path
sys.path.insert(0, _vorpal_core)
```

## Debugging

If you get `ModuleNotFoundError` for a module you can see exists, check your path construction:

```python
import os
print("Path:", os.path.join(os.path.dirname(os.path.abspath(__file__)), "CORE"))
print("Exists:", os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "CORE")))
```

## Relation to Existing Skills

The `python-script-verification` skill's `references/msys-path-pitfall.md` covers the
same issue but from the perspective of receiving paths from bash variables. This note
covers the specific case of building `sys.path` from `__file__` — which is the more
common trigger when integrating stolen code.
