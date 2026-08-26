# Ollama CLI quirks — verbatim errors and resolutions

Observed on Windows 10 / git-bash, ollama **v0.32.5**, 2026-08-05.

## Application names vs model tags

Ollama's docs list *integrations* (applications) and *models* under similar
names. They are different namespaces.

| Applications (`ollama launch <app>`) | Models (`ollama run/pull <tag>`) |
|---|---|
| `hermes` (Hermes Agent CLI) | `hermes3`, `hermes3:3b/8b/70b/405b` |
| `hermes-desktop` | `nous-hermes`, `nous-hermes:7b/13b` |
| `claude`, `opencode`, `openclaw` | `llama3`, `gemma4`, `qwen3.6`, `kimi-k2.5:cloud`, … |

`ollama run hermes` and `ollama pull hermes-2-pro` both fail — those tags do not
exist in the library.

## Error catalogue

### `Error: pull model manifest: file does not exist`

**Cause:** the model tag does not exist in the registry. Not a network,
permissions, or install problem.
**Fix:** verify the tag at `https://ollama.com/library/<name>` or via
`web_search "ollama <name> model"`, then pull the real tag.

### `Error: unknown command "search" for "ollama"`

**Cause:** there is no `ollama search`. Discovery is web-only.
**Fix:** use `ollama list` for local inventory and the web library for remote
discovery.

### `Error: model selection requires an interactive terminal; use --model to run in headless mode`

**Cause:** `ollama launch <app>` with no `--model` tries to render an interactive
picker; the agent's terminal is non-interactive.
**Fix:** `ollama launch <app> --model <tag>`. For launchers that then open a chat
REPL, hand the command to the user for their own shell.

### `exit_code 124` on `ollama pull`

**Cause:** foreground timeout (180 s default, 600 s max) vs a 4.7 GB download at
2–8 MB/s (8–25 min real time).
**Fix:** `background=true, notify_on_complete=true`.

## Progress-bar output volume

One 180 s foreground `ollama pull hermes3` emitted **247,179 characters** —
almost entirely progress-bar redraw frames (`pulling c8985d236593: 26% ▕████…`).
Hermes truncated it head+tail and spilled the rest to
`AppData/Local/hermes/cache/terminal-output/`.

Implication: never run a pull in the foreground, and when polling a background
pull, remember every poll returns a fresh slab of spinner frames. Poll on the
order of once per few minutes, not once per turn.

## ESM/CJS interop on Windows

### Dynamic ESM `import()` of .ts from CommonJS fails with `Received protocol 'c:'`

**Cause:** Windows `require()` + `import()` paths resolve to backslash paths like
`C:\Users\...\neurocore-swarm.ts`. Node's ESM loader requires `file://` URLs.

**Fix:** Convert to a `file://` URL and forward-slash the path:

```js
const mod = await import('file://' + absolutePath.replace(/\\/g, '/'));
```

Raw path without prefix throws:

```
Error: Only URLs with a scheme in: file, data, and node are supported
by the default ESM loader. On Windows, absolute paths must be valid file:// URLs.
Received protocol 'c:'
```

---

## Reference speed data point

hermes3 (4.7 GB) on this host: sustained 2–8 MB/s, ETA fluctuating 8–25 min.
Budget ~15 minutes for an 8B-class model.

## Hermes ↔ Ollama endpoint

- OpenAI-compatible base URL: `http://127.0.0.1:11434/v1`
- Model list probe: `curl -s http://127.0.0.1:11434/v1/models`
- Hermes config: `model.provider: custom`, `model.base_url: http://localhost:11434/v1`
- `HERMES_API_TIMEOUT=1800` in `~/.hermes/.env` for slow local generation
- Reconfigure interactively with `hermes model` or `hermes setup`
