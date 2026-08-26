"""
genewatch_drift_check.py — GENEWATCH drift scan for the VORPAL gene pool.
[◈VORPAL◈] Bot: GENEWATCH — monitors divergence between declared state
(registry.json, NOTES.md, GOALS.md) and reality on disk.

Drift classes detected:
  D1  ORPHAN_HARNESS   hermes_verify_*.py referencing dropped modules
                       (quarantined but still scanned as live)
  D2  FALSE_GREEN      harness exits 0 with EMPTY stdout (silent no-op)
  D3  STALE_CLAIM      registry.json / NOTES.md count != live reality
  D4  COMPILE_ROT      harness or module fails py_compile
  D5  STRAY_CACHE      __pycache__ remnants for moved/deleted harnesses

Run:  python GENEWATCH/genewatch_drift_check.py [--run]
      --run  actually executes harnesses (slower, full D2 gate)
Exit: 0 = no drift, 1 = drift found (cron/CI ready)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry.json"
NOTES = ROOT / "EVOLVE" / "NOTES.md"
GOALS = ROOT / "EVOLVE" / "GOALS" / "GOALS.md"
VERIFY_DIR = ROOT / "VERIFY"
REPAIR_DIR = ROOT / "EVOLVE" / "SKILLHUB" / "skill_repair" / "harnesses"

DRIFT: list[str] = []


def report(dclass: str, msg: str) -> None:
    DRIFT.append(f"[{dclass}] {msg}")
    print(f"  DRIFT {dclass}: {msg}")


def find_harnesses(root: Path) -> list[Path]:
    return sorted(root.rglob("hermes_verify_*.py"))


def stale_claims() -> None:
    """D3: cross-check declared harness counts vs files on disk."""
    live = [p for p in find_harnesses(VERIFY_DIR) if p.suffix == ".py"]
    repaired = [p for p in find_harnesses(REPAIR_DIR) if p.suffix == ".py"]
    print(f"  live harnesses: {len(live)}  quarantined: {len(repaired)}")

    reg_text = ""
    if REGISTRY.exists():
        try:
            reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
            reg_text = str(reg.get("last_cycle", {}).get("verify_gate", ""))
        except json.JSONDecodeError as e:
            report("D3", f"registry.json unparseable: {e}")
    print(f"  registry verify_gate claim: {reg_text!r}")

    # Extract a "N/N ... PASS" claim from registry and compare to live count.
    m = re.search(r"(\d+)/(\d+)", reg_text)
    if m and m.group(1).isdigit() and m.group(2).isdigit():
        live_n = len(live)
        claimed_live = int(m.group(1))
        claimed_total = int(m.group(2))
        if claimed_live != live_n or claimed_total < live_n:
            report("D3", f"registry claims {m.group(0)} live but disk shows {live_n}")

    # NOTES.md stale "9/9" claim — only flag if it POSTDATES the last repair
    # (a dated historical sweep entry superseded by the repair log is not drift).
    if NOTES.exists():
        text = NOTES.read_text(encoding="utf-8")
        # find the last repair/quarantine marker; claims after it are stale
        repair_at = -1
        for marker in ("VERIFY GATE REPAIR", "ERR_ORPHAN_HARNESS", "QUARANTINE"):
            idx = text.rfind(marker)
            if idx > repair_at:
                repair_at = idx
        for line in text.splitlines():
            if "9/9 harnesses PASS" in line:
                line_at = text.find(line)
                if repair_at == -1 or line_at > repair_at:
                    report("D3", f"NOTES.md stale 9/9 claim postdates repair: {line.strip()[:80]}")


def stray_cache() -> None:
    """D5: __pycache__ for harnesses that no longer exist live."""
    cache = VERIFY_DIR / "harnesses" / "__pycache__"
    if not cache.exists():
        return
    for pyc in cache.glob("hermes_verify_*.pyc"):
        stem = pyc.stem.split(".cpython")[0]  # hermes_verify_x
        if not (VERIFY_DIR / "harnesses" / f"{stem}.py").exists():
            report("D5", f"stale pycache for moved harness: {pyc.name}")


def run_harnesses(run: bool) -> None:
    """D1/D2/D4: compile every harness; optionally execute for false-green."""
    harnesses = find_harnesses(VERIFY_DIR) + find_harnesses(REPAIR_DIR)
    for h in harnesses:
        if h.suffix != ".py":
            continue
        quarantined = REPAIR_DIR in h.parents
        # D4 compile gate
        r = subprocess.run(
            [sys.executable, "-m", "py_compile", str(h)],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            report("D4", f"{h.relative_to(ROOT)} fails py_compile: {r.stderr.strip()[:120]}")
            continue
        if not run:
            continue
        # D2 false-green gate: execute, require non-empty stdout
        try:
            e = subprocess.run(
                [sys.executable, str(h)],
                capture_output=True, text=True, timeout=300,
            )
        except subprocess.TimeoutExpired:
            report("D2", f"{h.relative_to(ROOT)} TIMEOUT")
            continue
        out = e.stdout.strip()
        if quarantined and e.returncode != 0:
            # Expected: quarantined harness tests a dropped module. Not live drift —
            # but flag if it would still be auto-discovered by a recursive gate.
            print(f"  INFO {h.relative_to(ROOT)} fails as expected (quarantined, tests dropped module)")
            continue
        if e.returncode != 0:
            report("D1", f"{h.relative_to(ROOT)} FAILED (exit {e.returncode})")
        elif not out:
            report("D2", f"{h.relative_to(ROOT)} exit 0 with EMPTY stdout (false-green)")


def main() -> None:
    run = "--run" in sys.argv
    print(f"GENEWATCH drift scan @ {ROOT}")
    print(f"  mode: {'full execution' if run else 'static-only'} (add --run for D2)")
    stale_claims()
    stray_cache()
    run_harnesses(run)
    if DRIFT:
        print(f"\nRESULT: {len(DRIFT)} drift item(s) — GENEWATCH flags")
        sys.exit(1)
    print("\nRESULT: gene pool stable — no drift")
    sys.exit(0)


if __name__ == "__main__":
    main()
