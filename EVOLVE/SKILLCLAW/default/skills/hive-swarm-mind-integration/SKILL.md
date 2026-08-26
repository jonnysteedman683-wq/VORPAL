---
name: hive-swarm-mind-integration
description: "Hermes + Neurocore + OMNIBUS + Hive/Sentinel: wiring, UI mounts, ops, verification."
---

# Hive Swarm Mind Integration

## Overview

Class-level workflow for integrating Hermes, Neurocore, OMNIBUS, and ARISE with confidence-based auto-triage routing.

## Prerequisites

- Hermes installed with Ollama custom provider configured
- Neurocore repo at `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore`
- OMNIBUS repo at `C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS`
- Node.js 22+, npm, tsx
- Git push access to `jonnysteedman683-wq/neurocore` and `jonnysteedman683-wq/OMNIBUS`
- **Optional:** AI Studio applet for cloud-hosted Hive UI deployment

## Workflow

### Phase 1: ESM/CJS Bridge

Create `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore\neurocore-bridge.cjs`. Use dynamic `import('file://' + path)` to load Neurocore TypeScript modules from CommonJS. Export `loadNeurocoreModules()`, `getSwarmAdapter()`, and `isAvailable()`.

### Phase 2: Neurocore API Routes

1. Use `server.cjs` as the OMNIBUS backend entrypoint.
2. Prefer absolute require paths for cross-repo imports on Windows/OneDrive; relative `../AEGIS/...` hops from `AQB/OMNIBUS` may not resolve.
3. Add `/api/neurocore/connect`, `/intent`, `/health`, `/debate`, `/peers`, `/emergency-stop`, `/status`, and `/queue`.
4. Store connection state in `systemState` and update it in each route.
5. Health should use `swarmAdapter.capabilities()` rather than `getHealthMetrics()` unless the adapter provides it.

### Phase 3: Frontend Wiring

- In `app.js`: set `window.apiConfig = { provider: 'hermes', model: 'hermes3' }` and call `initHiveSwarmMind()` on load.
- In `agent_system.js`: add `dispatch()` to prefer `/api/neurocore/intent` with fallback to `/api/chat`.

### Phase 4: Neuro-Inspired Communication

Add optional spike-based communication primitives for sparse swarm messaging:

- Add `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore\adapters\omnibus-swarm\spike-comm.js` with:
  - `hashIntentToPhase(intent, source)`
  - `encodeIntentToSpikes(intentObj)`
  - `decodeSpikesToIntent(spikePayload)`
  - `groupByPhase(spikePayloads)`
- In `neurocore-bridge.cjs`, load it via dynamic `import('file://' + ...)` and expose it as `spikeComm`.
- In `server.cjs` `/api/neurocore/intent`, accept optional `phase` and echo it back in the response.
- In `agent_system.js` `dispatch()`, compute a deterministic `phase` from `provider + taskText` and send it.

This gives concurrent dispatch grouping without changing provider routing.

### Phase 5: Memory + Learning

Add intent memory and outcome learning:

- Add `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore\lib\memory\learning.ts` with:
  - `IntentMemoryStore` for recent/failed intent records
  - `LearningLogger` for confidence, success, provider, latency samples
- In `neurocore-bridge.cjs`, load via dynamic import and expose `getMemoryStore()` and `getLearningLogger()`.
- In `server.cjs` `/api/neurocore/intent`, log each completed intent outcome to both stores.
- Add endpoints:
  - `GET /api/neurocore/memory`
  - `GET /api/neurocore/learning`

These endpoints are read-only observability hooks for UI or Hermes self-improvement.

## Sentinel Frontend Component Wiring

When ARC Sentinel is mounted under OMNIBUS, wire these source components to the live backend:

- `SwarmVisualizer.tsx` -> `/api/swarm/initiate`, `/api/swarm/poll`
- `TelemetryDashboard.tsx` -> `/api/telemetry`, `/api/system/health-history`, `/api/debate/telemetry`, `/api/federated/collective-dream/1`
- `App.tsx` chat path -> `/api/chat` bridge, which forwards to `/api/neurocore/intent`
- Overlay controls -> `/api/neurocore/connect`, `/api/neurocore/status`, `/api/telemetry/summary`

Pitfall: Sentinel source calls `/api/chat` with `message`, `history`, `confidence`, `provider`, `model`. The OMNIBUS `/api/chat` bridge must normalize that payload into `/api/neurocore/intent` shape:
- `intent` from `message`
- `source` from confidence triage
- `confidence` default `0.6` if missing
- `features` object for `model`, `agentId`, `agentRole`, `sessionTraceId`, `contextData`
- omit `phase` entirely if not provided; do not send `phase: null`

Critical fix: do NOT implement `/api/chat` as `fetch('http://localhost:3001/api/neurocore/intent')` from inside `server.cjs`. That creates a self-loop. Instead, call `routeToAI(triageProvider, body.model, systemPrompt, question)` directly in the `/api/chat` handler and return `{ response, provider, confidence, swarmId: null }`. This preserves real routed responses without circular HTTP.

## Sentinel Backend Stub Coverage

Sentinel `src/` references many ARC backend routes that OMNIBUS does not implement by default. Add lightweight stubs in `server.cjs` so every panel gets a valid JSON response instead of 404:

- `POST /api/embed` -> `{ success, embedding: number[] }`
- `POST /api/knowledge/add` -> `{ success, added }`
- `GET /api/knowledge/status` -> `{ success, connected, count }`
- `POST /api/knowledge/sync` -> `{ success }`
- `GET /api/knowledge/erd` -> `{ success, entities, relations }`
- `POST /api/consolidate-memories` -> `{ success, consolidated }`
- `POST /api/memory/collapse` -> `{ success, collapsed }`
- `POST /api/tag-memory` -> `{ success, id, tags }`
- `POST /api/debate/step` -> `{ success, state, move }`
- `POST /api/debate/evaluate` -> `{ success, score }`
- `POST /api/debate/synthesize` -> `{ success, synthesis }`
- `GET /api/world-model/status` -> `{ success, active }`
- `POST /api/world-model/rollout` -> `{ success, steps }`
- `GET /api/skills/summary` -> `{ success, skills }`
- `POST /api/system/evolve` -> `{ success, fileName, applied }`
- `POST /api/execute-code` -> `{ success, output, error }`
- `POST /api/brainstorm` -> `{ success, ideas }`
- `POST /api/sculpting/prune` -> `{ success }`
- `POST /api/sculpting/bridge` -> `{ success }`
- `GET /api/debug/diagnostics` -> `{ success, diagnostics }`
- `POST /api/debug/reset-quota` -> `{ success }`
- `GET /api/debug/pipeline-diagnostics` -> `{ success, stages }`
- `GET /api/debug/trace` -> `{ success, traceId, events }`
- `POST /api/debug/replay` -> `{ success, replayed }`
- `GET /api/episodes/timeline` -> `{ success, episodes }`
- `GET /api/goals/generate` -> `{ success, goals }`
- `POST /api/goals/save` -> `{ success }`
- `POST /api/goals/update-task` -> `{ success }`
- `GET /api/identity/history` -> `{ success, history }`
- `GET /api/identity/proposals` -> `{ success, proposals }`
- `POST /api/identity/proposals/action` -> `{ success }`
- `GET /api/memory/multimodal` -> `{ success, memories }`
- `POST /api/system/heal` -> `{ success, message }`
- `GET /api/system/health-history` -> map recent intents to health event shape
- `GET /api/debate/telemetry` -> `{ transitions, agents }`
- `GET /api/federated/collective-dream/1` -> `{ round, narrative, updatedAt }`
- `GET /api/dream/history` -> `{ success, dreams }`
- `POST /api/system/execute-healing` -> `{ success, message }`

Keep these minimal; replace with real implementations only when a panel needs non-empty data.

## Auto-Triage Router

Confidence routing:
- `>= 0.8` -> `hermes`
- `>= 0.5` -> `ollama`
- `< 0.5` -> `nous`

Return the selected provider in the response.

## Verification

Static:
- `node --check server.cjs`
- `npm test` in OMNIBUS -> expected `44/44` pass

Runtime:
- `node server.cjs`
- `GET /api/neurocore/health`
- `POST /api/neurocore/connect`
- `POST /api/chat` with `{"message":"wiring check","history":[]}` -> expect JSON with `response`, `provider`, `confidence`, `swarmId`
- `GET /api/telemetry/summary`
- `GET /` and `GET /sentinel` for mounted Sentinel UI
- `GET /api/health` -> unified health endpoint
- `GET /api/dream/history` -> empty array stub
- `GET /api/system/health-history` -> recent intents mapped to health events
- `GET /api/debate/telemetry` -> agents list
- `GET /api/federated/collective-dream/1` -> round/narrative object
- `POST /api/system/execute-healing` -> accepts `actionType`

Public tunnel (optional):
```bash
winget install --id Cloudflare.cloudflared --accept-package-agreements --accept-source-agreements
/c/Program\ Files\ \(x86\)/cloudflared/cloudflared.exe tunnel --url http://localhost:3001
```

## Known Pitfalls

- On Windows/OneDrive, absolute paths are safer than relative cross-repo requires.
- Do not call missing adapter methods like `getHealthMetrics()` unless the adapter actually provides them.
- Keep backend entrypoint `.cjs` if the repo mixes ESM and CJS files.
- If old background logs show stale module-resolution errors, inspect the live `server.cjs` require path before retrying.
- Use dynamic `import('file://' + path)` only from the ESM/CJS bridge; don't use `require('file://...')`.
- When adding bridge modules, also add accessor functions (`getMemoryStore`, `getLearningLogger`) instead of exporting singletons directly.
- `tests/*.test.ts` can fail when `package.json` points at a directory without `index.ts`; fix the test script to the actual file path.
- `/api/neurocore/intent` rejects `phase: null`; omit the field when the caller has no phase.
- `/api/chat` bridge must compute triage provider before calling `/api/neurocore/intent`; otherwise intent handler sees `source: undefined` and may route incorrectly.
- `/api/neurocore/intent` returns `{ success, triage: { confidence, routedTo }, actionId, status }`, not `{ response, provider, confidence, swarmId }`. The `/api/chat` bridge must translate `actionId` into a user-facing `response` and read routing from `triage.routedTo`.

## Antigravity Integration

OMNIBUS can invoke Antigravity tasks through a backend route, which is useful for the daily 5AM upgrade and hourly optimization jobs already scheduled in this setup.

### Backend route

Add in `server.cjs`:

```js
app.post('/api/antigravity/run', async (req, res) => {
  const { prompt, model, timeoutMs, workdir } = req.body || {};
  const task = typeof prompt === 'string' && prompt.trim() ? prompt.trim() : 'Run OMNIBUS maintenance and suggest improvements.';
  const targetDir = workdir || __dirname;
  const printTimeout = Math.min(Math.max(timeoutMs || 5 * 60 * 1000, 1000), 20 * 60 * 1000);
  const command = `"${process.env.AG_BIN || 'agy'}" -p ${JSON.stringify(task)} ${model ? `--model ${JSON.stringify(model)}` : ''} --print-timeout ${printTimeout}`;

  try {
    const result = await new Promise((resolve, reject) => {
      const proc = require('child_process').exec(command, { cwd: targetDir, maxBuffer: 1024 * 1024 * 5 }, (error, stdout, stderr) => {
        resolve({ ok: !error, stdout: stdout || '', stderr: stderr || '', code: error ? (error.code || 1) : 0 });
      });
      if (proc.pid && typeof proc.kill === 'function') {
        setTimeout(() => proc.kill('SIGTERM'), printTimeout + 1000).unref?.();
      }
    });

    telemetry.intents.push({ id: `ag-${Date.now()}`, intent: 'antigravity-run', provider: 'system', confidence: 1, latencyMs: 0, status: result.ok ? 'completed' : 'failed', timestamp: Date.now(), raw: { prompt: task, model, workdir: targetDir, timeoutMs: printTimeout } });

    res.json({ success: result.ok, command, workdir: targetDir, timeoutMs: printTimeout, stdout: result.stdout, stderr: result.stderr, code: result.code });
  } catch (err) {
    res.status(500).json({ success: false, command, workdir: targetDir, timeoutMs: printTimeout, error: err.message });
  }
});
```

Pitfall: this route shells out to `agy`. If Antigravity is installed only as the Electron app on Windows, there may be no `agy` on PATH. In that case either:
- add `AG_BIN` env var pointing to a real CLI wrapper, or
- create a wrapper script at a known path and point `AG_BIN` to it.

### Windows Antigravity paths

On this Windows host, Antigravity installs as:
- Electron app: `C:\Users\jonny\AppData\Local\Programs\antigravity\Antigravity.exe`
- Agent API wrapper: `C:\Users\jonny\.gemini\antigravity\bin\agentapi.bat`
- Language server: `C:\Users\jonny\AppData\Local\Programs\antigravity\resources\bin\language_server.exe`

There is no standalone `agy.exe` on PATH by default. If `command -v agy` fails, do not assume Antigravity is absent; check the installed app paths above and decide whether to create a wrapper or use the agent API path.

## Sentinel Backend Payload Hardening

Symptom: built Sentinel UI throws `TypeError: Cannot read properties of undefined (reading 'toFixed')` from `assets/index-*.js`. This is a frontend render crash caused by missing numeric fields in backend responses.

Fix both sides:

1. Backend: ensure these endpoints always return numeric fields:
   - `GET /api/system/health` -> include `uptimeMs`, `uptime`, `memoryUsage: { heapUsed, heapTotal, rss }`, `activeConnections`, `unhandledErrors`
   - `GET /api/debug/diagnostics` -> include `memory`, `latency`, `errors`, `providers`, `circuitBreaker`, `queueSize`, `uptimeMs`, `uptime`, `memoryUsage`, `activeConnections`, `unhandledErrors`, `firestoreReadErrors`, `firestoreWriteErrors`
   - `GET /api/debug/pipeline-diagnostics` -> return `stages: Array<{ name, status, latencyMs }>`
   - `GET /api/debate/telemetry` -> return `transitions: []`, `agents: Array<{ id, updatedAt }>`

2. Frontend: where Sentinel source calls `.toFixed()` on API-derived values, guard with defaults:
   - `(value ?? 0).toFixed(n)`
   - `value?.toFixed(n) ?? 'N/A'`
   - `Number(value).toFixed(n)`

Pitfall: do not add these hardened fields only to `/api/health` if Sentinel panels call `/api/system/health`. Either unify them or keep both endpoints returning the same numeric shape.

## Cloudflare Tunnel Notes

- Quick tunnel URLs are ephemeral; they rotate when the tunnel process restarts or after timeouts.
- On this host/network, Cloudflare DNS can time out during tunnel startup even when `cloudflared` is running. In that case the tunnel is effectively unreachable from outside.
- Fallback: verify public access by fetching the tunnel URL from the same network path users will use. If it returns non-2xx or times out, stop advertising the public URL until the tunnel is healthy again.

## Push Pattern

OMNIBUS:
```bash
cd "/c/Users/jonny/OneDrive/Desktop/AQB/OMNIBUS"
git add server.cjs agent_system.js app.js package.json tests/
git commit -m "feat: Hive Swarm Mind integration with Neurocore routes, triage, frontend dispatch"
git push origin main
```

Neurocore:
```bash
cd "/c/Users/jonny/OneDrive/Documents/AEGIS/neurocore"
git add neurocore-bridge.cjs adapters/ tests/ README.md
git commit -m "feat: ESM/CJS bridge and neural-decoder scaffolding for Hive Swarm Mind"
git push origin main
```

## Support Files

- `references/omnibus_neurocore_integration.md` — session artifacts, exact paths, endpoint contracts, and debug notes.
- `references/ui-status-widget.md` — header status widget and queue widget markup, polling contract, and browser-script lint pitfall.
- `references/spike-communication.md` — spike-comm module, phase-tagged dispatch, and bridge loading notes.
- `references/memory-learning.md` — intent memory store, learning logger, endpoint wiring, and outcome logging notes.
- `references/function-calling-adapter.md` — tool registry, bridge accessors, `/tools` and `/tools/call` routes, and the `loadNeurocoreModules()` pitfall.
- `references/unified-hive-ui.md` — single-page Hive Command Center shell, tab routing, panel wiring, and polling contracts.
- `references/windows-server-and-tunnel.md` — Windows port lifecycle, restart/check commands, and Cloudflare quick-tunnel setup.
- `references/sentinel-backend-stubs.md` — Sentinel panel API coverage map, stub response shapes, and replacement order for real implementations.
- `references/antigravity-integration.md` — `/api/antigravity/run` route notes, Windows Antigravity install paths, wrapper requirement, and pitfalls.

## Absorbed sibling skills (labeled subsections)

These were separate skills; their full content now lives here as references:
- **Hive platform / backend registry** — `references/hermes-hive-platform.md` (+ `hermes-hive-platform--*.md`: SUPRIME bridge plan/verified, unified backend registry)
- **Hive/Sentinel UI operations** — `references/swarm-hive-ui-operations.md` (+ `swarm-hive-ui-operations--*.md`: ARC Sentinel mount, confidence triage, hive UI wiring, telemetry schema, Windows port recovery)
- **Neurocore↔OMNIBUS API debugging** — `references/neurocore-omnibus-integration.md` (+ `neurocore-omnibus-integration--*.md`); runnable probe: `scripts/verify-neurocore-omnibus.sh`
- **Windows start/restart ops** — `references/omnibus-neurocore-operations.md` (+ `omnibus-neurocore-operations--*.md`: Windows process management, unified Sentinel wiring)
- **Mounting external UIs / cross-system bridges** — `references/ui-system-integration.md` (+ `ui-system-integration--*.md`: CJS/ESM notes on Windows)
- **Integrating external AI projects with Hermes** — `references/ai-project-integration.md` (+ `ai-project-integration--*.md`: adapter API verification, Antigravity/AI Studio discovery, Neurocore bridge)

## Absorbed: frontend-backend telemetry & dead-code cleanup

The standalone `frontend-backend-telemetry-and-cleanup` skill was absorbed here; it is the OMNIBUS/Hive web-app
maintenance workflow (add telemetry, remove dead/fake code, polish UI) for the same server.cjs/app.js/experimental_ml.js
codebase. Support files:

- `references/large-scale-dead-code-removal.md` — exact line-range removal recipe for server.cjs, app.js,
  experimental_ml.js, and HTML dead-UI cleanup (OMNIBUS v85 upgrade).
- `references/defense-endpoints.md` — swarm hardening endpoints (`/api/neurocore/defense/*`) and payload hardening.

Key retained rules:

- **Dead code detection**: grep backend for fake tools (`generate_fake_user`, `mock.*response`, `Simulated response`),
  dead endpoint patterns (`app.post('/api/v` with unsupported versions), fake orchestrator classes
  (`class Omni...`, `class Hyper...`, `class Omniscient...`); frontend for dead render fns (`function renderV...Result(`)
  and dead tabs (`panel-brainstorm`, `v10M`, `v100000`, `godmind`, `transcendent`); HTML for fake data (`randomuser.me`).
- **Removal order**: backend fake endpoints/tools first, then frontend dead render functions, then dead UI tabs/panels.
  Prefer line-range deletion (reverse order to preserve indices) over multiline regex. Preserve REAL algorithm classes
  (`KolmogorovArnoldNetwork`, `MambaStateSpaceModel`, `QuantumSuperpositionEngine`, etc.) and real routes that
  instantiate actual `ExperimentalMLBackend` classes. Expect server.cjs to shrink 1000+ lines, app.js 2000+ in polluted builds.
- **Telemetry**: init state at module top-level BEFORE `app.use()`; instrument only real request paths; expose
  `/api/telemetry/summary`, `/api/telemetry/intents?limit=N`, `/api/telemetry/histogram`.
- **Defensible swarm hardening**: request schema validation, per-IP rate limiting, per-backend circuit breaker,
  append-only audit log, token-gated emergency stop; keep `/api/neurocore/*` routes above the static fallback so the
  catch-all HTML route can't shadow them.
- **Verification after each change**: `node --check server.cjs`, `npm test` (no regressions), live smoke
  (`/api/neurocore/health`, `/api/neurocore/connect`, `/api/neurocore/intent`), UI sanity on hive-unified-ui.html.
- **Hermes-Hive quick cleanup**: remove fake search/HTTP/repo/commit/DB data, replace fake connectors with real
  `fetch()`/`fs` flows or explicit not-implemented errors, rename `mockRequest`-style vars to neutral names.

