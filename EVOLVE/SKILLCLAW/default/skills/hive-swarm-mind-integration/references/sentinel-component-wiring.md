# ARC Sentinel Component Wiring

Source components in `C:\Users\jonny\OneDrive\Documents\AEGIS\ARCANE QUANTUM BRAIN\src\`:

- `components/SwarmVisualizer.tsx` -> `/api/swarm/initiate`, `/api/swarm/poll`
- `components/TelemetryDashboard.tsx` -> `/api/telemetry`, `/api/system/health-history`, `/api/debate/telemetry`, `/api/federated/collective-dream/1`
- `App.tsx` chat submit -> `/api/chat` bridge -> `/api/neurocore/intent`
- OMNIBUS overlay buttons -> `/api/neurocore/connect`, `/api/neurocore/status`, `/api/telemetry/summary`

## /api/chat bridge contract

Input:
- `message` or `question` or `text`
- optional `provider`, `confidence`, `model`, `agentId`, `agentRole`, `history`, `sessionTraceId`, `contextData`

Bridge must:
- compute triage provider from `confidence` if `provider` is absent
- default `confidence` to `0.6` when missing
- send `intent`, `source`, `confidence`, `features`, `requiresConfirmation: false`
- omit `phase` when caller did not provide it; never send `phase: null`

Output:
- `response`
- `provider`
- optional `confidence`
- optional `swarmId`

## Tunnel quirk

Installed `cloudflared` via winget to `C:\Program Files (x86)\cloudflared\cloudflared.exe`. Quick tunnel command:
```bash
/c/Program\ Files\ \(x86\)/cloudflared/cloudflared.exe tunnel --url http://localhost:3001
```
