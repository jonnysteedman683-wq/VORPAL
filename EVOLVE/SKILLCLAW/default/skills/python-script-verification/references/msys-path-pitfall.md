# MSYS/Cygwin Path Resolution Pitfall

## The Problem

When a Python script receives a path from MSYS2/Cygwin bash (e.g., `$PWD`, `$(pwd)`, or an environment variable exported from bash), the path is often in MSYS format — `/c/Users/jonny/...` rather than `C:\Users\jonny\...`.

Python's `pathlib.Path` on Windows resolves MSYS-style paths differently than expected:

```python
from pathlib import Path
p = Path("/c/Users/jonny/OneDrive/Documents")
print(p)          # May print: C:\c\Users\jonny\OneDrive\Documents
                    # (double C: drive letter)
print(p.exists()) # Often False — the path doesn't exist
```

This happens because MSYS paths start with `/c/` which Python interprets as a relative path component `c` under the current drive, producing `C:\c\...` instead of `C:\Users\...`.

## Real Case from This Session

When running the personal-api setup, `$(pwd)` returned `/c/Users/jonny/OneDrive/Documents/Personal API Vault`. Passing this to `python3 setup.py` via `OBSIDIAN_VAULT_PATH="$(pwd)"` caused the Python script to receive the MSYS path, resolve it to `C:\c\Users\...,` and fail with "does not exist or is not a directory."

## Fixes

### Fix 1: Use inline Python with explicit Windows paths

Instead of passing paths through bash variables, use inline Python with the path hardcoded or resolved inside Python:

```bash
python3 -c "
from pathlib import Path
vault = Path(r'C:\Users\jonny\OneDrive\Documents\Personal API Vault')
# ... use vault directly
"
```

This avoids the MSYS path entirely.

### Fix 2: Resolve the path in Python from bash

If you must pass the path from bash, convert it in Python before use:

```bash
export OBSIDIAN_VAULT_PATH="$(pwd)"
python3 -c "
import os
from pathlib import Path
raw = os.environ['OBSIDIAN_VAULT_PATH']
# MSYS paths start with /c/, /d/, etc. Convert to Windows format
if raw.startswith('/'):
    drive = raw[1:2].upper()
    rest = raw[3:].replace('/', '\\')
    resolved = Path(f'{drive}:{rest}')
else:
    resolved = Path(raw)
print(f'resolved: {resolved}')
"
```

### Fix 3: Use a Python script that accepts MSYS paths and normalizes them

```python
def normalize_msys_path(raw: str) -> Path:
    """Convert MSYS/Cygwin paths to Windows pathlib Paths."""
    if not raw.startswith('/'):
        return Path(raw)
    # /c/Users/... → C:\Users\...
    parts = raw.split('/')
    if len(parts) >= 3 and len(parts[1]) == 1:
        drive = parts[1].upper()
        rest = '\\'.join(parts[2:])
        return Path(f'{drive}:{rest}')
    return Path(raw)
```

### Fix 4: Use the actual Windows path directly in bash

On MSYS2, `cygpath` can convert between formats:

```bash
# Convert MSYS path to Windows format
WIN_PATH=$(cygpath -m "$(pwd)")
echo "$WIN_PATH"  # C:\Users\jonny\...
```

## Detection

If a Python script reports a path "does not exist" but you can see it in File Explorer or `ls`, suspect an MSYS path resolution issue. Print the resolved path from Python and compare with the known-good Windows path.

## Prevention

- **Prefer inline Python** for one-off scripts that need file system access — bypass bash path issues entirely.
- **Use raw strings** (`r"C:\..."`) for hardcoded Windows paths in Python.
- **Test with known paths** — if a script takes a path argument, test it with a path known to exist and verify the script resolves it correctly.
- **Add a path-debug print** when a script fails with "file not found" — print the resolved path before the failing operation.
