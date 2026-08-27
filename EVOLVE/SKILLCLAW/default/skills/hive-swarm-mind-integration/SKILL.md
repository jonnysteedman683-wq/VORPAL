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

## Known Pitfalls & Cloudflare tunnel notes

The accumulated failure ledger (absolute-path discipline, `.cjs`
entrypoint, `phase: null` rejection, `/api/chat` bridge translation,
tunnel ephemerality) lives in `references/pitfalls.md` — load it when
a wiring step fails.

## Antigravity Integration

OMNIBUS can invoke Antigravity tasks through a backend route, useful
for the daily 5AM upgrade and hourly optimization jobs already
scheduled in this setup. Full detail — the `/api/antigravity/run`
route code, the `agy`-on-PATH pitfall, `AG_BIN`, and the Windows
install paths (Electron app / `agentapi.bat` / `language_server.exe`,
and why `command -v agy` failing does NOT mean Antigravity is absent)
— lives in `references/antigravity-integration.md`.

## Sentinel Backend Stub Coverage & Payload Hardening

Wiring ARC Sentinel panels under OMNIBUS is branch work. The full
Sentinel-backend reference lives in `references/sentinel-backend-stubs.md`:

- the ~40 stub endpoints every panel needs (valid JSON instead of 404)
- the `toFixed` render-crash fix (numeric fields on both sides,
  `.toFixed()` guards, and the `/api/health` vs `/api/system/health`
  unify pitfall)

Load it when a Sentinel panel 404s or crashes rendering.

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

