---
name: local-llm-ollama
description: "Run local models with Ollama; wire them into Hermes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ollama, local-llm, models, offline, hermes, cli]
    related_skills: [adaptive-model-switcher, hermes-agent]
---

# Local LLMs with Ollama

## Overview

Operate Ollama from an agent context: discover the correct model tag, pull large
weights without blocking, serve them, and launch agent front-ends (Hermes,
Hermes Desktop, Claude Code, OpenCode, OpenClaw) against a local model.

The dominant failure mode is not "Ollama is broken" — it is **guessing model tags**
and **running interactive commands through a non-interactive tool**. Both are
avoidable with the rules below.

## When to Use

- User says "ollama <anything>", "run X locally", "launch hermes on ollama"
- Reducing API spend by pointing Hermes at a local endpoint
- Diagnosing `pull model manifest: file does not exist` or launcher TTY errors
- Inventorying which local models exist before recommending a routing candidate
  (pairs with `adaptive-model-switcher`)

## Rule 1 — Never guess a model tag

`ollama` has **no `search` subcommand**. Guessed names fail with a misleading
error:

```
Error: pull model manifest: file does not exist
```

That message means *the tag does not exist*, not that the network or install is
broken. Resolve the real tag first:

```bash
ollama list                      # what is already local
```

Then confirm the published tag via `web_search "ollama <name> model"` or
`https://ollama.com/library/<name>` before pulling.

Known trap: the Nous Research family is published as **`hermes3`**
(`hermes3:3b|8b|70b|405b`), plus legacy `nous-hermes`. There is **no** `hermes`
or `hermes-2-pro` tag — `hermes` is the name of the *application* integration,
not a model.

## Rule 2 — `ollama launch` needs a TTY unless you pass `--model`

`ollama launch <app>` opens an interactive model selector. From a non-interactive
tool this fails:

```
Error: model selection requires an interactive terminal; use --model to run in headless mode
```

Always pass the model explicitly:

```bash
ollama launch hermes          --model hermes3
ollama launch hermes-desktop  --model hermes3
ollama launch claude          --model hermes3
ollama launch opencode        --model hermes3
```

If the app itself is interactive (a chat REPL), it still needs the user's own
terminal. Hand the exact one-line command to the user rather than trying to
drive the REPL through a tool call. Offer `focus_pane(pane="terminal")` so they
can paste it in-app.

## Rule 3 — Pull multi-GB weights in the background

A 4.7 GB pull takes 8–25 minutes on a typical link and will blow the 180 s
foreground timeout. Worse, the progress bar emits a redraw per frame — a single
foreground call produced **~250,000 chars** of spinner noise.

```
terminal(command="ollama pull hermes3", background=true, notify_on_complete=true)
```

Then let the completion notification arrive. Poll with
`process(action="poll")` sparingly — every poll drags progress-bar bytes into
context. Do **not** `process(action="wait")` in a loop; the wait is clamped to
180 s and returns "still running", which is not an error.

While the pull runs, give the user a usable fallback immediately: launch against
a model they already have (`ollama list`) instead of making them wait.

## Wiring Ollama into Hermes directly

Ollama exposes an OpenAI-compatible endpoint at `http://localhost:11434/v1`.

```bash
hermes setup            # interactive: choose custom provider + base_url
```

Equivalent config shape:

```yaml
model:
  default: "hermes3"
  provider: "custom"
  base_url: "http://localhost:11434/v1"
```

Local models are slow; raise the timeout in `~/.hermes/.env`:

```
HERMES_API_TIMEOUT=1800
```

Verify the endpoint before declaring success:

```bash
curl -s http://localhost:11434/v1/models
```

Prefer `hermes config set` / `hermes setup` over hand-editing `config.yaml`.

## Sizing

Rough guidance for picking a tag: ~8B ≈ 4.7 GB download, runs on 8 GB VRAM;
~30B ≈ 16 GB VRAM; ~70B ≈ 40 GB download and needs a workstation GPU or heavy
offload. Pick the smallest tag that satisfies the task profile — see
`adaptive-model-switcher` for the quality/cost tradeoff framework.

## Reporting style for this user

Keep it to a compact ✅/❌ status table plus the exact command to run. No
narration of each failed attempt; state what works and what the blocker is.

## Common Pitfalls

1. Guessing a model tag → `file does not exist`. Look it up first.
2. Confusing an *application* name (`hermes`, `claude`, `opencode`) with a
   *model* tag (`hermes3`, `llama3`).
3. Running `ollama launch` or `ollama run` without `--model` from a tool.
4. Foreground `ollama pull` → timeout at 180 s + massive spinner output.
5. Polling a background pull repeatedly; each poll costs context.
6. Reporting "done" after `pull` without re-running `ollama list` to confirm the
   tag landed.
7. Forgetting `HERMES_API_TIMEOUT` — local generations get cut off mid-answer.

## Verification Checklist

- [ ] `ollama --version` succeeds
- [ ] Target tag confirmed against `ollama list` or ollama.com/library
- [ ] Long pulls run with `background=true, notify_on_complete=true`
- [ ] `ollama list` re-run after the pull shows the new tag
- [ ] `ollama launch <app> --model <tag>` given to the user verbatim
- [ ] If wiring into Hermes: `/v1/models` curl returns the model, timeout raised

See `references/ollama-cli-quirks.md` for verbatim error strings and the
model/application name split.
