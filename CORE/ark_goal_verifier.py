#!/usr/bin/env python3
"""
ARK GOAL VERIFIER — GOAL_5.3 implementation [RATIFIED: 2026-08-23]

Verifies that every `[IMPLEMENTED: id]` claim in GOALS.md has a corresponding
file on disk in ARK-RUNTIME/ and passes a basic validation gate (syntax check
for .py files, existence for other artifacts).

Usage:
    from ark_goal_verifier import verify_goals, verify_goals_file

    report = verify_goals()           # verifies ARK-STATE/GOALS.md by default
    print(report["summary"])          # "24/24 claims verified"
    print(report["failed"])           # [] if all pass

    # Or verify a specific file
    report = verify_goals_file("ARK-OBJECTIVES/GOALS/GOALS.md")

This module is wired into ark_upgrade_engine.py as a pre-write gate:
any attempt to write an [IMPLEMENTED] tag for a missing or broken artifact
is rejected with a detailed error report.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# ARK root derived from this file's location
ARK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_DIR = os.path.join(ARK, "ARK-RUNTIME")
STATE_DIR = os.path.join(ARK, "ARK-STATE")
GOALS_FILE = os.path.join(STATE_DIR, "GOALS.md")

# Regex for [IMPLEMENTED: ark_xxx] tags
# Matches: [IMPLEMENTED: ark_name] or [IMPLEMENTED: assets/file.js]
IMPLEMENTED_RE = re.compile(r"\[IMPLEMENTED:\s*([^\]]+)\]")

# Files that are valid targets for IMPLEMENTED claims
# Maps artifact name → expected relative path from ARK root
KNOWN_PATHS = {
    # ARK-RUNTIME Python modules
    "ark_field": "ARK-RUNTIME/ark_field.py",
    "ark_forge": "ARK-RUNTIME/ark_forge.py",
    "ark_fracture": "ARK-RUNTIME/ark_fracture.py",
    "ark_fuse": "ARK-RUNTIME/ark_fuse.py",
    "ark_upgrade_engine": "ARK-RUNTIME/ark_upgrade_engine.py",
    "ark_autocommit": "ARK-RUNTIME/ark_autocommit.py",
    "ark_state_layer": "ARK-RUNTIME/ark_state_layer.py",
    "ark_state_memory_manager": "ARK-RUNTIME/ark_state_memory_manager.py",
    "ark_jsonl": "ARK-RUNTIME/ark_jsonl.py",
    "ark_path": "ARK-RUNTIME/ark_path.py",
    "ark_redqueen_core": "ARK-RUNTIME/ark_redqueen_core.py",
    "ark_retaliation_engine": "ARK-RUNTIME/ark_retaliation_engine.py",
    "ark_security_scanner": "ARK-RUNTIME/ark_security_scanner.py",
    "ark_sandbox": "ARK-RUNTIME/ark_sandbox.py",
    "ark_auto_debugger": "ARK-RUNTIME/ark_auto_debugger.py",
    "ark_archive": "ARK-RUNTIME/ark_archive.py",
    "ark_skill_curation_engine": "ARK-RUNTIME/ark_skill_curation_engine.py",
    "ark_skill_health_probe": "ARK-RUNTIME/ark_skill_health_probe.py",
    "ark_skill_edge_tuner": "ARK-RUNTIME/ark_skill_edge_tuner.py",
    "ark_skill_token_ledger": "ARK-RUNTIME/ark_skill_token_ledger.py",
    "ark_cost_ledger": "ARK-RUNTIME/ark_cost_ledger.py",
    "ark_feedback_loop": "ARK-RUNTIME/ark_feedback_loop.py",
    "ark_replication_engine": "ARK-RUNTIME/ark_replication_engine.py",
    "ark_vessel": "ARK-RUNTIME/ark_vessel.py",
    "ark_coordination_layer": "ARK-RUNTIME/ark_coordination_layer.py",
    "ark_neurocore_bridge": "ARK-RUNTIME/ark_neurocore_bridge.py",
    "ark_edge_optimizer": "ARK-RUNTIME/ark_edge_optimizer.py",
    "ark_self_healing": "ARK-RUNTIME/ark_self_healing.py",
    "ark_provenance_verifier": "ARK-RUNTIME/ark_provenance_verifier.py",
    "ark_dashboard_server": "ARK-RUNTIME/ark_dashboard_server.py",
    # Goal verifier
    "ark_goal_verifier": "ARK-RUNTIME/ark_goal_verifier.py",
    # Frontend assets
    "assets/telemetry.js": "assets/telemetry.js",
}


def _validate_python_file(path: Path) -> Optional[str]:
    """Validate a Python file compiles. Returns None on success, error msg on failure."""
    import py_compile
    try:
        py_compile.compile(str(path), doraise=True)
        return None
    except py_compile.PyCompileError as e:
        return str(e)


def _resolve_artifact_path(artifact_id: str) -> Optional[Path]:
    """Resolve an artifact ID to an absolute path. Returns None if unknown."""
    if artifact_id in KNOWN_PATHS:
        return Path(ARK) / KNOWN_PATHS[artifact_id]

    # Fallback: assume it's a relative path from ARK root
    candidate = Path(ARK) / artifact_id
    return candidate


def verify_goals_file(goals_path: str) -> Dict[str, Any]:
    """
    Verify all [IMPLEMENTED:] claims in a GOALS.md file.

    Args:
        goals_path: Absolute path to the GOALS.md file.

    Returns:
        Report dict:
        {
            "file": str,
            "total": int,
            "passed": int,
            "failed": int,
            "claims": List[Dict],     # per-claim details
            "failed_claims": List[Dict],
            "summary": str,
            "verified": bool,          # True if all pass
            "checked_at": str,         # ISO timestamp
        }
    """
    goals_path = str(goals_path)
    if not os.path.exists(goals_path):
        return {
            "file": goals_path,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "claims": [],
            "failed_claims": [],
            "summary": "GOALS file not found",
            "verified": False,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    with open(goals_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Only scan table rows (lines starting with '|'), skip blockquote
    # instructional lines (starting with '|>') and other content.
    table_lines = [l for l in lines if l.lstrip().startswith("|") and not l.lstrip().startswith("|>")]
    scanable = "\n".join(table_lines)

    matches = IMPLEMENTED_RE.findall(scanable)
    claims: List[Dict[str, Any]] = []
    failed_claims: List[Dict[str, Any]] = []
    passed = 0

    for raw_id in matches:
        artifact_id = raw_id.strip()
        abs_path = _resolve_artifact_path(artifact_id)
        claim: Dict[str, Any] = {
            "id": artifact_id,
            "path": str(abs_path) if abs_path else None,
            "exists": False,
            "valid": False,
            "error": None,
        }

        if abs_path is None:
            claim["error"] = f"Unknown artifact ID: {artifact_id}"
        elif not abs_path.exists():
            claim["error"] = f"File not found: {abs_path}"
        else:
            claim["exists"] = True
            # Validate by extension
            if abs_path.suffix == ".py":
                err = _validate_python_file(abs_path)
                if err:
                    claim["error"] = f"Syntax error: {err}"
                else:
                    claim["valid"] = True
                    passed += 1
            else:
                # Non-Python files: existence is enough
                claim["valid"] = True
                passed += 1

        if not claim["valid"]:
            failed_claims.append(claim)
        claims.append(claim)

    total = len(claims)
    failed = total - passed
    verified = failed == 0

    return {
        "file": goals_path,
        "total": total,
        "passed": passed,
        "failed": failed,
        "claims": claims,
        "failed_claims": failed_claims,
        "summary": f"{passed}/{total} claims verified" + ("" if verified else f" — {failed} FAILED"),
        "verified": verified,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def verify_goals() -> Dict[str, Any]:
    """Convenience: verify ARK-STATE/GOALS.md."""
    return verify_goals_file(GOALS_FILE)


def assert_goals_verified(goals_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify goals and return the report. If verification fails, the report
    contains all failure details for the caller to handle.

    This is the wiring point for the upgrade engine.
    """
    path = goals_path or GOALS_FILE
    report = verify_goals_file(path)
    return report


if __name__ == "__main__":
    import json
    report = verify_goals()
    print(json.dumps(report, indent=2, default=str))
