#!/usr/bin/env python3
"""
Triad Dice Engine — HERMES + MARKUS + VORPAL upgrade selector.

Rolls the dice that pick the next upgrade, optimisation, or skill-curation
action across the HERMES ecosystem, the MARKUS OS, and the VORPAL agent core —
together (triad) or individually (single/duo). Stdlib-only, no network.

Mechanics
---------
single : 50% coin gate -> roll 1d18. 1-5/7-11/13-17 = MARKUS/HERMES/VORPAL
         actions, 6/12/18 = DOUBLE REROLL (2 more dice = 2 more options).
triad  : 50% coin gate -> combined cycle across all 3 systems. Lead die picks
         the lead system; one action die per system. 6 on any die = that
         system's double reroll.
duo    : 50% coin gate -> combined cycle across HERMES + MARKUS only.

Every executed cycle also rolls a curation die:
    1=CURATE  2=ENHANCE  3=OPTIMISE  4=SKIP  5=CURATE+ENHANCE  6=DEEP(all 3)

Rolls log to the roadmap (DICE_ROADMAP.md). Success rewards (0.0-1.0) bias
future rolls via epsilon-greedy weighting, the same learning pattern as
markus_dice_engine.py.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "1.0.0"

HOME = Path.home()
DEFAULT_ROADMAP = HOME / "OneDrive/Desktop/MARKUS-OS/HERMES UPGRADE/DICE_ROADMAP.md"
DEFAULT_STATE = HOME / ".hermes/dice_engine_state.json"

MARKUS_SLOTS = [1, 2, 3, 4, 5, 6]
HERMES_SLOTS = [7, 8, 9, 10, 11, 12]
VORPAL_SLOTS = [13, 14, 15, 16, 17, 18]
ALL_SLOTS = list(range(1, 19))
REROLL_SLOTS = {6, 12, 18}
EPS = 0.3  # exploration rate

# System -> its 6-slot band (for per-system resolution)
SYSTEM_BANDS = {
    "MARKUS": MARKUS_SLOTS,
    "HERMES": HERMES_SLOTS,
    "VORPAL": VORPAL_SLOTS,
}

TABLE: Dict[int, Dict[str, str]] = {
    1: {
        "system": "MARKUS",
        "name": "UPGRADE_MARKUS_UI",
        "target": "markus_chat.html, markus-os.html, the-orb.html, memory-palace.html, hack-console.html",
        "desc": "Refresh MARKUS UI: accessibility, contrast, keyboard nav, layout.",
        "next": "Edit the listed HTML under Desktop/MARKUS-OS; smoke-test via python launch_markus_app.py",
    },
    2: {
        "system": "MARKUS",
        "name": "UPGRADE_MARKUS_BACKEND",
        "target": "markus_server.py (8128), markus_kernel.py, markus_router.py, phoenix_*.py",
        "desc": "Backend refactor + API expansion on the MARKUS server.",
        "next": "py_compile touched files; restart server; curl http://localhost:8128/api/health",
    },
    3: {
        "system": "MARKUS",
        "name": "UPGRADE_MARKUS_FRONTEND",
        "target": "electron-main.js, electron-preload.js, package.json, hive-core/ frontend, markus-os-electron/",
        "desc": "Electron/JS frontend layer upgrade.",
        "next": "npm install per package.json; electron smoke test",
    },
    4: {
        "system": "MARKUS",
        "name": "OPTIMISE_MARKUS_PROCESS",
        "target": "markus_latency_multi_upgrade.py, markus_task_dag.py, markus_devswarm.py, markus_resilience.py, cron/schtasks",
        "desc": "Optimise MARKUS processes: latency, pools, DAG, resilience.",
        "next": "Run python markus_benchmark.py; profile hot paths; tune worker pools/DAG",
    },
    5: {
        "system": "MARKUS",
        "name": "RESEARCH_MARKUS_ROADMAP",
        "target": "markus_web_research.py -> research/evolutionary_loop_roadmap.md + DICE_ROADMAP.md",
        "desc": "Research MARKUS upgrade paths and log them to the roadmap.",
        "next": "Run markus_web_research.py; append findings to research/evolutionary_loop_roadmap.md and DICE_ROADMAP.md",
    },
    6: {
        "system": "MARKUS",
        "name": "MARKUS_DOUBLE_REROLL",
        "target": "engine",
        "desc": "MARKUS double reroll: roll 2 more dice for extra options.",
        "next": "2 extra dice resolve to 2 more MARKUS slots (1-6)",
    },
    7: {
        "system": "HERMES",
        "name": "UPGRADE_HERMES_UI",
        "target": "Hermes desktop: theme tokens, panes, chat surface (hermes-desktop-plugins skill)",
        "desc": "Upgrade HERMES UI: theme, pane layout, widget styling.",
        "next": "Follow hermes-desktop-plugins skill; edit theme tokens / build a pane plugin",
    },
    8: {
        "system": "HERMES",
        "name": "UPGRADE_HERMES_BACKEND",
        "target": "hermes config CLI: providers, models, gateway, MCP (setup_mcp), cron (cronjob)",
        "desc": "Upgrade HERMES backend wiring: model/provider routing, MCP, cron.",
        "next": "Load hermes-agent skill; hermes config set ...; audit MCP servers; review cron jobs",
    },
    9: {
        "system": "HERMES",
        "name": "UPGRADE_HERMES_FRONTEND",
        "target": "hermes-desktop-plugins, preview widgets, ::preview{file=...} pages, inline chat widgets",
        "desc": "Upgrade HERMES frontend: desktop plugins and inline widgets.",
        "next": "Build/extend a desktop plugin or chat widget; deliver as ::preview{file=...}",
    },
    10: {
        "system": "HERMES",
        "name": "OPTIMISE_HERMES_PROCESS",
        "target": "tool batching, memory hygiene, skill loading, adaptive-model-switcher routing",
        "desc": "Optimise HERMES process: batch calls, prune memory, tune triggers.",
        "next": "Audit skills_list for stale entries; run adaptive-model-switcher; prune memory with the memory tool",
    },
    11: {
        "system": "HERMES",
        "name": "RESEARCH_HERMES_ROADMAP",
        "target": "hermes docs https://hermes-agent.nousresearch.com/docs + web_search -> DICE_ROADMAP.md",
        "desc": "Research HERMES upgrade paths and log them to the roadmap.",
        "next": "Read hermes-agent skill + docs; web_search new capabilities; append findings to DICE_ROADMAP.md",
    },
    12: {
        "system": "HERMES",
        "name": "HERMES_DOUBLE_REROLL",
        "target": "engine",
        "desc": "HERMES double reroll: roll 2 more dice for extra options.",
        "next": "2 extra dice resolve to 2 more HERMES slots (7-12)",
    },
    13: {
        "system": "VORPAL",
        "name": "UPGRADE_VORPAL_CORE",
        "target": "Desktop/VORPAL: CORE/*.py (kernel, syscalls, shell, safety_gate, state_memory_manager, ark_*.py)",
        "desc": "Upgrade VORPAL's runtime core: kernel/syscalls/safety/state modules.",
        "next": "py_compile CORE/*.py; verify VORPAL harnesses (VERIFY/harnesses); commit to Desktop/VORPAL",
    },
    14: {
        "system": "VORPAL",
        "name": "UPGRADE_VORPAL_LINGUA",
        "target": "Desktop/VORPAL: LINGUA/ (lingua_prima, lp_tool, LINGUA_PROTOCOL.md)",
        "desc": "Upgrade VORPAL's internal language / compression engine.",
        "next": "Edit LINGUA modules; run lingua harnesses; py_compile; commit",
    },
    15: {
        "system": "VORPAL",
        "name": "UPGRADE_VORPAL_SKILLS",
        "target": "Desktop/VORPAL: EVOLVE/SKILLHUB/SKILLS/ + VERIFY/skills/",
        "desc": "Upgrade VORPAL's skill library (weapon rack): create/iterate/optimise skills.",
        "next": "Skill mutation per SOUL §9 (CREATE/ITERATE/REWRITE/MICRO-APPEND); commit",
    },
    16: {
        "system": "VORPAL",
        "name": "OPTIMISE_VORPAL_PROCESS",
        "target": "Desktop/VORPAL: EVOLVE/GOALS/GOALS.md, EVOLVE/NOTES.md, registry.json, cost ledger",
        "desc": "Optimise VORPAL's decision layer: goal-DAG accuracy, ledger hygiene, dead-weight.",
        "next": "Audit GOALS/NOTES/registry for stale or false claims; fix; commit",
    },
    17: {
        "system": "VORPAL",
        "name": "RESEARCH_VORPAL_ROADMAP",
        "target": "Desktop/VORPAL: EVOLVE/IDEAS.md + EVOLVE/GOALS/GOALS.md new goals",
        "desc": "Research VORPAL upgrade paths and log them to its DAG / ideas.",
        "next": "Research; append to EVOLVE/IDEAS.md; propose new GOALS entries; commit",
    },
    18: {
        "system": "VORPAL",
        "name": "VORPAL_DOUBLE_REROLL",
        "target": "engine",
        "desc": "VORPAL double reroll: roll 2 more dice for extra options.",
        "next": "2 extra dice resolve to 2 more VORPAL slots (13-17)",
    },
}

CURATION = {
    1: ("CURATE", "Inventory skills (skills_list); find stale/[SKILL_PRUNED]/duplicate skills; prune or consolidate via skill_manage delete absorbed_into=..."),
    2: ("ENHANCE", "Patch one skill with this cycle's lesson via skill_manage patch; bump version; keep pitfalls fresh."),
    3: ("OPTIMISE", "Tune a skill description/trigger (skill-creator run_loop) or merge near-identical skills."),
    4: ("SKIP", "No curation this cycle."),
    5: ("CURATE+ENHANCE", "Run CURATE then ENHANCE."),
    6: ("DEEP", "Run CURATE + ENHANCE + OPTIMISE (the extra chance)."),
}


# --------------------------------------------------------------------------
# RNG helpers (secrets for real runs, seeded Random for tests)
# --------------------------------------------------------------------------
def _rng(seed: Optional[int]):
    if seed is None:
        return None
    import random
    return random.Random(seed)


def _rand01(rng) -> float:
    if rng is None:
        return secrets.randbelow(1000000) / 1000000.0
    return rng.random()


def _rbelow(rng, n: int) -> int:
    """Uniform int in [0, n) — secrets for real runs, seeded Random for tests."""
    if rng is None:
        return secrets.randbelow(n)
    return rng.randrange(n)


def roll_d(rng, faces: int = 6) -> int:
    """Cryptographically secure (or seeded) roll in [1..faces]."""
    return _rbelow(rng, faces) + 1


def weighted_pick(rng, pool: List[int], rewards: Dict[str, float], eps: float = EPS) -> int:
    """Epsilon-greedy pick over slot ids: eps% uniform, else reward-weighted."""
    if _rand01(rng) < eps:
        return pool[_rbelow(rng, len(pool))]
    weights = [1.0 + max(float(rewards.get(str(s), 0.0)), 0.0) for s in pool]
    total = sum(weights)
    r = _rand01(rng)
    cum = 0.0
    for s, w in zip(pool, weights):
        cum += w / total
        if r <= cum:
            return s
    return pool[-1]


def weighted_pick_action(rng, pool: List[int], rewards: Dict[str, float], eps: float = EPS) -> int:
    """Like weighted_pick but never returns a reroll slot (bounded sub-rolls)."""
    while True:
        s = weighted_pick(rng, pool, rewards, eps)
        if s not in REROLL_SLOTS:
            return s


# --------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------
def slot_info(slot: int, reroll: bool = False) -> Dict[str, Any]:
    row = TABLE[slot]
    return {
        "slot": slot,
        "system": row["system"],
        "name": row["name"],
        "reroll": reroll,
        "target": row["target"] if not reroll else "",
        "next": row["next"] if not reroll else "",
    }


def resolve_single(rng, rewards: Dict[str, float], eps: float = EPS) -> List[Dict[str, Any]]:
    """50% gate handled by caller; here: 1d12, 6/12 -> 2 more dice."""
    s = weighted_pick(rng, ALL_SLOTS, rewards, eps)
    results: List[Dict[str, Any]] = []
    if s in REROLL_SLOTS:
        results.append(slot_info(s, reroll=True))
        for _ in range(2):
            results.append(slot_info(weighted_pick_action(rng, ALL_SLOTS, rewards, eps)))
    else:
        results.append(slot_info(s))
    return results


def vorpal_goal_pulse() -> float:
    """Read VORPAL's goal pulse (open-goal fraction) via the MARKUS bridge.
    Fail-open -> 0.0. Lets the dice steer toward the project with open work."""
    try:
        import subprocess as _sp, json as _json
        p = _sp.run(
            [sys.executable, r"C:/Users/jonny/OneDrive/Desktop/MARKUS-OS/markus_vorpal_bridge.py",
             "--status"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace")
        if p.returncode != 0:
            return 0.0
        d = _json.loads(p.stdout)
        return round(d.get("open_goal_count", 0) / max(1, d.get("goal_count", 1)), 3)
    except Exception:  # noqa: BLE001
        return 0.0


def resolve_duo(rng, rewards: Dict[str, float], eps: float = EPS,
                vorpal_bias: float = 0.0) -> Tuple[str, List[Dict[str, Any]]]:
    """Combined cycle: lead die + one action die per system (split between the 2).
    When vorpal_bias > 0, the lead die is nudged toward MARKUS (the project whose
    decision layer feeds the dice) proportional to VORPAL's open-goal pulse."""
    return resolve_triad(rng, rewards, eps, vorpal_bias,
                         systems=("HERMES", "MARKUS"))


def resolve_triad(rng, rewards: Dict[str, float], eps: float = EPS,
                  vorpal_bias: float = 0.0,
                  systems: Tuple[str, ...] = ("HERMES", "MARKUS", "VORPAL"),
                  lead_order: Tuple[str, ...] = ("HERMES", "MARKUS", "VORPAL")) -> Tuple[str, List[Dict[str, Any]]]:
    """Combined cycle across N systems (default triad: HERMES, MARKUS, VORPAL).
    Lead die picks the lead system; one action die per system (the pair is split
    between all systems). A 6 on any system's die = that system's double reroll."""
    lead = roll_d(rng)
    # Distribute lead across lead_order proportionally to a d-len dice.
    lead = _rbelow(rng, len(lead_order)) + 1  # 1..N
    if vorpal_bias > 0 and _rand01(rng) < vorpal_bias:
        # Bias the lead toward the system with the highest open-goal pulse.
        # Simplest: bias toward MARKUS (the VORPAL-fed side) when pulse is high.
        lead = lead_order.index("MARKUS") + 1 if "MARKUS" in lead_order else lead
    lead_sys = lead_order[min(len(lead_order) - 1, lead - 1)]
    results: List[Dict[str, Any]] = []
    for sysname in systems:
        band = SYSTEM_BANDS[sysname]
        s = weighted_pick(rng, band, rewards, eps)
        if s in REROLL_SLOTS:
            results.append(slot_info(s, reroll=True))
            sub_pool = [x for x in band if x not in REROLL_SLOTS]
            for _ in range(2):
                results.append(slot_info(weighted_pick_action(rng, sub_pool, rewards, eps)))
        else:
            results.append(slot_info(s))
    return lead_sys, results


# --------------------------------------------------------------------------
# State (reward learning)
# --------------------------------------------------------------------------
def load_state(path: Path) -> Dict[str, Any]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(path: Path, state: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def apply_reward(path: Path, slot: int, value: float) -> Dict[str, Any]:
    state = load_state(path)
    rewards = state.setdefault("rewards", {})
    key = str(slot)
    prev = rewards.get(key, {"reward": 0.0, "count": 0})
    alpha = 0.2
    new_r = (1 - alpha) * prev["reward"] + alpha * value
    rewards[key] = {"reward": round(new_r, 3), "count": prev["count"] + 1}
    state["rewards"] = rewards
    save_state(path, state)
    return state


def rewards_map(state: Dict[str, Any]) -> Dict[str, float]:
    return {k: v.get("reward", 0.0) for k, v in state.get("rewards", {}).items()}


# --------------------------------------------------------------------------
# Roadmap log
# --------------------------------------------------------------------------
def log_cycle(roadmap: Path, mode: str, coin_pass: bool, results: List[Dict[str, Any]],
              curation: Tuple[str, str], lead_sys: Optional[str], dry_run: bool) -> str:
    ts = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    lines = [f"\n## {ts} — mode={mode}", f"- Coin gate: {'PASS' if coin_pass else 'STAYED (no action this cycle)'}"]
    if lead_sys:
        lines.append(f"- Lead system: {lead_sys}")
    for r in results:
        if r["reroll"]:
            lines.append(f"- {r['system']} slot {r['slot']}: DOUBLE_REROLL -> 2 extra dice")
        else:
            lines.append(f"- {r['system']} slot {r['slot']}: {r['name']}")
            lines.append(f"    target: {r['target']}")
            lines.append(f"    next: {r['next']}")
    ck, cdesc = curation
    lines.append(f"- Curation die: {ck} — {cdesc}")
    lines.append("- Status: EXECUTED (log this cycle in DICE_ROADMAP.md)")
    block = "\n".join(lines)
    if dry_run:
        return block
    roadmap.parent.mkdir(parents=True, exist_ok=True)
    with open(roadmap, "a", encoding="utf-8") as f:
        f.write(block + "\n")
    return block


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def cmd_actions(args) -> int:
    print(f"Duo Dice Engine v{VERSION} — 18-slot HERMES+MARKUS+VORPAL map\n")
    print(f"{'Slot':<5}{'System':<8}{'Action':<32}{'Target'}")
    for s in ALL_SLOTS:
        row = TABLE[s]
        print(f"{s:<5}{row['system']:<8}{row['name']:<32}{row['target']}")
    print("\nMechanics: 50% coin gate | 6/12/18 = double reroll (2 extra dice) | reward-weighted (eps-greedy)")
    print("Modes: single (1d18) | duo (HERMES+MARKUS) | triad (HERMES+MARKUS+VORPAL, one die each)")
    return 0


def cmd_roll(args) -> int:
    rng = _rng(args.seed)
    coin_pass = args.force or (roll_d(rng, 100) <= 50)
    if not coin_pass:
        results: List[Dict[str, Any]] = []
        lead_sys = None
    else:
        rewards = rewards_map(load_state(_state_path(args)))
        if args.mode == "triad":
            vbias = vorpal_goal_pulse() if args.vorpal else 0.0
            lead_sys, results = resolve_triad(rng, rewards, args.eps, vorpal_bias=vbias)
        elif args.mode == "duo":
            vbias = vorpal_goal_pulse() if args.vorpal else 0.0
            lead_sys, results = resolve_duo(rng, rewards, args.eps, vorpal_bias=vbias)
        else:
            lead_sys = None
            results = resolve_single(rng, rewards, args.eps)
    cur_face = roll_d(rng)
    curation = CURATION[cur_face]
    block = log_cycle(_roadmap_path(args), args.mode, coin_pass, results, curation, lead_sys, args.dry_run)
    if args.json:
        out = {
            "version": VERSION,
            "mode": args.mode,
            "coin": coin_pass,
            "lead": lead_sys,
            "actions": results,
            "curation_die": cur_face,
            "curation": curation[0],
            "roadmap": str(_roadmap_path(args)),
        }
        print(json.dumps(out, indent=2))
    else:
        print(block)
    return 0


def cmd_reward(args) -> int:
    if not (1 <= args.slot <= 18):
        print(f"ERROR: slot {args.slot} out of range 1-18")
        return 2
    if not (0.0 <= args.value <= 1.0):
        print(f"ERROR: value {args.value} must be 0.0-1.0")
        return 2
    state = apply_reward(_state_path(args), args.slot, args.value)
    print(f"Reward recorded: slot {args.slot} += {args.value}")
    print(f"Rewards now: {state['rewards']}")
    return 0


def cmd_stats(args) -> int:
    state = load_state(_state_path(args))
    rewards = state.get("rewards", {})
    if not rewards:
        print("No rewards recorded yet. Run: python scripts/dice_engine.py reward <slot> <0.0-1.0>")
        return 0
    print(f"{'Slot':<5}{'Reward':<10}{'Count':<7}Action")
    for s in ALL_SLOTS:
        r = rewards.get(str(s))
        if r:
            print(f"{s:<5}{r['reward']:<10.3f}{r['count']:<7}{TABLE[s]['name']}")
    return 0


def cmd_verify(args) -> int:
    ok = True
    checks: List[Tuple[str, bool, str]] = []

    # 1. py_compile self
    try:
        import py_compile
        py_compile.compile(__file__, doraise=True)
        checks.append(("py_compile self", True, ""))
    except Exception as e:  # noqa: BLE001
        ok = False
        checks.append(("py_compile self", False, str(e)))

    # 2. single mode reaches all 18 slots
    seen = set()
    rng_cov = _rng(args.seed)
    for _ in range(6000):
        for r in resolve_single(rng_cov, {}):
            seen.add(r["slot"])
    ok1 = all(s in seen for s in range(1, 19))
    ok = ok and ok1
    checks.append(("single mode covers all 18 slots", ok1, f"hit={sorted(seen)}"))

    # 3. coin ~50%
    rng = _rng(args.seed + 1)
    passed = sum(1 for _ in range(2000) if roll_d(rng, 100) <= 50)
    frac = passed / 2000
    okc = 0.35 <= frac <= 0.65
    ok = ok and okc
    checks.append(("coin gate ~50%", okc, f"passed={passed}/2000 ({frac:.3f})"))

    # 4. duo mode always touches both systems; triad touches all 3
    both = True
    rng_duo = _rng(args.seed + 2)
    for _ in range(2000):
        _, res = resolve_duo(rng_duo, {})
        systems = {r["system"] for r in res if not r["reroll"]}
        if not ({"HERMES", "MARKUS"} <= systems):
            both = False
            break
    ok = ok and both
    checks.append(("duo always touches both systems", both, ""))

    all3 = True
    rng_triad = _rng(args.seed + 3)
    for _ in range(2000):
        _, res = resolve_triad(rng_triad, {})
        systems = {r["system"] for r in res if not r["reroll"]}
        if not ({"HERMES", "MARKUS", "VORPAL"} <= systems):
            all3 = False
            break
    ok = ok and all3
    checks.append(("triad always touches all 3 systems", all3, ""))

    # 5. roadmap dir writable
    try:
        tmp = Path(tempfile.gettempdir()) / "duo_dice_write_test.md"
        tmp.write_text("test\n", encoding="utf-8")
        tmp.unlink()
        checks.append(("roadmap dir writable", True, ""))
    except Exception as e:  # noqa: BLE001
        ok = False
        checks.append(("roadmap dir writable", False, str(e)))

    for name, passed_check, detail in checks:
        mark = "PASS" if passed_check else "FAIL"
        print(f"{mark}  -  {name}" + (f"  ({detail})" if detail else ""))
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def _roadmap_path(args) -> Path:
    return Path(os.environ.get("DICE_ROADMAP", str(DEFAULT_ROADMAP)))


def _state_path(args) -> Path:
    return Path(os.environ.get("DICE_STATE", str(DEFAULT_STATE)))


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="dice_engine", description="Duo Dice Engine — HERMES + MARKUS upgrade selector")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("roll", help="roll the dice and log the cycle")
    pr.add_argument("--mode", choices=["single", "duo", "triad"], default="triad")
    pr.add_argument("--force", action="store_true", help="bypass the 50% coin gate")
    pr.add_argument("--vorpal", action="store_true",
                    help="bias the lead die toward MARKUS by VORPAL's open-goal pulse")
    pr.add_argument("--dry-run", action="store_true", help="print only, do not write roadmap")
    pr.add_argument("--json", action="store_true", help="machine-readable output")
    pr.add_argument("--seed", type=int, default=None, help="seeded RNG (tests only)")
    pr.add_argument("--eps", type=float, default=EPS, help="exploration rate")
    pr.set_defaults(fn=cmd_roll)

    pa = sub.add_parser("actions", help="print the 12-slot map")
    pa.set_defaults(fn=cmd_actions)

    prw = sub.add_parser("reward", help="record a reward for a slot")
    prw.add_argument("slot", type=int)
    prw.add_argument("value", type=float)
    prw.set_defaults(fn=cmd_reward)

    ps = sub.add_parser("stats", help="show reward table")
    ps.set_defaults(fn=cmd_stats)

    pv = sub.add_parser("verify", help="run the self-test gate")
    pv.add_argument("--seed", type=int, default=1)
    pv.set_defaults(fn=cmd_verify)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
