---
name: frontend-backend-telemetry-and-cleanup
description: Add telemetry, polish UI, and remove dead/fake code safely.
---

# Frontend/Backend Telemetry & Dead Code Cleanup

Use when asked to add telemetry, instrument routes, remove dead/fake code, or polish UI in a JS/TS fullstack app while preserving existing tests and live behavior.

## Workflow

1. Audit dead code first: grep for fake identifiers, fake endpoints, fake render stubs.
2. Remove dead code in order: backend fake endpoints/tools, then frontend dead render functions, then dead UI tabs/panels.
3. Add telemetry state at module top-level, before route registration.
4. Instrument only real request paths; do not instrument dead branches.
5. Polish UI after functional changes are verified.
6. Run tests and live smoke checks after each major change.

## Dead Code Detection

### Backend (server.cjs)
- Grep for fake tools: `generate_fake_user`, `mock.*response`, `offline fallback`, `Simulated response`
- Grep for dead endpoint patterns: `app.post('/api/v` with high version numbers not in supported range
- Grep for fake orchestrator classes: `class Omni...`, `class Hyper...`, `class Omniscient...`

### Frontend (app.js)
- Grep for dead render functions: `function renderV...Result(`, `function render...Result(`
- Grep for dead UI tabs: `panel-brainstorm`, `v10M`, `v100000`, `godmind`, `transcendent`

### UI HTML (hive-unified-ui.html)
- Grep for dead tabs: `panel-brainstorm`, ARISE simulation controls
- Grep for fake data: `randomuser.me`, `Fake User Generated`

## Dead Code Removal

### Server.cjs Endpoints
- Prefer line-range deletion over multiline regex.
- Remove contiguous dead blocks from highest version down to lowest.
- Verify with `grep -n "app.post('/api/v"` after removal.
- Large-scale removal pattern: identify dead route blocks by version prefix, then delete exact line ranges in reverse order to preserve indices.
- Real algorithm endpoints may share `/api/v` prefixes; preserve routes that instantiate actual `ExperimentalMLBackend` classes like `KolmogorovArnoldNetwork`, `MambaStateSpaceModel`, `QuantumSuperpositionEngine`, etc.
- After removal, expect server.cjs to shrink by 1000+ lines in heavily polluted codebases.

### App.js Render Functions
- Identify blocks starting with `function renderV...Result(` and ending at the matching `}`.
- Use brace-depth scanning; remove from end to start to preserve indices.
- Validate with `node --check app.js`.
- Expected removal: 2000+ lines of dead render stubs in polluted OMNIBUS versions.

### Fake Tools
- Remove from tools array definition.
- Remove from switch/case handler.
- Verify tool count matches between definition and handler.

### experimental_ml.js Fake Orchestrators
- Grep for fake class patterns: `class Omni...`, `class Hyper...`, `class Omniscient...`
- Fake orchestrators typically have version strings like "v70.0", "v85.0", "v100000.0" in `this.version` or method bodies.
- Preserve real algorithm classes: `KolmogorovArnoldNetwork`, `MambaStateSpaceModel`, `FlowMatchingEngine`, `ModernHopfieldNetwork`, `LiquidNeuralNetwork`, `MixtureOfExperts`, etc.
- Use line-range removal for class bodies when regex fails on multiline class definitions.

### HTML Dead UI
- Remove dead tabs/panels referencing ARISE, brainstorm, or fake modes.
- Remove header widgets that duplicate existing status badges.

## Telemetry Implementation

### Server State
Initialize at module top-level, before `app.use()` calls:
```javascript
const telemetry = {
  intents: [],
  providerCounts: { hermes: 0, ollama: 0, nous: 0 },
  latencyMs: [],
  errors: [],
  startTime: Date.now()
};
```

### Data Collection
Instrument only real request paths in the intent handler:
```javascript
const provider = intentObj.source || triageProvider;
const latencyMs = Date.now() - startTime;

telemetry.intents.push({
  id, intent, provider, confidence, latencyMs,
  status,
  timestamp: Date.now()
});
telemetry.providerCounts[provider]++;
if (latencyMs !== null) telemetry.latencyMs.push(latencyMs);
if (result?.status === 'failed') telemetry.errors.push({ id, intent, provider, timestamp });
```

### API Endpoints
- `GET /api/telemetry/summary` — aggregate stats
- `GET /api/telemetry/intents?limit=N` — recent records
- `GET /api/telemetry/histogram` — confidence bins + latency p50/p95/p99

### UI Dashboard
- Summary cards: total intents, avg latency, errors, uptime
- Provider cards: count + success rate per provider
- Intent table: compact rows with status pills
- Wrap all fetch calls in try/catch for graceful degradation.

## UI Polish Standards

- Buttons: gradient background, `font-weight: 800`, `letter-spacing: 0.3px`, hover `translateY(-1px)` with glow.
- Cards: subtle border, padded, consistent `border-radius: 12px`.
- Tables: compact, ellipsis for long text, pill badges for status.
- Avoid duplicated widgets in header; keep tab shell compact.

## Support Files

- `references/large-scale-dead-code-removal.md` — exact line-range removal recipe for server.cjs, app.js, experimental_ml.js, and HTML dead UI cleanup used in OMNIBUS v85 upgrade.

After each major change:
1. `npm test` — must pass with no regressions.
2. Live smoke: `GET /api/neurocore/health`, `POST /api/neurocore/connect`, `POST /api/neurocore/intent`.
3. UI sanity: open `hive-unified-ui.html`, verify tabs render, telemetry refresh works.

## Defensible Swarm Hardening

Use when the user asks to make swarm dispatch/control safer or more defensible. Additive only; preserve existing `/api/neurocore/*` behavior for valid requests.

### Server-side defenses to add
- Request schema validation before triage.
- Per-IP rate limiting with configurable window and max requests.
- Provider circuit breaker per backend (`hermes`/`ollama`/`nous`) with failure threshold and cooldown.
- Append-only audit logging with timestamps, source IP, intent hash/id, triage result, latency, and error state.
- Emergency stop gated by confirmation token; reset also token-gated.

### Endpoints to add
- `GET /api/neurocore/health` — health + defense state JSON
- `GET /api/neurocore/defense/status` — circuit breaker states, rate-limit stats, uptime
- `GET /api/neurocore/defense/audit` — recent audit entries

### Route-order rule
- Keep `/api/neurocore/*` API routes above the static fallback.
- Do not let the catch-all HTML route shadow `/api/neurocore/health`; verify with `grep -n "neurocore/health"` and a live curl.

### Verification
- `node --check server.cjs`
- `npm test`
- Live smoke: `/api/neurocore/health`, `/api/neurocore/defense/status`, `/api/neurocore/defense/audit`

## Hermes Hive quick cleanup checklist
Use when editing `C:/Users/jonny/HERMES-HIVE/src` directly.
- Remove fake search results, fake HTTP payloads, fake repo contents, fake commit hashes, and fake DB rows.
- Replace fake connectors with real `fetch()`/`fs` flows or explicit not-implemented errors.
- Rename local variables like `mockRequest` to something neutral such as `policyRequest`.
- Prefer build/runtime verification over full type-check when the repo has large pre-existing `world/*` type errors.

## Pitfalls

- Do not use multiline regex to remove dead `app.post(...)` blocks; use line ranges.
- Do not remove real algorithm endpoints that call actual `ExperimentalMLBackend` classes.
- Do not instrument dead branches; only instrument live request paths.
- Do not start a second server while another instance owns the port; use `PORT=3001` override if needed.
- `node --check app.js` validates syntax but not runtime behavior; use browser smoke tests for UI.
- Old server instances can remain on the port after crashes; free with `taskkill /F /PID <pid>` before restarting.
