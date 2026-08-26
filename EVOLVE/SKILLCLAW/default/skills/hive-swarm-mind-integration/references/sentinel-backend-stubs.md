# Sentinel Backend Stubs and Real Implementations

## Coverage Map

Use this when adding or verifying Sentinel-backed routes in `server.cjs`.

### Implemented
- `POST /api/chat` -> real routed response via `routeToAI`; no self-loop to `/api/neurocore/intent`
- `POST /api/neurocore/intent` -> neurocore dispatch with triage, memory, learning
- `POST /api/neurocore/connect` -> connects `OmniSwarmAdapter`
- `GET /api/neurocore/health` -> healthy/degraded
- `GET /api/health` -> unified health
- `POST /api/embed` -> adapter or OpenAI embeddings; deterministic fallback
- `POST /api/knowledge/add`, `GET /api/knowledge/status`, `POST /api/knowledge/sync`, `GET /api/knowledge/erd`
- `POST /api/consolidate-memories`, `POST /api/memory/collapse`, `POST /api/tag-memory`, `GET /api/memory/multimodal`
- `GET /api/memories/reinforce`, `POST /api/memories/forget`
- `GET /api/debug/diagnostics`, `POST /api/debug/reset-quota`, `GET /api/debug/pipeline-diagnostics`, `GET /api/debug/trace`, `POST /api/debug/replay`
- `GET /api/episodes/timeline`
- `GET /api/goals/generate`, `POST /api/goals/save`, `POST /api/goals/update-task`
- `GET /api/identity/history`, `GET /api/identity/proposals`, `POST /api/identity/proposals/action`
- `GET /api/world-model/status`, `POST /api/world-model/rollout`
- `POST /api/brainstorm`, `POST /api/system/evolve`, `POST /api/execute-code`
- `POST /api/sculpting/prune`, `POST /api/sculpting/bridge`
- `GET /api/system/maintenance-history`, `GET /api/system/health`
- `POST /api/dream/log`, `POST /api/federated/submit-dream`, `POST /api/predict-action`, `POST /api/log-interaction`
- `GET /api/debug/quota-status`, `POST /api/telemetry`, `POST /api/fractal-think`
- `GET /api/telemetry/summary`, `GET /api/telemetry/intents`, `GET /api/telemetry/histogram`
- `POST /api/swarm/initiate`, `GET /api/swarm/poll`
- `GET /api/dream/history`, `GET /api/system/health-history`, `GET /api/debate/telemetry`, `GET /api/federated/collective-dream/1`, `POST /api/system/execute-healing`

## Notes

- Keep responses minimal; replace with real implementations only when a panel needs non-empty data.
- Avoid duplicate route blocks for the same path.
- `/api/identity/*` shares one `identityStore`; remove earlier duplicate empty stubs.
