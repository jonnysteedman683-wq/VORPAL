---
name: hermes-python-encoding
description: Python encoding bugs, JSONL writing, and hashing pitfalls.
category: software-development

## Hermes Python Encoding — Encoding Bugs, JSONL, and Hashing Pitfalls

### Trigger
When writing Python code that serializes data to disk, computes hashes,
or handles string/bytes conversions. These bugs fail silently at runtime.

### Pitfall 1: JSONL — Literal Backslash-n

```python
# BUG: writes literal "\n" (backslash + n), NOT a newline
import json
f.write(json.dumps(obj) + "\\n")

# FIX: real newline character
f.write(json.dumps(obj) + "\n")
```

**Why it happens**: In Python, `"\\n"` is a 2-char string: backslash + n.
`"\n"` is a 1-char newline. In source code, both look similar but produce
different output. When writing JSONL files, literal `\n` creates invalid
JSONL that downstream parsers reject.

### Pitfall 2: hashlib.sha256 Needs .encode()

```python
# BUG: TypeError on Python 3 — sha256() requires bytes
hashlib.sha256("string_input")

# FIX: encode to bytes first
hashlib.sha256("string_input".encode("utf-8"))
```

### Pitfall 3: f.write with Escaped Backslash

```python
# BUG: writes literal backslash-n instead of newline
f.write(json.dumps(obj) + "\\n")

# FIX: use single backslash for real newline
f.write(json.dumps(obj) + "\n")
# OR better: use json.dumps + newline via print
print(json.dumps(obj), file=f)
```

### Pitfall 4: open() Without encoding

```python
# BUG: platform-dependent encoding (fails on Windows with non-UTF8 content)
with open(path, "w") as f:
    f.write(data)

# FIX: always specify encoding
with open(path, "w", encoding="utf-8") as f:
    f.write(data)
```

### Pitfall 5: json.load(open(...)) — File Handle Leak

```python
# BUG: file handle never closed
reg = json.load(open(path))

# FIX: use context manager
with open(path, encoding="utf-8") as f:
    reg = json.load(f)
```

### Pitfall 6: Token Strip Bug (Lingua Prima)

```python
# BUG: strips @ prefix, but tokenizer expects @x format
if token.startswith("@"):
    return token[1]  # returns "a" instead of "@a"

# FIX: return full token
return token
```

### Pitfall 7: Path("") Is Truthy

```python
# BUG: Path("") == Path("."), and Path(".").exists() is True
vault = Path(os.environ.get("OBSPATH", ""))
if vault.exists():  # BUG: always True when env unset!
    do_obsidian_sync()

# FIX: guard against empty string
env = os.environ.get("OBSPATH", "")
vault = Path(env) if env else None
if vault and vault.exists():
    do_obsidian_sync()
```

### Pitfall 8: Non-Atomic Read-Modify-Write

```python
# BUG: race condition — two processes can read same content, both write
content = path.read_text()
path.write_text(content + new_line)

# FIX: atomic write via temp file + os.replace
tmp = path.with_suffix(".tmp")
tmp.write_text(new_content)
os.replace(tmp, path)  # atomic on same volume
```

### Pitfall 9: Mutable Default Argument

```python
# BUG: shared mutable default across calls
def append_to_log(item, log=[]):
    log.append(item)
    return log

# FIX: use None sentinel
def append_to_log(item, log=None):
    if log is None:
        log = []
    log.append(item)
    return log
```

### Pitfall 10: Integer Division Misuse

```python
# BUG: 90 // 60 = 1, not 1.5
logger.info(f"interval={args.interval}s ({args.interval // 60} min)")

# FIX: use float division for display
logger.info(f"interval={args.interval}s ({args.interval / 60:.1f} min)")
```

### Quick Reference — Write Patterns

```python
# JSONL file (one JSON object per line):
import json
with open(path, "w", encoding="utf-8") as f:
    for obj in objects:
        f.write(json.dumps(obj) + "\n")  # NOT "\\n"

# Single JSON file:
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# SHA256 hash:
import hashlib
key = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

# Atomic file write:
import os
from pathlib import Path
tmp = path.with_suffix(".tmp")
tmp.write_text(data, encoding="utf-8")
os.replace(tmp, path)
```

### Pattern Proved
`json.dumps(obj) + "\\n"` looks correct in source but writes literal backslash-n.
Always use `+ "\n"` (single backslash) for real newlines in JSONL files.
