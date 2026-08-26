# Telemetry Schema & Workflow

## Session: 2026-08-05 OMNIBUS Upgrade — Telemetry + Dead Code Cleanup

This document captures the telemetry system that was successfully added to OMNIBUS v85.0 in the swarm upgrade session.

### Telemetry State Object (server.cjs)

```javascript
const telemetry = {
  intents: [],                                    // array of intent records
  providerCounts: { hermes: 0, ollama: 0, nous: 0 }, // cumulative dispatch counts
  latencyMs: [],                                  // array of execution latencies
  errors: [],                                     // array of failed intent records
  startTime: Date.now()                          // boot timestamp for uptime calc
};
```

### Telemetry Data Collection (in /api/neurocore/intent handler)

On each successful intent execution:

```javascript
const provider = intentObj.source || triageProvider; // determined by confidence triage
const latencyMs = Date.now() - startTime;

telemetry.intents.push({
  id: intentObj.id,
  intent: intentObj.intent,
  provider,
  confidence: intentObj.confidence,
  latencyMs,
  status: result?.status === 'pending_confirmation' ? 'pending_confirmation' : 
          (result?.status === 'failed' ? 'failed' : 'completed'),
  timestamp: Date.now()
});

telemetry.providerCounts[provider] = (telemetry.providerCounts[provider] || 0) + 1;
if (latencyMs !== null) telemetry.latencyMs.push(latencyMs);
if (result?.status === 'failed') telemetry.errors.push({ id, intent, provider, timestamp });
```

### API Endpoints

**GET /api/telemetry/summary**
- Returns: `{ totalIntents, providerCounts, avgLatencyMs, errorCount, recentErrors, uptimeMs }`
- avgLatencyMs: average of telemetry.latencyMs array (rounded)
- recentErrors: last 20 errors
- uptimeMs: Date.now() - telemetry.startTime

**GET /api/telemetry/intents?limit=N**
- Returns: `{ intents: [ { id, intent, provider, confidence, latencyMs, status, timestamp }, ... ] }`
- Default limit: 50, max: 500
- Sorted newest-first

### UI Tab: panel-telemetry

Summary cards (grid-2 layout):
- `<div id="teleTotalIntents">` → total intents count
- `<div id="teleProviders">` → JSON.stringify(providerCounts)
- `<div id="teleLatency">` → "${avgLatencyMs} ms"
- `<div id="teleErrors">` → error count

Table (id="telemetryTableBody"):
- Columns: id, intent, provider, confidence, status, latencyMs, timestamp (localeTimeString)
- Fetched from /api/telemetry/intents?limit=50

Refresh function:
```javascript
async function refreshTelemetry(){
  const res = await fetch('/api/telemetry/summary');
  const data = await res.json();
  // populate cards: teleTotalIntents, teleProviders, teleLatency, teleErrors
  
  const intentRes = await fetch('/api/telemetry/intents?limit=50');
  const intentData = await intentRes.json();
  // populate telemetryTableBody with rows
}
```

### Dead Code Removed (Session 2026-08-05)

- Tool: `generate_fake_user` (randomuser.me API call) — removed from tools array and handler
- UI tabs: dead `panel-brainstorm` (placeholder lab) — replaced with `panel-telemetry`
- Handler code in app.js: removed dead `v100000`, `v10000`, `v5000`, `v3000_quantum`, `v1000_quantum` dispatch branches; kept only `v200_omnipresent` → `/api/chat`, `python_core` → /api/python/ml-core, everything else → `/api/neurocore/intent`

### Tests Status

After telemetry addition: **41/41 passing** (no regressions, 2026-08-05 verification).

### Key Lessons

1. Telemetry state **must** be initialized at module top-level, before app.use() calls, so it persists across all handlers.
2. Confidence triage thresholds (>= 0.8 → hermes, >= 0.5 → ollama, < 0.5 → nous) should be captured in telemetry.intents so trends can be analyzed later.
3. UI refresh handlers must wrap fetch in try/catch; graceful degradation when telemetry endpoints are slow.
4. Dead code removal should be comprehensive (all branches in a large if/else tree) in one patch, not piecemeal — leaves no orphaned code.
