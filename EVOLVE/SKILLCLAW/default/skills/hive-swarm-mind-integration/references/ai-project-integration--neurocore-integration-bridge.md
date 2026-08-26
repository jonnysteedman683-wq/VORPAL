# Hive Swarm Mind Integration: Bridge & Endpoints

## Date
2026-08-05 — Integration session

## What works (verified)

### ESM/CJS Bridge
`C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore\neurocore-bridge.cjs`

```js
// Windows test:
node -e "const b = require('./neurocore-bridge.cjs'); b.isAvailable().then(avail => {
  if (avail) b.loadNeurocoreModules().then(m => console.log('Loaded:', Object.keys(m)));
});"

// Output:
// Loaded: [ 'OmniSwarmAdapter', 'NeuroStreamAdapter', 'SwarmUpgradeRegistry', 'FederatedDebateEngine', 'SafetyGate' ]
```

**Windows gotcha:** `import()` needs `file://` prefix:
```js
const mod = await import('file://' + path.replace(/\\/g, '/'));
```

### Server endpoints (server.js, L3210+)
- `POST /api/neurocore/connect` — initializes swarmAdapter
- `POST /api/neurocore/intent` — routes intent through NeuromorphicPipeline
- `GET /api/neurocore/health` — health metrics
- `POST /api/neurocore/debate` — standalone debates
- `GET /api/neurocore/peers` — P2P peer list + capabilities
- `POST /api/neurocore/emergency-stop` — cascade stop

### Frontend wiring (app.js)
- `window.apiConfig` defaults to `{ provider: 'hermes', model: 'hermes3' }`
- `initHiveSwarmMind()` auto-connects on DOMContentLoaded
- `python_core` mode routes through `AgentSystem.dispatch()` when connected

## Auto-triage model selection

| Confidence | Provider | Provider URL | Cost |
|---|---|---|---|
| >= 0.80 | hermes (Ollama) | localhost:8080/v1 | Free |
| >= 0.50 | ollama (local) | localhost:11434 | Free |
| < 0.50 | nous (cloud) | portal.nousresearch.com | Paid |

## TODOs for next session
1. Implement confidence-based routing in `/api/neurocore/intent` handler (Phase 4)
2. Add frontend provider selector dropdown in index.html (Tier 4)
3. Test full flow end-to-end with running server
