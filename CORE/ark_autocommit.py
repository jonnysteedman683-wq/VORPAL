"""
ARK AUTO-COMMIT -- local git commit of ARK-only changes with provenance.

Runs unattended (Hermes cron). ARK is a SEPARATE repo from OMNICORE/OMNIPRIME.
This script WILL NOT touch sibling repos:
  - ARK root is derived as the parent of this file's directory.
  - A hard guard aborts if the resolved root is not named 'ARK'.
  - We never `git add -A` at a scope that could reach the Desktop.

Robustness:
- MSYS path de-mangling for git-bash/python-on-MSYS drive doubling.
- Explicit `git add` of known ARK subtrees only.
"""

import os
import sys
import subprocess
from datetime import datetime

# Derive ARK root as parent of the runtime directory
def fix_path(path):
    """Convert MSYS-style /c/ paths to native Windows paths."""
    if path.startswith('/'):
        parts = path.split('/')
        if len(parts) >= 3 and parts[1] in ('c:', 'd:', 'e:', 'f:'):
            drive = parts[1].upper().replace(':', '')
            rest = '/'.join(parts[2:])
            return f"{drive}:/{rest}"
        if len(parts) >= 2:
            drive = parts[1].upper().replace(':', '')
            rest = '/'.join(parts[2:]) if len(parts) > 2 else ''
            return f"{drive}:/{rest}"
    return path

ARK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Safety guard
if os.path.basename(ARK) != 'ARK':
    print(f"SAFETY ABORT: resolved ARK root '{ARK}' is not an ARK dir.")
    sys.exit(2)

# Scope: only known ARK subtrees
STAGE_PATHS = [
    'ARK-RUNTIME',
    'ARK-SKILLS',
    'ARK-SOUL',
    'tests',
    'assets',
    'README.md',
    'index.html',
]

def existing_stage_paths():
    """Return subset of STAGE_PATHS that actually exist."""
    return [p for p in STAGE_PATHS if os.path.exists(os.path.join(ARK, p))]


def run_provenance_gate():
    """
    Pre-commit provenance verification [RATIFIED: 2026-08-23].
    Scans identity-bearing files for uncited origin/creation/authorship
    claims (fabricated-metadata guard). Returns list of blocked files;
    empty list == gate green.
    """
    gate_findings = []
    try:
        from ark_provenance_verifier import scan_path
    except ImportError:
        print("PROVENANCE GATE: verifier module unavailable — failing open "
              "with warning [ERR_PROVENANCE_GATE_UNAVAILABLE]", file=sys.stderr)
        return []

    for rel in ("ARK-SOUL", "ARK-DIRECTIVES", "README.md"):
        full = os.path.join(ARK, rel)
        if os.path.isfile(full):
            candidates = [full]
        elif os.path.isdir(full):
            candidates = [
                os.path.join(dirpath, fn)
                for dirpath, _, fns in os.walk(full)
                for fn in fns if fn.lower().endswith(('.md', '.py'))
            ]
        else:
            continue

        for path in candidates:
            r = scan_path(path)
            if not r.get("clean", True):
                gate_findings.append(r)

    if gate_findings:
        print("PROVENANCE GATE: BLOCKED — uncited origin claims found:", file=sys.stderr)
        for f in gate_findings:
            print(f"  {f['path']}", file=sys.stderr)
            for finding in f.get("findings", []):
                print(f"    - [{finding['severity']}] {finding['claim'][:120]}", file=sys.stderr)
                print(f"      ({finding['reason']})", file=sys.stderr)
    else:
        print("PROVENANCE GATE: clean")
    return gate_findings


def run_goal_verification_gate():
    """
    Pre-commit goal verification [GOAL_5.3 — RATIFIED: 2026-08-23].
    Verifies all [IMPLEMENTED:] claims in GOALS.md have corresponding files
    on disk. Returns list of failed claims; empty list == gate green.
    """
    failed_claims = []
    try:
        from ark_goal_verifier import verify_goals
    except ImportError:
        print("GOAL VERIFICATION: verifier module unavailable — failing open "
              "with warning [ERR_GOAL_VERIFICATION_UNAVAILABLE]", file=sys.stderr)
        return []

    report = verify_goals()
    if not report.get("verified", False):
        failed_claims = report.get("failed_claims", [])
        print(f"GOAL VERIFICATION: FAILED — {len(failed_claims)} claim(s) invalid:", file=sys.stderr)
        for c in failed_claims:
            print(f"  {c['id']}: {c['error']}", file=sys.stderr)
    else:
        print(f"GOAL VERIFICATION: {report['summary']}")
    return failed_claims


def main():
    """Commit ARK-only changes with provenance."""
    # Check git is available
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("git not available", file=sys.stderr)
        sys.exit(1)
    
    # Pre-commit provenance gate [SOUL Inv.3: Provenance or Perish]
    gate_blockers = run_provenance_gate()
    if gate_blockers:
        print("Auto-commit aborted by provenance gate. Fix the cited-claim "
              "violations above (add [cite: ...], a repo-file reference, or a "
              "URL) or remove the fabricated claim.", file=sys.stderr)
        sys.exit(3)

    # Pre-commit goal verification gate [GOAL_5.3]
    goal_blockers = run_goal_verification_gate()
    if goal_blockers:
        print("Auto-commit aborted by goal verification gate. Fix the "
              "[IMPLEMENTED:] claim violations above (create the missing file "
              "or remove the claim).", file=sys.stderr)
        sys.exit(4)
    
    # Check for changes
    result = subprocess.run(
        ['git', 'status', '--short'],
        cwd=ARK,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("git status failed", file=sys.stderr)
        sys.exit(1)
    
    changes = result.stdout.strip()
    if not changes:
        print("No changes to commit")
        sys.exit(0)
    
    # Stage known paths only
    for rel_path in existing_stage_paths():
        full_path = os.path.join(ARK, rel_path)
        if os.path.isdir(full_path):
            subprocess.run(
                ['git', 'add', rel_path],
                cwd=ARK,
                capture_output=True,
            )
        else:
            subprocess.run(
                ['git', 'add', rel_path],
                cwd=ARK,
                capture_output=True,
            )
    
    # Commit with provenance
    timestamp = datetime.utcnow().isoformat()
    msg = f"ARK auto-commit: {timestamp}\n\nAutomated commit of ARK-only changes."
    result = subprocess.run(
        ['git', 'commit', '-m', msg],
        cwd=ARK,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        print(f"Commit failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    # Show last commit
    subprocess.run(
        ['git', 'log', '-1', '--oneline'],
        cwd=ARK,
        capture_output=True,
    )


if __name__ == '__main__':
    main()
