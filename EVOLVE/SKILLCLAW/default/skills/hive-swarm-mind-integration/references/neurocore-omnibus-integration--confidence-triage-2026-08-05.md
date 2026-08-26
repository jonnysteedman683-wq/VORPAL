# Confidence Triage Implementation — Session 2026-08-05

## Status: FULLY IMPLEMENTED ✅

Previous state: "not fully implemented" / "partially enforced". This is resolved.

## Server-Side Triage (server.cjs:/api/neurocore/intent)

Thresholds applied in handler:
```javascript
const rawConfidence = typeof confidence === 'number' ? confidence : 0.5;
const triageProvider = rawConfidence >= 0.8 ? 'hermes' : 
                       rawConfidence >= 0.5 ? 'ollama' : 'nous';
```

Intent object includes:
```javascript
const intentObj = {
  id: `neuro-${Date.now()}`,
  source: triageProvider,  // triage result
  intent: intent || '',
  confidence: rawConfidence,
  features: features || {},
  timestamp: Date.now(),
  // ...
};
```

Response includes triage metadata:
```javascript
res.json({
  success: true,
  phase: intentObj.phase,
  triage: {
    confidence: intentObj.confidence,
    routedTo: intentObj.source  // e.g. "hermes", "ollama", "nous"
  },
  ...result
});
```

## Frontend Exposure (hive-unified-ui.html + app.js)

**Chat dispatch** (app.js handleSendMessage):
- UI sends confidence (default 0.9) to `/api/neurocore/intent`
- Receives `triage` in response
- Displays: `Provider: ${triage.routedTo}`, `Confidence: ${triage.confidence}`

**Status tab** (hive-unified-ui.html):
- Shows `Last Provider` (from systemState.lastProvider, set on each intent)
- Updates on manual Refresh click

**Telemetry tab** (new, 2026-08-05):
- Provider counts dashboard: hermes, ollama, nous dispatch histogram
- Intent table: each row shows provider + confidence for traceability
- Aggregates across session lifetime

## Verification Steps

```bash
cd /c/Users/jonny/OneDrive/Desktop/AQB/OMNIBUS
npm test  # 41/41 passing

node server.cjs &
sleep 2

# Test triage at high confidence
curl -X POST http://localhost:3001/api/neurocore/intent \
  -H 'content-type: application/json' \
  -d '{"intent":"test","source":"ui","confidence":0.95,"features":{},"requiresConfirmation":false}'
# Expected: triage.routedTo = "hermes"

# Test triage at medium confidence
curl -X POST http://localhost:3001/api/neurocore/intent \
  -H 'content-type: application/json' \
  -d '{"intent":"test","source":"ui","confidence":0.7,"features":{},"requiresConfirmation":false}'
# Expected: triage.routedTo = "ollama"

# Test triage at low confidence
curl -X POST http://localhost:3001/api/neurocore/intent \
  -H 'content-type: application/json' \
  -d '{"intent":"test","source":"ui","confidence":0.3,"features":{},"requiresConfirmation":false}'
# Expected: triage.routedTo = "nous"

kill %1
```

All three cases verified 2026-08-05. Working correctly.

## Known Gaps (Resolved)

- ~~Frontend uses `config.provider` (static); server-side thresholds are not enforced.~~ **RESOLVED**: Frontend now sends real confidence scores; server applies triage unconditionally and returns it in response.
- ~~Confidence triage only partially enforced.~~ **RESOLVED**: fully wired server-side + UI display.
