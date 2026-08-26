---
name: hermes-profile-shellout
description: "Use when shelling out to a Hermes profile from a script."
version: 1.0.0
author: ox-alpha
license: MIT
category: devops
metadata:
  hermes:
    tags: [hermes, cli, shellout, subprocess, profile, worker, markus]
    related_skills: [hermes-worker-agents, hermes-skill-management]
---

# Hermes Profile Shellout (embed a profile as a worker/brain)

## When to Use
- An external daemon/server (e.g. MARKUS OS on port 8128) needs an LLM brain backed by a Hermes profile
- Any script must call `hermes chat -q ... -p <profile>` and use the reply programmatically
- Wiring a one-shot Hermes answer into a REST endpoint, cron tick, or watchman loop

## Setup: create a dedicated profile (one-time)
```bash
hermes profile create <name> --clone --no-alias   # clones default's config, .env, SOUL.md, skills
export HERMES_HOME="C:/Users/jonny/AppData/Local/hermes/profiles/<name>"
hermes config set model.provider nous
hermes config set model.model deepseek/deepseek-v4-flash
# verify before wiring anything:
hermes chat -q "Reply with exactly: READY" -p <name>
```
- `--clone` copies config + .env + SOUL.md + skills from the active profile — a full brain with the user's persona.
- When calling from another process, pass `-p <name>` explicitly AND set `HERMES_HOME` in the subprocess env, or the wrong profile answers.
- CONFIRM ROUTING (proven 2026-08-26): `-p <profile>` does not appear in
  `hermes chat --help` (it is a global/root option) — do NOT "fix" the hook by
  removing it. To prove the reply came from the intended profile and not the
  default, capture the `session_id:` line from the reply, then grep that id in
  `<profile>/logs/agent.log` and `<profile>/state.db` — it must appear there,
  NOT in the default profile's store. This is the empirical routing check.
- Add `-Q` (quiet) to the subprocess call: it suppresses banner/spinner/tool
  previews so stdout is just the final answer + session id — far less ANSI noise
  for the parser than an interactive-mode call.

## Calling from Python (subprocess)
DO use the `hermes` executable (`shutil.which`), NOT `python -m hermes` — the caller's venv usually has no hermes module and fails with `No module named hermes`.

```python
import subprocess, os, shutil, re
env = dict(os.environ)
env["HERMES_HOME"] = "C:/Users/jonny/AppData/Local/hermes/profiles/markus"
cmd = [shutil.which("hermes") or "hermes", "chat", "-q",
       f"USER intent: {prompt}. Reply directly and concisely.", "-p", "markus"]
proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120,
                      env=env, encoding="utf-8", errors="replace")
reply = _extract_reply((proc.stdout or "") + (proc.stderr or ""))
```

## Parsing the reply — the hard-won part
`hermes chat -q` stdout is ANSI-painted and banner-heavy. Naive "first non-empty line" / "last line" parsers fail in a chain of specific ways (all observed 2026-08-26):
1. A leading `Warning: Unknown toolsets: ...` line beats the answer to "first".
2. The prompt is echoed as `Query: <prompt>` and may WRAP, so a mid-line fragment (e.g. `concisely.`) lands where you expect the answer.
3. The `Resume this session with: / hermes --resume <id> -p <name>` footer wraps too; after `.strip()` it no longer starts with two spaces, so an indent-based filter misses it.
4. Box borders (`╰─────╯`, `─`, `━`) can be the literal last line.

RELIABLE rule: strip ANSI, drop lines starting with skip-tokens or containing the injected prompt, keep only lines with ≥1 alpha char, take the LAST candidate.

```python
def _extract_reply(out: str) -> str:
    ansi = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
    skip = ("query:", "warning:", "initializing", "reasoning", "resume",
            "session:", "title:", "duration:", "messages:",
            "hermes --resume", "hermes -c", "◆", "─", "━")
    cand = [ansi.sub("", l).strip() for l in out.splitlines()]
    cand = [l for l in cand if l and not l.lower().startswith(skip)
            and "MARKUS user intent" not in l
            and any(c.isalpha() for c in l)]
    return cand[-1] if cand else "(no parseable reply)"
```
(Filter the exact injected prompt string too, since it can be echoed into the body.)

## Pitfalls
- Long timeout: first call after profile creation is slow (CLI boot + model init). Use 120s, not 30s.
- The callee inherits env — export `HERMES_HOME` explicitly; a different value elsewhere in the caller breaks routing.
- Non-zero returncode ≠ empty reply; parse stdout+stderr combined, then surface rc only on failure.

## Real run (2026-08-26)
MARKUS OS brain: `markus_server.py` `/api/intent` originally returned a canned stub (`Dispatched intent to ...`). Replaced with a `_ask_markus_brain()` subprocess to the new `markus` profile (deepseek-v4-flash via nous). After 5 parser iterations (warning line, wrapped prompt tail, resume footer, box border) the alpha-last-line rule landed. Verified end-to-end: `curl -X POST /api/intent` → real DeepSeek answer streamed back through SSE.
