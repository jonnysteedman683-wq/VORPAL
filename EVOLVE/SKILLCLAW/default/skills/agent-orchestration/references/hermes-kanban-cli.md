# Hermes Kanban CLI — working surface (verified 2026-08-26)

## Flag placement (critical)
`--board` is a flag on the `kanban` command, BEFORE the verb:
```
hermes kanban --board default list      ✓
hermes kanban list --board default      ✗ unrecognized arguments
```
The kanban subcommand help (`hermes kanban <verb> --help`) only shows verb flags; the board flag lives on the parent. When scripting, route every kanban call through one helper that inserts `--board` before the verb.

## Core verbs + signatures (verified)
- `list` — rows like `◻ t_abc123  todo  default  title...`; `(no matching tasks)` = empty board (correct output, not a bug)
- `show <id>` — title, status, assignee, workspace, parents, comments, events
- `claim <id> [--ttl N]` (default 900s) — atomic; prints the resolved workspace path
- `heartbeat <id> [--note TEXT]` — keep a long-running claim alive
- `complete <id> [--result TEXT] [--summary TEXT] [--metadata JSON]` — closes the run; metadata is a JSON dict of structured facts (e.g. changed_files, tests_run, elapsed_s)
- `block <id> --kind {capability|dependency|needs_input|transient} --reason TEXT`
- `create`, `comment`, `link`/`unlink`, `assign`, `schedule`, `unblock`, `dispatch`, `daemon`, `stats`, `boards list/switch`
- `swarm` — create a Kanban Swarm v1 graph (parallel workers → verifier → synthesizer)

`--board` placement also matters for `boards`: `hermes kanban boards list` / `boards switch <slug>`.

## Known-good bridge pattern (from VORPAL WORKER/hermes_bridge.py)
```python
def _kanban(subcmd, board=None, timeout=60):
    args = ["kanban"]
    if board:
        args += ["--board", board]
    args += subcmd
    return _run(args, timeout=timeout)   # subprocess, capture_output, raise BridgeError on rc!=0

def chat(prompt, model=None, provider=None, timeout=600):
    args = ["chat", "-q", prompt, "-Q"]   # -Q suppresses banner/spinner
    if model:
        args += ["-m", model]
    if provider:
        args += ["--provider", provider]
    return _run(args, timeout=timeout)
```
`-Q` (quiet) keeps one-shot output clean for machine parsing. Add `--max-turns` to cap runaway tool loops.

## Verify-gate tokens (worker)
`("[FAIL", "FAILED", "[FAILURE]", "NEEDS ATTENTION", "TRACEBACK")` — uppercase the output before matching so tokens are case-insensitive; reject empty output outright.

## Task prompt template (self-contained — chat -q has no memory)
```
You are a worker executing a kanban task. Do the work completely and verify it
before finishing. If you cannot complete it, say so and state what is missing.

TASK: <title>
TASK ID: <id>
WORKSPACE: <workspace or 'scratch'>

CONTEXT:
<full description from kanban show>

Report what you did and the result. Include file paths of anything created.
```
