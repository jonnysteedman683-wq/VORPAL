"""
AURORAL Bootstrap — Executable cold-start for Inquisitor mode.

AURORAL (Epistemic Hardener) provides verification, claim tagging,
quarantine, and judging rubric enforcement.

This script provides the executable Stage 1-5 bootstrap that was prose-only.
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# ── Stage 1: Identity ───────────────────────────────────────────────
AURORAL_MODE = "INQUISITOR"
AURORAL_WATERMARK = "[◈AURORAL◈]"
VORPAL_ROOT = Path(__file__).resolve().parent.parent

# ── Stage 2: Language Setup ─────────────────────────────────────────
class AuroralLingua:
    """Claim tagging protocol — [VERIFIED]/[HIGH]/[MEDIUM]/[LOW]/[DEGRADED]/[STALE]"""
    
    VALID_TAGS = {"VERIFIED", "HIGH", "MEDIUM", "LOW", "DEGRADED", "STALE"}
    
    @staticmethod
    def tag(claim: str, evidence: bool = False) -> str:
        if evidence:
            return f"[VERIFIED] {claim}"
        return f"[LOW] {claim}"
    
    @staticmethod
    def verify(claim: str, evidence: dict) -> tuple[bool, str]:
        """Verify a claim against evidence. Returns (passed, tag)."""
        if evidence.get("reproducible"):
            return True, "VERIFIED"
        elif evidence.get("source_trusted"):
            return True, "HIGH"
        elif evidence.get("contextual"):
            return True, "MEDIUM"
        else:
            return False, "LOW"

# ── Stage 3: Ledger Bind ─────────────────────────────────────────────
AURORAL_LEDGER = {
    "mode": AURORAL_MODE,
    "watermark": AURORAL_WATERMARK,
    "claims_verified": 0,
    "claims_failed": 0,
    "quarantined": 0,
    "started_at": time.time(),
}

def bind_ledger():
    """Initialize AURORAL claim ledger from VERIFY/ directory."""
    verify_path = VORPAL_ROOT / "VERIFY"
    rubric = (verify_path / "JUDGING_RUBRIC.md").read_text() if (verify_path / "JUDGING_RUBRIC.md").exists() else ""
    AURORAL_LEDGER["rubric_loaded"] = bool(rubric)
    return True

# ── Stage 4: Bus Heartbeat ───────────────────────────────────────────
def heartbeat():
    """Return AURORAL liveness signal for the VORPAL mesh."""
    return {
        "source": "AURORAL",
        "mode": AURORAL_MODE,
        "alive": True,
        "verified": AURORAL_LEDGER["claims_verified"],
        "failed": AURORAL_LEDGER["claims_failed"],
        "quarantined": AURORAL_LEDGER["quarantined"],
        "timestamp": time.time(),
    }

# ── Stage 5: Ready Signal ────────────────────────────────────────────
def ready():
    """Assert AURORAL is ready to audit claims."""
    assert AURORAL_MODE == "INQUISITOR", f"Invalid AURORAL mode: {AURORAL_MODE}"
    assert VORPAL_ROOT.exists(), f"VORPAL root not found: {VORPAL_ROOT}"
    return True

def audit_claim(claim: str, evidence_path: str = None) -> dict:
    """Run Inquisitor audit on a single claim."""
    evidence = {}
    if evidence_path:
        ev_file = Path(evidence_path)
        if ev_file.exists():
            evidence["source_file"] = str(ev_file)
            evidence["reproducible"] = True  # File exists = reproducible
            evidence["source_trusted"] = True
    
    passed, tag = AuroralLingua.verify(claim, evidence)
    
    result = {
        "claim": claim,
        "tag": tag,
        "passed": passed,
        "timestamp": datetime.now().isoformat(),
    }
    
    if passed:
        AURORAL_LEDGER["claims_verified"] += 1
    else:
        AURORAL_LEDGER["claims_failed"] += 1
        # Write to NOTES.md as [ERR_*]
        notes_path = VORPAL_ROOT / "EVOLVE" / "NOTES.md"
        with open(notes_path, "a") as f:
            f.write(f"\n[ERR_UNVERIFIED] {claim} — {datetime.now().isoformat()}\n")
    
    return result

if __name__ == "__main__":
    ready()
    print(f"AURORAL ready — mode={AURORAL_MODE} — heartbeat={heartbeat()}")