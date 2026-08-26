---
name: neurocore-omnibus-integration
description: Debug Neurocore-OMNIBUS API wiring and bridge behavior.
---

# Neurocore + OMNIBUS Integration

## Repo Map

- Neurocore: `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore`
  - Contracts: `contracts/index.ts`, `contracts/neuro_intent.json`
  - Core: `core/dispatcher.ts`, `core/safety_gate.ts`, `core/event_bus.ts`, `core/events.ts`
  - Adapters: `adapters/function-call-adapter.ts`, `adapters/omnibus-swarm/`
  - Lib: `lib/neurocore-swarm.ts`, `lib/safety_gate.ts`, `lib/memory/learning.ts`
  - Bridge: `neurocore-bridge.cjs`
  - CI: `.github/workflows/neurocore-ci.yml`

- OMNIBUS: `C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS`
  - Server: `server.cjs`
  - Agent system: `agent_system.js`
  - Frontend: `app.js`, `index.html`
  - Adapters: `adapters/omni-swarm-adapter.ts`, `lib/hermes-adapter.ts`, `lib/neurocore-swarm.ts`
  - Tests: `tests/*.test.ts`

- Hermes Hive: `C:\\Users\\jonny\\HERMES-HIVE`
  - Stack: Vite 6 + React 19 + TS + Express middleware plugin (`src/server/apiMiddleware.ts`)
  - Dev server: `npm run dev` → `http://localhost:3000`
  - Health: `GET /api/health`
  - Chat/data surfaces: `src/client/hooks/useHiveData.ts`, `/api/hermes/command`, `/api/demo/trigger`
  - Note: separate from AQB `server.ts`; use this repo when the task is the Hive UI itself, not OMNIBUS.

## Separation Rule

- Keep Hermes Hive and AQB/OMNIBUS as separate codebases.
- Integration should be via API bridges or shared contracts, not by merging repos.
- If asked to “wire up” Hive, prefer mounting Hive as its own dev server and connecting through documented `/api/*` endpoints.

## Reference Notes

- `references/hermes-hive-wiring-2026-08-11.md` contains the Hermes Hive clone path, startup recipe, observed API surface, and current integration direction.

## Verified Wiring

1. **ESM/CJS bridge**: `server.cjs` requires `neurocore-bridge.cjs`, which dynamically imports Neurocore TS modules via `import('file://' + ...)` with tsx transpilation.
2. **Server endpoints**: `server.cjs` exposes `/api/neurocore/connect`, `/api/neurocore/intent`, `/api/neurocore/health`, `/api/neurocore/status`, `/api/neurocore/queue`, `/api/neurocore/memory`, `/api/neurocore/learning`, `/api/neurocore/tools`, `/api/neurocore/tools/call`, `/api/neurocore/debate`, `/api/neurocore/peers`, `/api/neurocore/emergency-stop`, `/api/neurocore/emergency-stop/reset`, `/api/neurocore/defense/status`, `/api/neurocore/defense/audit`.
3. **Frontend dispatch**: `agent_system.dispatch()` posts to `/api/neurocore/intent` and falls back to `/api/chat` on failure.
4. **Confidence triage**: server-side routing on `/api/neurocore/intent` with thresholds `>=0.8 → hermes`, `>=0.5 → ollama`, `<0.5 → nous`.
5. **Route order**: keep `/api/neurocore/*` API routes above the static fallback so `/api/neurocore/health` is not shadowed by `index.html`.
4. **Config**: `window.apiConfig` supplies `provider`, `model`, etc. to the frontend dispatch path.

## Verification Recipe

Run in this order:

```bash
# Neurocore
cd 'C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore'
npx tsc --noEmit
npm test

# OMNIBUS
cd 'C:\\Users\\jonny\\OneDrive\\Desktop\\AQB\\OMNIBUS'
npm test
PORT=3001 node server.cjs &
sleep 2
curl http://localhost:3001/api/neurocore/health
curl -X POST http://localhost:3001/api/neurocore/intent \
  -H 'content-type: application/json' \
  -d '{"intent":"probe","source":"mock","confidence":0.9,"features":{},"requiresConfirmation":false}'
kill %1
```

Expected: lint clean, tests pass, health returns `status` JSON, intent returns `status: completed` with triage `routedTo: hermes`.

## Known Gaps

- `adapters/neural-decoder/` is referenced in CI but missing from the repo.
- SwarmVisualizer UI component is not present.
- Neurocore's `lib/neurocore-swarm.ts` expects `../Omnibus/swarm_runtime.js` from the OMNIBUS repo; if missing, the adapter falls back to mock mode with `Mock Routing` capabilities.

## Pitfalls

- Use `scripts/verify-neurocore-omnibus.sh` to rerun the full lint/test/smoke-check sequence.
- `tsc --noEmit` must run from the Neurocore root; paths alias `@/contracts`, `@/core`, `@/lib`.
- OMNIBUS tests require tsx; they import TS test files directly.
- The bridge uses `file://` URLs with forward slashes; do not pass Windows backslashes.
- `neurocore-bridge.cjs` caches dynamic imports; restart the server after Neurocore changes.
- Port conflicts are common on Windows: if `EADDRINUSE` occurs, identify the owner PID via `netstat -ano | grep <port>` and stop it before restarting. Prefer `PORT=3001` for assistant-controlled runs.
- If `/api/neurocore/connect` returns `roles: ["Mock Routing"]`, the runtime dependency is missing. Create `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore\Omnibus\swarm_runtime.cjs` from OMNIBUS's `swarm_runtime.js` and update `lib/neurocore-swarm.ts` to require `.cjs`. Restart the server and verify roles switch to real skills.
