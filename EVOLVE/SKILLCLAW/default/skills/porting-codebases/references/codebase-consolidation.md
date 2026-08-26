# Codebase Consolidation (merging sibling codebases into one)

Generic workflow for merging N codebases of the SAME lineage (triad forks, generations,
redundant agent workspaces) into a single living tree. Proven on the ARK/OMNIPRIME/
AURORAL → VORPAL fold; case study in `agent-triad-orchestration` →
`references/triad-consolidation-to-vorpal.md`.

## Sequence that works
1. **Recon each codebase** — py-file counts, line counts, verify harnesses, soul/
   constitution docs. Be deliberate, not wholesale: separate codebases are a real gene
   pool; the fold should pick winners per module, not dump everything.
2. **Write a CONSOLIDATION.md manifest** — per module: absorbed (winner + why it won),
   dropped (dead weight + why), provenance (source → destination). The drop list
   matters as much as the winners: the ring/bus/spawn machinery usually dies here.
3. **Copy winners into a fresh scaffold**, preserving each module's relative home —
   do NOT flatten paths that harnesses depend on.
4. **Gate**: `python -m py_compile` every migrated module, then run the FULL harness
   suite capturing each returncode (pipe-free — never `| tail` which masks exit codes).
   A green suite is the only "migration succeeded" signal. Compile alone is not enough:
   a harness can compile and still fail at runtime on a missing module.
5. **`git init`** for provenance, repoint `registry.json`/path refs at the new root.

## Key pitfall — harnesses encode their home (restore layout, don't edit the harness)
Migrated `hermes_verify_*.py` files frequently resolve paths relative to their OWN
location:
- `ROOT = Path(__file__).resolve().parents[3]` then `ROOT / "some_module.py"` — the
  harness expects a specific nesting depth (e.g. `SKILLHUB/tests/` under the worktree).
- `sys.path.insert(0, Path(__file__).parent.parent / "SKILLS" / "pyramid" / "LANGUAGE")`
  — the harness expects its sibling directories.

Moving the harness one level changes what those relative paths resolve to →
`ModuleNotFoundError` / `FileNotFoundError` that LOOKS like broken migrated code but is
actually a displaced harness. Symptom vs cause: the migrated module compiles fine; only
the harness fails.

FIX: **restore the harness's expected directory layout** (move the harness back, or move
its sibling modules to where the relative paths resolve). Do NOT rewrite the harness. An
unmodified harness stays a valid provenance anchor; editing it silently invalidates the
very gate you're using to prove the migration. When a harness points at a data dir that
didn't get migrated (e.g. a `PLASMIDS/` folder), migrate the data — don't drop the gate.

## Verification discipline
- `python -m py_compile` all migrated modules FIRST (fast fail on syntax).
- Then run each harness individually capturing `returncode` — aggregate in Python
  (subprocess) rather than shell, so a FAIL isn't masked by a pipe.
- Two real outcomes to expect and fix, not paper over: (a) harness relative-path
  displacement → restore layout; (b) missing data dir the harness points at → migrate
  the data.
- Log the sweep to the repo's NOTES/ledger and record pass counts in the manifest.
