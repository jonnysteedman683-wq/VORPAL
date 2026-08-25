---
name: hermes-file-lock-patterns
description: Filesystem lock files, atomic moves, and concurrency safety in Python.
category: devops

## Hermes File Lock Patterns — Concurrency Safety in Python

### Trigger
When building filesystem-based coordination primitives (bus routers, claim
processing, batch commits) that must handle multiple processes, threads, or
cron jobs touching the same files.

### Core Principle
Never assume a file's state between checking it and acting on it. The window
between `_locate()` and `read_text()` is a TOCTOU (time-of-check-to-time-of-use)
race that causes `FileNotFoundError` under concurrency.

### Two-Layer Locking Pattern

```python
import threading
import time
import os

try:
    import msvcrt  # Windows file locking
except ImportError:
    msvcrt = None

_PROC_LOCK = threading.Lock()      # Layer 1: in-process thread mutex
LOCK_RETRIES = 50
LOCK_BACKOFF_S = 0.01

CLAIM_LOCK = None  # set per-bus instance

def _acquire_claim_lock():
    """Exclusive claim lock. Returns unlock fn."""
    _PROC_LOCK.acquire()
    f = open(CLAIM_LOCK, "a+")
    try:
        if msvcrt is not None:
            # Layer 2: OS advisory lock for cross-process
            for attempt in range(LOCK_RETRIES):
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                    break
                except OSError:
                    if attempt == LOCK_RETRIES - 1:
                        raise
                    time.sleep(LOCK_BACKOFF_S * (attempt + 1))
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    except BaseException:
        f.close()
        _PROC_LOCK.release()
        raise

    def _release():
        try:
            if msvcrt is not None:
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        finally:
            f.close()
            _PROC_LOCK.release()
    return _release
```

### Atomic Move Pattern

```python
import os

def _move_packet(src: Path, dst_inbox: Path, profile: str):
    """Atomically move a packet with claimed_by status."""
    pkt = json.loads(src.read_text(encoding="utf-8"))
    pkt["status"] = f"claimed_by:{profile}"
    pkt["claimed_ts"] = _now()

    dst_path = dst_inbox / src.name
    tmp_path = dst_inbox / f"{src.name}.claiming"

    # Write to temp file first
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(pkt, f, indent=2)

    # Atomic rename (os.replace is atomic on same volume)
    os.replace(tmp_path, dst_path)

    src.unlink(missing_ok=True)
    return pkt
```

### Lock-Before-Locate (TOCTOU Fix)

```python
def consume(profile: str, packet_id: str) -> None:
    """Atomically reserve a pending packet for processing."""
    release = _acquire_claim_lock()  # LOCK FIRST
    try:
        path = _locate(profile, packet_id)  # Now safe inside lock
        if path is None:
            raise SystemExit(f"packet not found: {packet_id}")
        pkt = json.loads(path.read_text(encoding="utf-8"))
        if pkt.get("status") != "pending":
            raise SystemExit(2)  # already claimed
        # ... process ...
    finally:
        release()
```

### Atomic Write Pattern

```python
def safe_write(path: Path, data: str, encoding="utf-8"):
    """Write file atomically — never leaves partial content."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding=encoding) as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())  # force to disk
    os.replace(tmp, path)  # atomic on same volume
```

### File Handle Management

```python
# BUG: file handle leak
data = json.load(open(path))

# FIX: context manager
with open(path, encoding="utf-8") as f:
    data = json.load(f)

# BUG: no encoding
with open(path, "w") as f:
    f.write(data)

# FIX: always specify encoding
with open(path, "w", encoding="utf-8") as f:
    f.write(data)
```

### Common Exit Codes

| Code | Meaning | Pattern |
|------|---------|---------|
| 0 | Success | Normal completion |
| 1 | Error | General failure |
| 2 | Rejected | Already claimed/acked (double-exec, double-ack) |
| 3 | Partial | Batch not fully committed (G3) |

### Lock Scope

```
Scope                    | Layer Used       | Handles
------------------------|------------------|------------------
Threads in one process  | _PROC_LOCK       | cron threads
Processes (same host)   | msvcrt/fcntl     | concurrent cron jobs
Network (multi-host)    | External (Redis) | not covered here
```

### Pattern Proved
Two-layer locking (thread mutex + OS advisory) is the minimum for
filesystem-based coordination. Lock BEFORE `_locate()` to eliminate
the TOCTOU window that causes `FileNotFoundError` under concurrency.
