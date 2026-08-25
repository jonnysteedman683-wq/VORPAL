---
name: hermes-bus-atomicity
description: Filesystem bus atomicity, claim, and race-condition patterns.
category: software-development

## Hermes Bus Atomicity — Filesystem-Based Inter-Agent Messaging

### Trigger
When building or auditing filesystem-based message buses with multi-consumer
race conditions, claim-then-process patterns, or batch task commit semantics.

### Core Invariants

| Invariant | Rule | Exit Code |
|-----------|------|-----------|
| G1 | A consumed packet is invisible to `read()` | consume moves to `processing/` |
| G3 | Batch acked only when ALL tasks = PASS | partial → exit 3 |
| G4 | Double-ack rejected | re-ack → exit 2 |
| G5 | Atomic file moves via `os.replace()` | temp file + atomic swap |

### Two-Layer Locking Pattern

```python
_PROC_LOCK = threading.Lock()      # in-process thread serialization
LOCK_RETRIES = 50
LOCK_BACKOFF_S = 0.01

def _acquire_claim_lock():
    CLAIM_LOCK.parent.mkdir(parents=True, exist_ok=True)
    _PROC_LOCK.acquire()
    f = open(CLAIM_LOCK, "a+")
    try:
        # Layer 2: OS advisory lock (msvcrt on Windows, fcntl on Unix)
        if msvcrt is not None:
            for attempt in range(LOCK_RETRIES):
                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                    break
                except OSError:
                    if attempt == LOCK_RETRIES - 1: raise
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
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        finally:
            f.close()
            _PROC_LOCK.release()
    return _release
```

### TOCTOU-Safe Consume Pattern

```python
def consume(profile: str, packet_id: str) -> None:
    # BUG: _locate() outside lock → TOCTOU race
    # path = _locate(profile, packet_id)   # RACE: file moves between here...
    # release = _acquire_claim_lock()
    # pkt = path.read_text()  # ...and here

    # FIX: lock BEFORE _locate
    release = _acquire_claim_lock()
    try:
        path = _locate(profile, packet_id)
        if path is None:
            raise SystemExit(f"packet not found: {packet_id}")
        pkt = json.loads(path.read_text(encoding="utf-8"))
        if pkt.get("status") != "pending":
            raise SystemExit(2)  # already claimed/acked
        # move to processing/ atomically
        proc = inbox / "processing"
        proc.mkdir(parents=True, exist_ok=True)
        tmp = proc / f"{packet_id}.claiming"
        with open(tmp, "w") as f:
            json.dump(pkt, f)
        os.replace(tmp, proc / f"{packet_id}.json")
        path.unlink(missing_ok=True)
    finally:
        release()
```

### Batch Task Commit (G3)

```python
def ack(profile, packet_id):
    release = _acquire_claim_lock()
    try:
        pkt = json.loads(path.read_text())
        if pkt["status"] not in ("pending", "processing"):
            raise SystemExit(2)  # double-ack
        tasks = pkt.get("payload", {}).get("tasks")
        if isinstance(tasks, list) and tasks:
            states = pkt.get("task_status") or []
            done = [s for s in states if s == "PASS"]
            if len(done) != len(tasks):
                raise SystemExit(3)  # partial batch
        pkt["status"] = "acked"
        path.write_text(json.dumps(pkt))
    finally:
        release()
```

### Test Harness — `bus_atomicity_test.py`

```python
# B1: claim-vs-read race — consumed packet invisible to read()
# B2: double-exec — N concurrent consumers, exactly 1 winner, rest get exit 2
# B3: no-double-ack — second ack() returns exit 2
# B4: batch partial — ack@0/3=3, ack@1/3=3, ack@3/3=0
```

### Pattern Proved
Lock before locate. Always. The two-layer lock (thread mutex + OS advisory)
serializes both same-process threads and cross-process cron jobs.
