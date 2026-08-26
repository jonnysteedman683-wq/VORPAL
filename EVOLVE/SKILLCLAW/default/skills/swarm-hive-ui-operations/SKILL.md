---
name: swarm-hive-ui-operations
description: Hive Swarm UI and Neurocore/OMNIBUS backend wiring.
---

# Swarm Hive UI Operations

Class-level skill for the swarm-capable Hive Command Center frontend and its Neurocore/OMNIBUS backend integration surface.

## Scope

- Tabbed Hive UI pages exposing Neurocore data: status, phase groups, memory, learning, tools, brainstorm, chat
- Mounting the ARC Sentinel/Sentinel-style built UI under a dedicated OMNIBUS route
- Backend endpoint wiring between OMNIBUS and Neurocore
- Confidence triage exposure in the UI and API responses
- Emergency stop UX and live polling patterns
- Bridge endpoints that translate external/legacy swarm API contracts into current `/api/neurocore/*` routes

## Core Workflow

1. Identify whether changes are frontend, backend, or both.
2. Keep the UI swarm-first: status, queue, memory, learning, tools, and chat should all reflect live backend state.
3. For API work, prefer extending existing `/api/neurocore/*` routes over inventing new top-level endpoints.
4. For frontend, preserve the tabbed shell unless the user explicitly requests a redesign.

## UI Design Rules for Swarm Hive

- Keep the tab shell compact; avoid duplicated widgets in the header.
- Show connection state, emergency stop, queue, Hermes availability, last intent, last provider, and phase groups.
- Make Neurocore actions explicit: Connect, Refresh, Emergency Stop.
- Do not embed ARISE simulation controls in the main Hive shell unless the user explicitly asks for it.

## Backend Wiring Rules

- OMNIBUS must call `/api/neurocore/connect` before `/api/neurocore/intent`.
- `/api/neurocore/intent` should:
  - normalize confidence,
  - apply confidence triage,
  - record memory and learning samples,
  - return `triage.confidence` and `triage.routedTo` in the JSON response.
- Confidence triage thresholds:
  - `confidence >= 0.8` → `hermes`
  - `confidence >= 0.5` → `ollama`
  - `confidence < 0.5` → `nous`
- When mounting a built external UI under `/sentinel`:
  - mount `/sentinel/assets` as static
  - serve `/sentinel` with rewritten relative asset paths
  - avoid a raw `express.static('/sentinel')` mount that can cause redirect stubs instead of the real app shell
- In OMNIBUS `server.cjs`, require the Neurocore bridge via `path.resolve(__dirname, ...)`; do not use hardcoded Windows paths with forward slashes.
- The Neurocore repo uses ESM (`"type": "module"`); any CommonJS bridge/adapter files loaded from it must use `.cjs` to avoid `module is not defined in ES module scope`.
- `/api/neurocore/health` reports `disconnected` until `/api/neurocore/connect` is called; this is expected startup behavior.

## Unified Sentinel Root Mount

Make the built ARC Sentinel UI the single entry point instead of a subpath:

- Register Sentinel routes BEFORE OMNIBUS static serving.
- Serve Sentinel at `/` and `/sentinel` from the same handler.
- Keep `/assets` and `/sentinel/assets` static mounts so the app shell and chunk files resolve.
- Rewrite built asset paths from absolute to relative at serve time.

Example handler shape:

```js
const sendArcIndex = (req, res) => {
  const indexPath = path.join(arcDistPath, 'index.html');
  let html = fs.readFileSync(indexPath, 'utf8');
  html = html.replace(/src="\/assets\//g, 'src="./assets/').replace(/href="\/assets\//g, 'href="./assets/');
  res.type('html').send(html);
};
app.get('/', sendArcIndex);
app.get('/sentinel', sendArcIndex);
```

**Route-order rule:** If OMNIBUS also has `express.static(__dirname)` or `app.get('*', ...)` fallbacks, Sentinel must be registered before them or `/` will continue serving OMNIBUS’s `index.html`.

## Unified Overlay Injection

To combine OMNIBUS controls inside Sentinel without modifying the built app source, inject a small HTML/JS overlay into the served shell:

- inject a fixed top nav plus a floating panel into `index.html` before `</head>`
- wire buttons to existing `/api/neurocore/*` and `/api/telemetry/*` endpoints
- keep the overlay CSS self-contained and scoped to avoid breaking the Sentinel layout
- do not rely on the overlay for Sentinel’s core functionality; if JS fails, Sentinel should still load

## Frontend Chat Dispatch

- `agent_system.dispatch()` should call `/api/neurocore/intent` first and fall back to `/api/chat` on failure.
- `window.apiConfig` should provide `provider`, `model`, and any swarm-specific config.
- UI should show the routed provider and confidence when available.

## Bridge Endpoints for Legacy Swarm UI

- If a frontend expects `/api/swarm/initiate` and `/api/swarm/poll`, implement them as thin bridges:
  - `/api/swarm/initiate` creates a `swarmId`, forwards to `/api/neurocore/intent`, and returns normalized state.
  - `/api/swarm/poll` enriches that state from `/api/neurocore/status` and recent intents.
- Keep bridge state in a Map keyed by `swarmId`.
- Do not let bridge polling become a tight loop; throttle or back off if the backend is slow.

## Polling and State

- Refresh functions should be wrapped in `try/catch` so a failed fetch degrades gracefully.
- Avoid auto-poll loops that can overwhelm local backends; prefer manual refresh or slow polling.
- Emergency stop should reset global connection state to `stopped`/`error` and clear active adapter references.

## Pitfalls

- Do not start a second server while an existing instance still owns the port.
- On Windows, `netstat -ano | grep :3001` is the reliable owner check; ignore `TIME_WAIT` entries.
- `bash: no job control in this shell` is harmless MSYS noise during background launches.
- `EADDRINUSE` means rebind is blocked; either free the port or switch ports.
- Do not kill unrelated Node processes; confirm PID ownership first.
- Neurocore repo declares `"type": "module"`; any CommonJS bridge/adapter files under it must use `.cjs`, otherwise Node throws `module is not defined in ES module scope`.
- When wiring `neurocore-bridge.cjs` from OMNIBUS, use `path.resolve(__dirname, ...)` instead of hardcoded Windows paths with forward slashes.
- Mounting a built external UI under `/sentinel` requires both `/sentinel/assets` static mount and a `/sentinel` handler that rewrites asset paths to relative form; a bare `express.static('/sentinel')` mount can return redirect stubs instead of the real app shell.
- `/api/neurocore/health` reports `disconnected` until `/api/neurocore/connect` is called; this is expected, not a server fault.
- The Sentinel index handler must be declared as `(req, res) => {...}`; using `() => {...}` causes `ReferenceError: res is not defined` at runtime.
- Avoid duplicate Sentinel mount blocks in `server.cjs`; duplicate route registration can change effective mount order and cause the wrong `index.html` to win at `/`.
- Route order matters: if OMNIBUS also has `express.static(__dirname)` or `app.get('*', ...)` fallbacks, Sentinel routes must be registered before them or `/` will continue serving OMNIBUS’s `index.html`.

## References

- `references/hive-ui-wiring.md` — exact HTML/JS wiring for chat, status, phase, memory, learning, tools, brainstorm
- `references/confidence-triage.md` — API contract for triage routing and frontend exposure
- `references/windows-port-recovery.md` — safe port takeover pattern for localhost on Windows
- `references/arc-sentinel-mount.md` — mounting built Sentinel/ARC dist under `/sentinel` and `/api/swarm/*` bridge shape