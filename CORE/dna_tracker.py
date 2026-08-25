"""
DNA Manifest Tracker — Triad Codebase Evolution Engine v2.0

3-LINEAGE CROSS-POLLINATION WITH DONOR INJECTION, PURPOSE BIAS, AND DRIFT-CORRECTING REVERSE

Lineage map:
  ark        → orchestration / routing / user-interface DNA
  auroral    → verification / audit / AST DNA
  omniprime  → execution / build / DAG DNA
  donor      → pure novelty source (injects only, never receives)

Phase logic (per workspace, priority order):
  1. REPRODUCE  — namesake DNA >=70% AND cross_cycles >=10
  2. SELF-INTEGRATE — every 5th cycle, all lineages self-integrate
  3. CROSS-REVERSE  — any codebase namesake DNA <40%, reverse ring for recovery
  4. CROSS-FORWARD  — default

Donor injects into all 3 lineages every cycle at DONOR_INJECT_RATE (default 15%).
Donor never receives. Donor DNA is included in ratios but donor cannot trigger REPRODUCE.

Purpose bias: the namesake profile's commits count at PURPOSE_BIAS_WEIGHT (default 1.5x),
so each lineage retains its identity despite cross-pollination.

Usage:
    python dna_tracker.py status                  # full report
    python dna_tracker.py record <workspace> <profile>  # record commit
    python dna_tracker.py phase [workspace]        # phase check
    python dna_tracker.py evolve                  # run one evolution cycle
    python dna_tracker.py reverse                 # manual ring flip
    python dna_tracker.py set <forward|reverse>   # set ring direction
    python dna_tracker.py inject <workspace>      # donor inject into workspace
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

DESKTOP = Path(r"C:\Users\jonny\OneDrive\Desktop")
TRIAD_ROOT = DESKTOP / "TRIAD CO-ORDINATION AND EVOLUTION"

WORKSPACES = {
    "ark": DESKTOP / "ARK",
    "auroral": DESKTOP / "AURORAL",
    "omniprime": DESKTOP / "OMNIPRIME",
}

# Forward ring: profile X works-on workspace Y (donor excluded — injects only)
CROSS_FORWARD = {
    "ark": "auroral",
    "auroral": "omniprime",
    "omniprime": "ark",
}

# Reverse ring: opposite direction
CROSS_REVERSE = {
    "ark": "omniprime",
    "auroral": "ark",
    "omniprime": "auroral",
}

# Donor workspace (4th, injects but never receives)
DONOR_WORKSPACE = DESKTOP / "DONOR"

# Self-integration routing (loop recovery)
SELF_ROUTING = {
    "ark": "ark",
    "auroral": "auroral",
    "omniprime": "omniprime",
}

# Purpose bias: each workspace's core identity profile
# When this profile commits, its weight is multiplied
CORE_PROFILE = {
    "ark": "ark",
    "auroral": "auroral",
    "omniprime": "omniprime",
}

# Donor profile — injects but never receives
DONOR_PROFILE = "donor"
DONOR_INJECT_TARGETS = ["ark", "auroral", "omniprime"]

# --- Thresholds ---
REPRODUCTION_DNA_THRESHOLD = 0.70  # namesake DNA ratio needed
REPRODUCTION_CYCLE_THRESHOLD = 10  # min cross-pollinate cycles
SELF_INTEGRATE_INTERVAL = 5       # every N cycles, self-integrate

DRIFT_REVERSE_THRESHOLD = 0.40    # trigger reverse if namesake DNA < 40%
DRIFT_RECOVERY_CYCLES = 3         # reverse for N cycles to recover

PURPOSE_BIAS_WEIGHT = 1.5         # core profile commits count 1.5x
DONOR_INJECT_RATE = 0.15          # donor injects 15% of cycle's commits

MANIFEST_FILENAME = "dna_manifest.json"
STATE_FILE = TRIAD_ROOT / "dna_state.json"

# Import thinking modes
sys.path.insert(0, str(TRIAD_ROOT))
from thinking_modes import (
    THINKING_MODES, LINEAGE_NATIVE_MODE,
    derive_brain_profile, brain_profile_to_text,
    init_brain_profile, update_brain_profile_from_dna,
)


ALL_PROFILES = list(WORKSPACES) + [DONOR_PROFILE]  # known profiles


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------

def manifest_path(workspace_key: str) -> Path:
    return WORKSPACES[workspace_key] / MANIFEST_FILENAME


def load_manifest(workspace_key: str) -> dict:
    p = manifest_path(workspace_key)
    if not p.exists():
        return empty_manifest(workspace_key)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty_manifest(workspace_key)


def empty_manifest(workspace_key: str) -> dict:
    return {
        "codebase": workspace_key,
        "total_commits": 0,
        "dna": {p: 0.0 for p in ALL_PROFILES},
        "raw_counts": {p: 0 for p in ALL_PROFILES},
        "weighted_commits": 0.0,
        "cross_pollinate_cycles": 0,
        "self_integrate_cycles": 0,
        "donor_injects": 0,
        "reproduction_ready": False,
        "reproduced": False,
        "generation": 1,
        "last_profile": None,
        "last_commit_hash": None,
        "phase_history": [],
        "brain_profile": init_brain_profile({"codebase": workspace_key}),
    }


def save_manifest(workspace_key: str, manifest: dict) -> None:
    p = manifest_path(workspace_key)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {
            "cycle": 0,
            "global_phase": "CROSS-POLLINATE",
            "ring_direction": "forward",
            "drift_recovery_remaining": 0,
        }
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {
            "cycle": 0,
            "global_phase": "CROSS-POLLINATE",
            "ring_direction": "forward",
            "drift_recovery_remaining": 0,
        }


def save_state(state: dict) -> None:
    if not TRIAD_ROOT.exists():
        TRIAD_ROOT.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Git attribution
# ---------------------------------------------------------------------------

def get_git_author_profile(workspace_key: str) -> str | None:
    """Infer which profile authored the most recent commit."""
    ws = WORKSPACES[workspace_key]
    if not (ws / ".git").exists():
        return None
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%an|%ae"],
            capture_output=True, text=True, timeout=15, cwd=str(ws),
        )
        if r.returncode != 0:
            return None
        author = r.stdout.strip().lower()
    except (subprocess.TimeoutExpired, OSError):
        return None
    profile_hints = {
        "ark": ["ark", "jonny", "orchestrator"],
        "auroral": ["auroral", "auditor", "verify"],
        "omniprime": ["omniprime", "prime", "executor"],
        "donor": ["donor", "inject", "seed"],
    }
    for profile, hints in profile_hints.items():
        for hint in hints:
            if hint in author:
                return profile
    return None


def get_latest_commit_hash(workspace_key: str) -> str | None:
    ws = WORKSPACES[workspace_key]
    if not (ws / ".git").exists():
        return None
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%H"],
            capture_output=True, text=True, timeout=15, cwd=str(ws),
        )
        if r.returncode != 0:
            return None
        return r.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return None


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def record_commit(workspace_key: str, profile: str | None = None,
                  weight: float = 1.0, force: bool = False) -> dict:
    """Record a commit in a workspace's DNA manifest with optional weight.
    force=True bypasses git hash dedup (for synthetic events like donor injects)."""
    manifest = load_manifest(workspace_key)
    if profile is None:
        profile = get_git_author_profile(workspace_key)
    if profile is None:
        profile = "unknown"

    if not force:
        commit_hash = get_latest_commit_hash(workspace_key)
        if commit_hash and commit_hash == manifest.get("last_commit_hash"):
            return manifest
        if commit_hash:
            manifest["last_commit_hash"] = commit_hash
    else:
        # Synthetic event (donor inject / cycle-work deposit): the hash is
        # overwritten unconditionally, so querying git first was a wasted
        # subprocess on EVERY deposit -- ~0.3s each on Windows, which is what
        # pushed this module's harness past the 60s triad_index timeout.
        import uuid
        manifest["last_commit_hash"] = f"synthetic_{uuid.uuid4().hex[:12]}"

    manifest["total_commits"] += 1
    manifest["weighted_commits"] += weight

    raw = manifest["raw_counts"]
    raw[profile] = raw.get(profile, 0) + weight

    total = sum(raw.values())
    if total > 0:
        manifest["dna"] = {p: round(raw.get(p, 0) / total, 4) for p in ALL_PROFILES}
    else:
        manifest["dna"] = {p: 0.0 for p in ALL_PROFILES}

    manifest["last_profile"] = profile
    save_manifest(workspace_key, manifest)
    return manifest


def record_weighted_commit(workspace_key: str, profile: str | None = None,
                           force: bool = False) -> dict:
    """Record a commit with purpose bias applied.

    force=True records a synthetic cycle-work event (bypasses git-hash dedup).
    Needed because donor injects are forced while worker deposits were not --
    see [ERR_DNA_DONOR_MONOCULTURE] in cmd_evolve.
    """
    if profile is None:
        profile = get_git_author_profile(workspace_key)
    if profile is None:
        profile = "unknown"

    weight = 1.0
    # Apply purpose bias if this profile is the workspace's core
    core = CORE_PROFILE.get(workspace_key)
    if core and profile == core:
        weight = PURPOSE_BIAS_WEIGHT

    return record_commit(workspace_key, profile, weight, force=force)


def record_donor_inject(workspace_key: str) -> dict:
    """Record a donor injection into a workspace."""
    manifest = load_manifest(workspace_key)
    manifest["donor_injects"] += 1
    save_manifest(workspace_key, manifest)
    # Bypass git hash dedup with force=True
    return record_commit(workspace_key, DONOR_PROFILE, weight=1.0, force=True)


def update_cycle_counts(workspace_key: str) -> dict:
    """Increment the appropriate cycle counter."""
    state = load_state()
    manifest = load_manifest(workspace_key)
    global_phase = state.get("global_phase", "CROSS-POLLINATE")

    if global_phase in ("CROSS-POLLINATE", "CROSS-REVERSE"):
        # [ERR_DNA_CROSS_UNCOUNTED]: only "CROSS-POLLINATE" used to count, but a
        # CROSS-REVERSE cycle IS cross-pollination -- the ring direction flips,
        # the activity does not (a reverse cycle still deposits a FOREIGN
        # profile's DNA into each workspace). Because drift recovery pins the
        # phase to CROSS-REVERSE whenever namesake DNA < 40%, the counter was
        # frozen at 0 forever, and the REPRODUCE gate's cross_cycles >= 10
        # requirement could never be satisfied.
        manifest["cross_pollinate_cycles"] += 1
    elif global_phase == "SELF-INTEGRATE":
        manifest["self_integrate_cycles"] += 1

    save_manifest(workspace_key, manifest)
    return manifest


# ---------------------------------------------------------------------------
# Phase determination
# ---------------------------------------------------------------------------

def check_drift(workspace_key: str) -> bool:
    """Check if a codebase has drifted below threshold."""
    manifest = load_manifest(workspace_key)
    namesake_dna = manifest["dna"].get(workspace_key, 0.0)
    return namesake_dna < DRIFT_REVERSE_THRESHOLD


def determine_phase(workspace_key: str) -> str:
    """Determine what phase a codebase should be in."""
    manifest = load_manifest(workspace_key)

    # Reproduction (highest priority)
    namesake_dna = manifest["dna"].get(workspace_key, 0.0)
    enough_cycles = manifest["cross_pollinate_cycles"] >= REPRODUCTION_CYCLE_THRESHOLD
    if (namesake_dna >= REPRODUCTION_DNA_THRESHOLD
            and enough_cycles
            and not manifest.get("reproduced", False)):
        return "REPRODUCE"

    state = load_state()
    global_phase = state.get("global_phase")

    # Self-integrate (overrides drift recovery)
    if global_phase == "SELF-INTEGRATE":
        return "SELF-INTEGRATE"

    # Drift-correcting reverse
    if global_phase == "CROSS-REVERSE":
        return "CROSS-REVERSE"

    # Cycle-based self-integrate fallback
    cycle = state.get("cycle", 0)
    if cycle > 0 and cycle % SELF_INTEGRATE_INTERVAL == 0:
        return "SELF-INTEGRATE"

    # Default: forward
    return "CROSS-FORWARD"


def get_cross_routing() -> dict:
    """Return cross-pollination routing based on current ring direction."""
    state = load_state()
    direction = state.get("ring_direction", "forward")
    if direction == "reverse":
        return CROSS_REVERSE
    return CROSS_FORWARD


def get_effective_routing(workspace_key: str) -> dict:
    """Return the routing dict for the current phase."""
    phase = determine_phase(workspace_key)
    if phase == "SELF-INTEGRATE":
        return SELF_ROUTING
    return get_cross_routing()


def get_worker_for_codebase(workspace_key: str) -> str:
    """Which profile should work on this codebase right now?"""
    phase = determine_phase(workspace_key)
    if phase == "SELF-INTEGRATE":
        return workspace_key
    routing = get_cross_routing()
    for p, target in routing.items():
        if target == workspace_key:
            return p
    return "?"


def check_reproduction_readiness(workspace_key: str) -> dict:
    """Full reproduction readiness report."""
    manifest = load_manifest(workspace_key)
    namesake_dna = manifest["dna"].get(workspace_key, 0.0)
    checks = {
        "namesake_dna": namesake_dna,
        "dna_threshold": REPRODUCTION_DNA_THRESHOLD,
        "dna_pass": namesake_dna >= REPRODUCTION_DNA_THRESHOLD,
        "cross_cycles": manifest["cross_pollinate_cycles"],
        "cycle_threshold": REPRODUCTION_CYCLE_THRESHOLD,
        "cycle_pass": manifest["cross_pollinate_cycles"] >= REPRODUCTION_CYCLE_THRESHOLD,
        "not_already_reproduced": not manifest.get("reproduced", False),
        "generation": manifest.get("generation", 1),
    }
    checks["ready"] = (checks["dna_pass"] and checks["cycle_pass"]
                       and checks["not_already_reproduced"])
    return checks


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def status_report() -> str:
    lines = [
        "# DNA MANIFEST STATUS",
        f"_Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
    ]
    state = load_state()
    direction = state.get("ring_direction", "forward")
    drift_remaining = state.get("drift_recovery_remaining", 0)
    lines.append(
        f"**Global cycle:** {state.get('cycle', 0)} | "
        f"**Global phase:** {state.get('global_phase', 'CROSS-POLLINATE')} | "
        f"**Ring:** {direction.upper()}"
    )
    if drift_remaining > 0:
        lines.append(f"**Drift recovery:** {drift_remaining} cycles remaining")
    lines.append("")

    # Donor summary
    total_donor = sum(load_manifest(ws)["donor_injects"] for ws in WORKSPACES)
    lines.append(f"**Donor injects:** {total_donor} total across triad")
    lines.append("")

    for ws_key in WORKSPACES:
        m = load_manifest(ws_key)
        phase = determine_phase(ws_key)
        worker = get_worker_for_codebase(ws_key)
        repro = check_reproduction_readiness(ws_key)

        lines.append(f"## {ws_key.upper()}")
        lines.append(f"- Phase: **{phase}** | Worker: **{worker}** | Gen: **{m.get('generation', 1)}**")
        lines.append(
            f"- DNA: ark={m['dna'].get('ark', 0):.0%} | "
            f"auroral={m['dna'].get('auroral', 0):.0%} | "
            f"omniprime={m['dna'].get('omniprime', 0):.0%} | "
            f"donor={m['dna'].get('donor', 0):.0%}"
        )
        lines.append(
            f"- Commits: {m['total_commits']} (weighted: {m['weighted_commits']:.1f}) | "
            f"Cross cycles: {m['cross_pollinate_cycles']} | "
            f"Self cycles: {m['self_integrate_cycles']} | "
            f"Donor injects: {m['donor_injects']}"
        )

        if repro["ready"]:
            lines.append(f"- 🧬 **REPRODUCTION READY** — can spawn gen {m.get('generation', 1) + 1}")
        elif repro["dna_pass"] and not repro["cycle_pass"]:
            remaining = REPRODUCTION_CYCLE_THRESHOLD - m["cross_pollinate_cycles"]
            lines.append(f"- ⏳ DNA threshold met, {remaining} more cycles needed")
        elif not repro["dna_pass"]:
            needed = REPRODUCTION_DNA_THRESHOLD - m['dna'].get(ws_key, 0)
            lines.append(f"- ⏳ Need {needed:.0%} more {ws_key} DNA")

        if check_drift(ws_key):
            lines.append(f"- ⚠️ **DRIFT WARNING** — namesake DNA {m['dna'].get(ws_key, 0):.0%} < {DRIFT_REVERSE_THRESHOLD:.0%}")

        # Brain profile
        profile = update_brain_profile_from_dna(m)
        save_manifest(ws_key, m)
        sorted_modes = sorted(profile.items(), key=lambda x: -x[1])
        mode_strs = []
        for mode, weight in sorted_modes:
            meta = THINKING_MODES[mode]
            marker = "◉" if weight == max(profile.values()) else "○"
            mode_strs.append(f"{marker} {meta['icon']} {meta['name']} {weight:.0%}")
        lines.append(f"- Brain: {' | '.join(mode_strs)}")

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main CLI
# ---------------------------------------------------------------------------

def cmd_status():
    print(status_report())


def cmd_record(args: list):
    if len(args) < 1:
        print("Usage: python dna_tracker.py record <workspace> [profile]")
        return
    ws = args[0].lower()
    if ws not in WORKSPACES:
        print(f"Unknown workspace: {ws}. Use: {list(WORKSPACES)}")
        return
    profile = args[1].lower() if len(args) > 1 else None
    m = record_weighted_commit(ws, profile)
    dna_str = ", ".join(f"{p}={m['dna'].get(p, 0):.0%}" for p in ALL_PROFILES)
    print(f"Recorded commit in {ws} by {m.get('last_profile', '?')}. DNA: {dna_str}")


def cmd_phase(args: list):
    if args:
        ws = args[0].lower()
        if ws not in WORKSPACES:
            print(f"Unknown workspace: {ws}")
            return
        phase = determine_phase(ws)
        worker = get_worker_for_codebase(ws)
        repro = check_reproduction_readiness(ws)
        drift = check_drift(ws)
        print(f"{ws}: phase={phase} worker={worker} ready={repro['ready']} drift={drift}")
        dna_parts = []
        for p in ALL_PROFILES:
            if p == ws:
                val = repro["namesake_dna"]
            else:
                val = load_manifest(ws)["dna"].get(p, 0)
            dna_parts.append(f"{p}={val:.0%}")
        print(f"  DNA: {', '.join(dna_parts)}")
    else:
        for ws in WORKSPACES:
            phase = determine_phase(ws)
            worker = get_worker_for_codebase(ws)
            repro = check_reproduction_readiness(ws)
            drift = check_drift(ws)
            m = load_manifest(ws)
            namesake = m['dna'].get(ws, 0)
            flag = "🧬" if repro["ready"] else "⚠️" if drift else "⏳"
            print(f"{flag} {ws}: phase={phase} worker={worker} "
                  f"namesake={namesake:.0%} donor={m['dna'].get('donor',0):.0%} "
                  f"ready={repro['ready']}")


def cmd_evolve():
    """Full evolution cycle."""
    state = load_state()
    state["cycle"] = state.get("cycle", 0) + 1
    n = state["cycle"]

    # Check drift — any codebase below threshold?
    drifted = [ws for ws in WORKSPACES if check_drift(ws)]

    # Determine global phase
    if n % SELF_INTEGRATE_INTERVAL == 0:
        state["global_phase"] = "SELF-INTEGRATE"
    elif drifted and state.get("drift_recovery_remaining", 0) == 0:
        # Start drift recovery: reverse for N cycles
        state["global_phase"] = "CROSS-REVERSE"
        state["drift_recovery_remaining"] = DRIFT_RECOVERY_CYCLES
    elif state.get("drift_recovery_remaining", 0) > 0:
        # Continue drift recovery
        state["global_phase"] = "CROSS-REVERSE"
        state["drift_recovery_remaining"] -= 1
    else:
        state["global_phase"] = "CROSS-POLLINATE"

    # Set ring direction
    if state["global_phase"] == "CROSS-REVERSE":
        state["ring_direction"] = "reverse"
    elif state["global_phase"] == "CROSS-POLLINATE":
        # Auto-flip forward direction every 3rd cross cycle (gentle oscillation)
        cross_cycles = sum(load_manifest(ws)["cross_pollinate_cycles"] for ws in WORKSPACES) // 3
        state["ring_direction"] = "forward" if cross_cycles % 2 == 0 else "reverse"

    save_state(state)

    # Update cycle counts
    for ws in WORKSPACES:
        update_cycle_counts(ws)

    # --- Worker DNA deposit -------------------------------------------------
    # [ERR_DNA_DONOR_MONOCULTURE]: this cycle previously recorded ONLY donor
    # injects (one per workspace, i.e. a 100% donor rate despite
    # DONOR_INJECT_RATE=0.15), and the worker's own contribution was never
    # recorded at all. raw_counts could therefore contain nothing but `donor`:
    #   * namesake DNA pinned at 0% -> DRIFT WARNING permanent and unclearable
    #   * check_drift() always True -> phase pinned to CROSS-REVERSE forever
    #     -> cross_pollinate_cycles frozen at 0
    #   * REPRODUCE gate (namesake >= 70% AND cross >= 10) mathematically
    #     unreachable -> gen-2 spawn structurally impossible
    # A cycle of real work must deposit the WORKER's DNA into the workspace it
    # worked on. force=True is required for symmetry: donor injects bypass the
    # git-hash dedup, so an unforced worker deposit would be silently dropped
    # on every cycle where git HEAD had not moved (ARK/OMNIPRIME are repos),
    # which is the exact asymmetry that produced the monoculture.
    routing = SELF_ROUTING if state["global_phase"] == "SELF-INTEGRATE" \
        else get_cross_routing()
    deposits = 0
    for profile, target_ws in routing.items():
        if target_ws in WORKSPACES:
            record_weighted_commit(target_ws, profile, force=True)
            deposits += 1

    # --- Donor injection at the declared rate -------------------------------
    # Honour DONOR_INJECT_RATE instead of injecting into every workspace every
    # cycle. Deterministic accumulator (no RNG, reproducible) + rotating target
    # so no single workspace absorbs all novelty.
    acc = state.get("donor_inject_accumulator", 0.0) + DONOR_INJECT_RATE * deposits
    injects = int(acc)
    state["donor_inject_accumulator"] = round(acc - injects, 6)
    ws_keys = list(WORKSPACES)
    for i in range(injects):
        record_donor_inject(ws_keys[(n + i) % len(ws_keys)])
    state["last_cycle_deposits"] = deposits
    state["last_cycle_donor_injects"] = injects
    save_state(state)

    print(f"\n=== DNA EVOLUTION CYCLE {n} ===")
    print(f"Worker deposits: {deposits} ({state['global_phase']} routing) | "
          f"donor injects: {injects} (rate {DONOR_INJECT_RATE:.0%}, "
          f"carry {state['donor_inject_accumulator']})")
    print(status_report())


def cmd_reverse():
    """Manually flip ring direction."""
    state = load_state()
    current = state.get("ring_direction", "forward")
    new_dir = "reverse" if current == "forward" else "forward"
    state["ring_direction"] = new_dir
    save_state(state)
    print(f"Ring direction: {current.upper()} -> {new_dir.upper()}")
    routing = get_cross_routing()
    for p, target in routing.items():
        print(f"  {p} -> {target}/codebase")


def cmd_set(args: list):
    """Set ring direction explicitly."""
    if not args:
        state = load_state()
        print(f"Ring direction: {state.get('ring_direction', 'forward').upper()}")
        print("Usage: python dna_tracker.py set <forward|reverse>")
        return
    direction = args[0].lower()
    if direction not in {"forward", "reverse"}:
        print(f"Invalid direction: {direction}. Use: forward, reverse")
        return
    state = load_state()
    state["ring_direction"] = direction
    save_state(state)
    print(f"Ring direction set to: {direction.upper()}")


def cmd_inject(args: list):
    """Manually inject donor DNA into a workspace."""
    if not args:
        print("Usage: python dna_tracker.py inject <workspace>")
        return
    ws = args[0].lower()
    if ws not in WORKSPACES:
        print(f"Unknown workspace: {ws}")
        return
    m = record_donor_inject(ws)
    dna_str = ", ".join(f"{p}={m['dna'].get(p, 0):.0%}" for p in ALL_PROFILES)
    print(f"Donor injected into {ws}. DNA: {dna_str}")


def cmd_brain(args: list):
    """Show brain profile for a workspace or all workspaces."""
    if args and args[0] in WORKSPACES:
        ws = args[0]
        m = load_manifest(ws)
        profile = update_brain_profile_from_dna(m)
        save_manifest(ws, m)
        print(f"\n{ws.upper()} BRAIN PROFILE:")
        print(brain_profile_to_text(profile))
        print(f"\nDNA: {m['dna']}")
    else:
        print("THINKING MODES:")
        print()
        for mode, meta in THINKING_MODES.items():
            print(f"  {meta['icon']}  {meta['name'].upper()}  ({mode})")
            print(f"     {meta['description'][:80]}")
            print(f"     Latency: {meta['latency']:8s}  Compute: {meta['compute']:8s}")
            print(f"     Strengths: {', '.join(meta['strengths'][:3])}")
            print()
        print("DNA → MODE MAP:")
        for lineage, mode in LINEAGE_NATIVE_MODE.items():
            print(f"  {lineage:12s} → {THINKING_MODES[mode]['icon']}  {mode}")
        print()
        print("Usage: python dna_tracker.py brain <workspace> for profile detail")


def main():
    if len(sys.argv) < 2:
        cmd_status()
        return
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd == "status":
        cmd_status()
    elif cmd == "record":
        cmd_record(args)
    elif cmd == "phase":
        cmd_phase(args)
    elif cmd == "evolve":
        cmd_evolve()
    elif cmd == "reverse":
        cmd_reverse()
    elif cmd == "set":
        cmd_set(args)
    elif cmd == "inject":
        cmd_inject(args)
    elif cmd == "brain":
        cmd_brain(args)
    elif cmd == "init":
        for ws in WORKSPACES:
            m = empty_manifest(ws)
            save_manifest(ws, m)
            print(f"Initialized {MANIFEST_FILENAME} in {ws}")
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: status, record, phase, evolve, init, reverse, set, inject")


if __name__ == "__main__":
    main()
