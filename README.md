# VORPAL — The Unified Blade

One autonomous agent. Three absorbed codebases. Zero rings.

VORPAL is the consolidated successor of the ARK + OMNIPRIME + AURORAL triad.
The triad's mistake was running three organisms that shared ~40% donor DNA and
shuffled state between contexts — a photocopier, not a gene pool. VORPAL keeps
the proven genome as **internal modes** inside one codebase.

## Layout

```
VORPAL/
  SOUL.md              — the invariant constitution (read first)
  CONSOLIDATION.md     — migration manifest: what won, where it landed, what died
  README.md            — this file
  kernel.py / syscalls.py / shell.py / lingua_boot.py  — runtime entrypoints (worktree root)
  CORE/                — guards + muscle: safety_gate, state mgr, token compressor, ark_* modules, dna_tracker
  LINGUA/              — Lingua Prima engine + lp_tool + protocol
  EVOLVE/              — DAG (GOALS.md), skill hub (SKILLHUB/tests), ledgers (NOTES/IDEAS)
  COMMAND/             — command deck (HTML dashboards) + ARK directives + ARK soul
  VERIFY/              — inquisitor layer: judging rubric, harnesses (+PLASMIDS), AURORAL skills
  registry.json        — skill/claim inventory
  dna_manifest.json    — lineage ledger (donor origins per module)
```

## Quickstart

```bash
# Verify the blade is sharp — all harnesses green, zero stubs
python -m py_compile CORE/*.py LINGUA/*.py
python VERIFY/harnesses/hermes_verify_self_improvement.py   # (example gate)

# Boot the runtime
python CORE/kernel.py

# Open the command deck
start COMMAND/ark-command-center.html
```

## Working modes (the triad, internalized)

| Mode | Inherited from | What it does |
|---|---|---|
| FORGE | ARK | Generate / meta-edit self (task-level + meta-level, DGM-H) |
| FRACTURE | ARK | Attack the population; adversarial critic |
| FUSE | ARK | Harden, commit, gate |
| FIELD | ARK | Observe, judge, route; score drift-to-NORTH |
| Forge Loop | OMNIPRIME | Build discipline: zero stubs, py_compile gate, Lingua P/F/V3 |
| Inquisitor | AURORAL | Verify / tag / quarantine every claim |

All six run inside ONE context. No packet bus, no ownership ring, no spawn.

## Golden rule

No `[IMPLEMENTED]` without a green `hermes_verify_*.py`. No claim without a tag.
No file without provenance.
