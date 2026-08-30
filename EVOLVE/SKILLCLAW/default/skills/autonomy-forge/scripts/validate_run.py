#!/usr/bin/env python3
"""Validate the deterministic shape of an Autonomy Forge run record."""
from __future__ import annotations
import json
import sys
from pathlib import Path


def fail(message: str) -> int:
    print(f"INVALID: {message}")
    return 1


def main() -> int:
    if len(sys.argv) != 3:
        return fail("usage: validate_run.py MANIFEST.json REPORT.json")
    try:
        manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        report = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(str(exc))
    required_manifest = {"run_id", "operator_intent", "targets", "actions", "success_criteria", "stop_conditions"}
    missing = sorted(required_manifest - manifest.keys())
    if missing:
        return fail("manifest missing: " + ", ".join(missing))
    if not isinstance(manifest["actions"], list) or not manifest["actions"]:
        return fail("manifest actions must be a non-empty list")
    for index, action in enumerate(manifest["actions"]):
        for key in ("id", "operation", "preconditions", "verification", "rollback", "risk"):
            if key not in action:
                return fail(f"action {index} missing: {key}")
    required_report = {"outcome", "run_id", "actions", "evidence", "failures_recovery", "changed_paths", "citadel"}
    missing = sorted(required_report - report.keys())
    if missing:
        return fail("report missing: " + ", ".join(missing))
    if report["run_id"] != manifest["run_id"]:
        return fail("manifest/report run_id mismatch")
    if report["outcome"] not in {"VERIFIED", "DEGRADED", "BLOCKED"}:
        return fail("outcome must be VERIFIED, DEGRADED, or BLOCKED")
    print("VALID: autonomy manifest and report shape verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
