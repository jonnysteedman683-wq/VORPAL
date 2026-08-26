"""
trustcheck_ledger_audit.py — TRUSTCHECK ledger-integrity audit for VORPAL.
[◈VORPAL◈] Bot: TRUSTCHECK — verifies the money/state ledger is HONEST:
declared state matches reality, spend is sane, errors are logged, goals are
not marked [IMPLEMENTED] without an artifact on disk.

Audit classes (parallel to GENEWATCH D-classes):
  T1  LEDGER_LIE     registry.json field contradicts reality on disk
  T2  BAD_ENTRY      ledger_balance not int / last_spend not valid ISO
  T3  STALE_ERR      NOTES.md carries an [ERR_*] never closed / drifted
  T4  UNPROVEN_GOAL  GOALS.md [IMPLEMENTED: x] with no matching artifact
  T5  LEDGER_DRIFT   last_spend in the future or wildly inconsistent

Run:  python GENEWATCH/trustcheck_ledger_audit.py
Exit: 0 = ledger honest, 1 = audit findings (cron/CI ready)
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry.json"
NOTES = ROOT / "EVOLVE" / "NOTES.md"
GOALS = ROOT / "EVOLVE" / "GOALS" / "GOALS.md"

FINDINGS: list[str] = []


def report(tclass: str, msg: str) -> None:
    FINDINGS.append(f"[{tclass}] {msg}")
    print(f"  AUDIT {tclass}: {msg}")


def parse_iso(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def check_registry() -> None:
    """T1/T2: registry.json must be parseable, sane, and truthful."""
    if not REGISTRY.exists():
        report("T1", "registry.json missing")
        return
    try:
        reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report("T1", f"registry.json unparseable: {e}")
        return

    balance = reg.get("ledger_balance")
    if not isinstance(balance, int):
        report("T2", f"ledger_balance not an int: {balance!r}")

    last_spend = reg.get("last_spend", "")
    dt = parse_iso(last_spend)
    if dt is None:
        report("T2", f"last_spend not valid ISO: {last_spend!r}")
    elif dt > datetime.now(timezone.utc):
        report("T5", f"last_spend is in the future: {last_spend}")

    # T1: declared profile/lineage sanity
    if reg.get("profile") != "default":
        report("T1", f"registry profile={reg.get('profile')!r}, expected 'default'")

    vg = reg.get("last_cycle", {}).get("verify_gate", "")
    if vg and "PASS" not in vg and "green" not in vg.lower():
        report("T1", f"verify_gate claim neither PASS nor green: {vg!r}")

    # T5: ledger_balance vs spend — flag a non-positive balance.
    if isinstance(balance, int) and balance < 0:
        report("T5", f"ledger_balance negative: {balance}")


def check_errors() -> None:
    """T3: every [ERR_*] token in NOTES.md should be closed or acknowledged."""
    if not NOTES.exists():
        report("T3", "NOTES.md missing — cannot audit error ledger")
        return
    text = NOTES.read_text(encoding="utf-8")
    tokens = re.findall(r"\[(ERR_[A-Z0-9_]+)\]", text)
    if not tokens:
        return
    # A token is "open" if it appears in an entry lacking CLOSED/VERIFIED/fixed.
    # Simple heuristic: flag tokens that appear more than once (recurring = unresolved).
    from collections import Counter
    counts = Counter(tokens)
    for tok, n in counts.items():
        if n > 1:
            report("T3", f"{tok} recurs {n}x — unresolved or drifting error ledger")
    print(f"  err tokens in NOTES.md: {dict(counts)}")


def check_goals() -> None:
    """T4: [IMPLEMENTED: x] must have a matching artifact on disk.
    False-positive guards: strip HTML comment blocks (schema placeholders),
    accept directory-based implementations, and accept cross-repo artifacts
    (e.g. verify_all lives at OMNIPRIME/scripts/verify_all.py).
    Performance: pre-index sibling-repo .py filenames once (O(N+M))."""
    if not GOALS.exists():
        report("T4", "GOALS.md missing")
        return
    raw = GOALS.read_text(encoding="utf-8")
    # Strip HTML comment blocks so schema placeholders like [IMPLEMENTED: skill_id] are ignored.
    text = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)
    # Pre-index sibling-repo .py filenames once to avoid O(N*M) rglob.
    cross_repo_py: set[str] = set()
    for sibling in ROOT.parent.iterdir():
        if not sibling.is_dir() or sibling == ROOT:
            continue
        for p in sibling.rglob("*.py"):
            cross_repo_py.add(p.name)
    # Known GOALS.md spec inconsistencies: implementation tag -> actual dir name.
    # procedure_library (GOAL_5.4) lives in PROCEDURE/ — tag/dir mismatch in source spec.
    KNOWN_DIR_ALIASES = {"procedure_library": "PROCEDURE"}

    for m in re.finditer(r"\[IMPLEMENTED:\s*([a-zA-Z0-9_]+)\]", text):
        skill = m.group(1)
        candidates = list(ROOT.rglob(f"**/{skill}.py")) + list(ROOT.rglob(f"**/{skill}/**/SKILL.md"))
        if candidates:
            continue
        # directory-based implementation (case-insensitive, with alias fallback)
        skill_lower = skill.lower()
        alias_dir = KNOWN_DIR_ALIASES.get(skill, skill)
        if any(p.name.lower() == skill_lower or p.name.lower() == alias_dir.lower()
               for p in ROOT.rglob("**/*") if p.is_dir()):
            continue
        # cross-repo artifact (sibling workspace, e.g. OMNIPRIME/scripts/verify_all.py)
        if f"{skill}.py" in cross_repo_py:
            continue
        report("T4", f"[IMPLEMENTED: {skill}] no artifact, dir, or cross-repo hit found")


def main() -> None:
    print(f"TRUSTCHECK ledger audit @ {ROOT}")
    check_registry()
    check_errors()
    check_goals()
    if FINDINGS:
        print(f"\nRESULT: {len(FINDINGS)} audit finding(s) — TRUSTCHECK flags")
        sys.exit(1)
    print("\nRESULT: ledger honest — no findings")
    sys.exit(0)


if __name__ == "__main__":
    main()
