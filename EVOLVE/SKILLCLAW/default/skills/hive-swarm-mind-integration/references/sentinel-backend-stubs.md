# Sentinel backend — stub coverage & payload hardening

Load this file when wiring ARC Sentinel panels under OMNIBUS: adding
missing backend routes, or fixing the `toFixed` render crash from
missing numeric fields.

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
