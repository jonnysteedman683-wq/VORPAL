# Windows Unified Sentinel Wiring Notes

## Server file
`C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS\server.cjs`

## Key routes
- `GET /` → unified Sentinel UI with OMNIBUS overlay
- `GET /sentinel` → same unified UI
- `GET /api/neurocore/health` → neurocore health
- `POST /api/neurocore/connect` → connect swarm adapter
- `POST /api/neurocore/intent` → dispatch intent with confidence triage
- `GET /api/telemetry/summary` → telemetry summary
- `POST /api/swarm/initiate` → ARC swarm bridge into neurocore
- `GET /api/swarm/poll?swarmId=` → poll ARC swarm state

## Unified overlay
Injected into Sentinel `index.html` before `</head>`:
- Top bar buttons: Connect, Status, Telemetry
- Panel fetches:
  - Connect → `/api/neurocore/connect`
  - Status → `/api/neurocore/status`
  - Telemetry → `/api/telemetry/summary`, `/api/telemetry/intents?limit=20`, `/api/telemetry/histogram`

## Bridge fix
- Renamed `neurocore/adapters/omnibus-swarm/spike-comm.js` → `spike-comm.cjs`
- Updated `neurocore-bridge.cjs` import path to `.cjs`

## Tunnel
- Tool: `cloudflared` installed via `winget install --id Cloudflare.cloudflared`
- Quick tunnel: `cloudflared tunnel --url http://localhost:3001`
- Example public URL: `https://laser-tells-drives-africa.trycloudflare.com`
- Executable path on this machine: `/c/Program Files (x86)/cloudflared/cloudflared.exe`

## Test command
`cd 'C:\Users\jonny\OneDrive\Desktop\AQB\OMNIBUS' && npm test`
Expected: 41/41 passing
