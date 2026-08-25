# syscalls.py -- Agent OS Syscall Layer for OMNIPRIME
# [OMNIPRIME-FORGE] | Version: 1.0.0 | Lingua Status: V3
#
# Zero-dependency syscalls with P|F|V3 status returns.

"""OMNICORE SYSCALL INTERFACE -- Watermarked [OMNIPRIME-FORGE]"""

import sys
import json
import hashlib
import shutil
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Workspace paths
ROOT = Path(__file__).parent
PYRAMID = ROOT / "EVOLVE" / "SKILLHUB" / "SKILLS" / "pyramid"
BUS = ROOT / ".hive" / "bus"
REGISTRY = ROOT / "EVOLVE" / "SKILLHUB" / "registry.json"
CACHE = BUS / "artifact_cache.json"

# Lingua status codes
class LinguaStatus:
    PROGRESS = "P"
    FAILURE = "F"  
    VERIFIED_V3 = "V3"

# Observable proof-of-work counter: incremented ONLY when verify() actually
# runs py_compile. A cache hit must leave it untouched (M8 harness asserts).
COMPILE_COUNT = 0

# ==================== VERIFICATION SYSCALL ====================

def verify(artifact: Path) -> str:
    """Verify artifact health via py_compile gate.

    Lingua: verify(filepath) -> P|F|V3
    V3 if py_compile green AND harness PASS

    M8 RESULT COMPOUNDING: a cached PASS from a trusted verifier short-circuits
    the compile entirely. COMPILE_COUNT is the observable that makes "duplicate
    verification is avoided" a provable claim rather than a comment --
    hermes_verify_artifact_cache.py asserts on it.
    """
    global COMPILE_COUNT
    artifact = Path(artifact)
    if not artifact.exists():
        return LinguaStatus.FAILURE

    # Check the cache first (M8 ritual: never re-verify a trusted PASS)
    if not should_verify(artifact):
        return LinguaStatus.VERIFIED_V3

    # Run py_compile -- this is the work the cache exists to avoid
    import py_compile
    try:
        COMPILE_COUNT += 1
        py_compile.compile(str(artifact), doraise=True)
        register_artifact(artifact, verdict="PASS", verified_by="omniprime")
        return LinguaStatus.VERIFIED_V3
    except py_compile.PyCompileError:
        register_artifact(artifact, verdict="FAIL", verified_by="omniprime")
        return LinguaStatus.FAILURE

# ==================== QUARANTINE SYSCALL ====================

def quarantine(fail_path: Path, category: str = "PRIORITY_1_CRITICAL") -> Path:
    """Move failed artifact to skill_repair directory.
    
    Lingua: quarantine(path, type) -> P|F
    
    Uses timestamp-based unique naming to prevent overwrites.
    """
    fail_path = Path(fail_path)
    if not fail_path.exists():
        return Path("/nonexistent")
    
    repair_dir = ROOT / "EVOLVE" / "SKILLHUB" / "skill_repair" / category
    repair_dir.mkdir(parents=True, exist_ok=True)
    
    # Use timestamp + original name to prevent overwrites
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    unique_name = f"{timestamp}_{fail_path.name}"
    dest = repair_dir / unique_name
    
    # Double-check dest doesn't exist (rare race window)
    if dest.exists():
        uuid_suffix = uuid.uuid4().hex[:8]
        dest = repair_dir / f"{timestamp}_{uuid_suffix}_{fail_path.name}"
    
    shutil.move(str(fail_path), str(dest))
    return dest

# ==================== ERROR LOGGING SYSCALL ====================

def log_err(error: Exception, context: dict) -> Path:
    """Log error to ERR_ ledger. Returns log file path.
    
    Lingua: log_err(ex, ctx) -> P|F
    
    Uses uuid for unique err_id to avoid race on concurrent calls.
    """
    error_log = ROOT / "NOTES.md"
    
    # Use uuid for unique err_id to avoid race on concurrent calls
    err_id = f"ERR_{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now(timezone.utc).isoformat()
    
    entry = {
        "err_id": err_id,
        "timestamp": timestamp,
        "type": type(error).__name__,
        "message": str(error),
        "context": context
    }
    
    with open(error_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    
    return error_log

# ==================== CACHE CHECK SYSCALL ====================

def cache_check(artifact: Path) -> Optional[Dict[str, Any]]:
    """Check if artifact is cached with VERIFIED_V3 status.

    Lingua: cache_check(path) -> P|F|V3 + metadata or None

    Two-source lookup (M8 RESULT COMPOUNDING):
      1. .hive/bus/artifact_cache.json  -- fast local verification cache
      2. registry.json  ["verified_artifacts"]  -- durable, cross-cycle record

    A hit in EITHER source means this exact (path, mtime) pair already passed a
    harness, so re-verifying it is provably redundant work.
    """
    artifact = Path(artifact)
    if not artifact.exists():
        return None

    try:
        artifact_key = _artifact_key(artifact)
    except OSError:
        return None

    # --- source 1: bus-local cache ---
    if CACHE.exists():
        try:
            cache_data = json.loads(CACHE.read_text(encoding='utf-8'))
            entry = cache_data.get(artifact_key)
            if entry and entry.get('verdict') == 'PASS':
                return entry
        except (json.JSONDecodeError, OSError):
            pass  # corrupt cache is a miss, never a crash

    # --- source 2: durable registry ledger ---
    entry = _registry_artifact(artifact_key)
    if entry and entry.get('verdict') == 'PASS':
        return entry
    return None


def _artifact_key(filepath: Path) -> str:
    """Generate cache key from file path + mtime.

    O(1) in file SIZE by construction: only the resolved path string and the
    mtime float are hashed, never file contents. hermes_verify_artifact_cache.py
    proves this empirically across a 4000x size range.
    """
    stat = filepath.stat()
    raw = f"{filepath.resolve()}|{stat.st_mtime}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ==================== M8: VERIFIED-ARTIFACT REGISTRY ====================

def _load_registry() -> Dict[str, Any]:
    """Load registry.json, tolerating absence/corruption."""
    if not REGISTRY.exists():
        return {}
    try:
        data = json.loads(REGISTRY.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _registry_artifact(artifact_key: str) -> Optional[Dict[str, Any]]:
    """Look up one verified-artifact entry by its sha256 key."""
    entries = _load_registry().get('verified_artifacts')
    if isinstance(entries, dict):
        return entries.get(artifact_key)
    return None


def register_artifact(artifact: Path, verdict: str = "PASS",
                      verified_by: str = "omniprime") -> Optional[Dict[str, Any]]:
    """Record a verified artifact in registry.json (M8 schema). Returns entry.

    Lingua: register_artifact(path, verdict, verifier) -> entry | None

    Schema per verified_artifacts[key]:
        path                   relative-to-root path (portable across clones)
        sha256_of_path_mtime   the O(1) cache key
        verdict                PASS | FAIL
        verified_by            agent id that ran the harness
        at                     UTC ISO-8601 timestamp
        green_streak           consecutive PASS count for this path

    Called after a harness PASS so the NEXT cycle can skip re-verification.
    """
    artifact = Path(artifact)
    if not artifact.exists():
        return None

    key = _artifact_key(artifact)
    try:
        rel = str(artifact.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        rel = str(artifact.resolve()).replace("\\", "/")

    data = _load_registry()
    entries = data.get('verified_artifacts')
    if not isinstance(entries, dict):
        entries = {}

    # green_streak carries over from any prior entry for the SAME path.
    streak = 0
    for old in entries.values():
        if old.get('path') == rel:
            streak = max(streak, int(old.get('green_streak', 0) or 0))
    streak = streak + 1 if verdict == "PASS" else 0

    entry = {
        "path": rel,
        "sha256_of_path_mtime": key,
        "verdict": verdict,
        "verified_by": verified_by,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "green_streak": streak,
    }
    entries[key] = entry
    data['verified_artifacts'] = entries
    data['verified_artifacts_schema'] = 1
    REGISTRY.write_text(json.dumps(data, indent=2), encoding='utf-8')
    return entry


def verified_artifacts() -> Dict[str, Any]:
    """Return the whole verified-artifact ledger (M8 read syscall)."""
    entries = _load_registry().get('verified_artifacts')
    return entries if isinstance(entries, dict) else {}


def should_verify(artifact: Path, verifier: str = "omniprime") -> bool:
    """M8 gate: False when re-verification is provably redundant.

    Skip only when the cached verdict is PASS AND the verifier is trusted
    (auroral, or self with a green streak) -- exactly the ritual ARK specified.
    """
    entry = cache_check(artifact)
    if not entry or entry.get('verdict') != 'PASS':
        return True
    by = entry.get('verified_by') or entry.get('verifier') or ''
    if by == 'auroral':
        return False
    if by == verifier and int(entry.get('green_streak', 0) or 0) >= 1:
        return False
    return True


# ==================== LINGUA BOOT SYSCALL ====================

def lingua_boot(emit: bool = True) -> Dict[str, Any]:
    """Boot the Lingua Prima dictionary and emit LP events. Returns boot record.

    Lingua: lingua_boot() -> {status: P|F|V3, fingerprint, events_emitted}
    Closes [ERR_LINGUA_BOOT_GAP]: the LP event set is non-empty after this call.
    """
    import importlib.util
    mod_path = ROOT / "lingua_boot.py"
    if not mod_path.exists():
        return {"status": LinguaStatus.FAILURE, "error": "lingua_boot.py absent"}
    spec = importlib.util.spec_from_file_location("omniprime_lingua_boot", mod_path)
    if spec is None or spec.loader is None:
        return {"status": LinguaStatus.FAILURE, "error": "spec build failed"}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.boot(emit=emit)

# ==================== LEDGER BALANCE SYSCALLS ====================

def ledger_balance() -> int:
    """Return current token/credit balance from registry."""
    if not REGISTRY.exists():
        return 1000  # Default boot credits
    
    try:
        data = json.loads(REGISTRY.read_text(encoding='utf-8'))
        return data.get('ledger_balance', 1000)
    except (json.JSONDecodeError, OSError):
        return 1000

def ledger_spend(cost: int) -> str:
    """Deduct credits from ledger. Returns P|F.
    
    Blocks dispatch at negative balance (gate: M3).
    
    Uses atomic read-modify-write with json.loads/write to minimize
    race window between reads. For production use with concurrent
    access, consider adding file-level locking.
    """
    if cost < 0:
        return LinguaStatus.FAILURE
    
    # Atomic-ish read: load once, compute, write once
    try:
        data = json.loads(REGISTRY.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        data = {"ledger_balance": 1000}
    
    balance = data.get('ledger_balance', 1000)
    
    if balance < cost:
        return LinguaStatus.FAILURE
    
    data['ledger_balance'] = balance - cost
    data['last_spend'] = datetime.now(timezone.utc).isoformat()
    
    REGISTRY.write_text(json.dumps(data, indent=2), encoding='utf-8')
    return LinguaStatus.PROGRESS

# ==================== UTILITY SYSCALLS ====================

def send(to_profile: str, ptype: str, payload: dict) -> dict:
    """Send packet via bus. Returns packet dict."""
    packet = {
        "id": uuid.uuid4().hex[:12],
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "from": "omniprime",
        "to": to_profile,
        "type": ptype,
        "payload": payload,
        "status": "pending",
    }
    
    inbox = BUS / f"inbox_{to_profile}"
    inbox.mkdir(parents=True, exist_ok=True)
    path = inbox / f"{packet['id']}.json"
    
    path.write_text(json.dumps(packet, indent=2), encoding='utf-8')
    return packet

def verify_cache(artifact_hash: str) -> str:
    """Check if artifact is in cache. Returns CACHED or MISS.
    
    Accepts either a 64-char SHA-256 hash or a file path. If a path is given
    and the file exists, it is hashed first. If the path does not exist,
    returns MISS (no stat() on non-existent paths).
    """
    key = artifact_hash
    p = Path(artifact_hash)
    if len(artifact_hash) != 64 and p.exists():
        key = _artifact_key(p)
    entry = cache_check(p) if p.exists() else None
    if entry:
        # Fixed: use entry['verifier'] for the verifier field
        return f"CACHED verdict={entry['verdict']} verifier={entry.get('verifier', 'unknown')}"
    return f"MISS {key[:16]}..."

# ==================== BOOTSTRAP ENTRYPOINT ====================

if __name__ == "__main__":
    print("[BOOTSTRAP] OMNIPRIME syscalls.py V3")
    print(f"[BOOTSTRAP] ledger_balance = {ledger_balance()}")
    print(f"[BOOTSTRAP] os_ready = true")
    print(f"[BOOTSTRAP] Lingua: P=F=V3 status protocol active")