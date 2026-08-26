# HERMES-HIVE local operations

Use when the user asks to start, verify, drive, or upgrade the local HERMES-HIVE swarm control plane on Windows.

## Known-good location

- Repo: `C:/Users/jonny/HERMES-HIVE`
- Project anchor: `HERMES HIVE` Hermes project

## Background dev server launch

Preferred on Windows:

```text
terminal(background=true, command="cd /c/Users/jonny/HERMES-HIVE && npm run dev", notify_on_complete=true)
```

- Vite serves on `http://localhost:3000`
- HMR is disabled when `DISABLE_HMR=true`
- Do not use foreground `npm run dev` for long-running sessions

## Health + API verification

- `GET http://localhost:3000/api/health` → `{"status":"ok","hive":"HERMES HIVE",...}`
- `GET http://localhost:3000/api/agents` → seeded/default agent list
- `GET http://localhost:3000/api/events?limit=5` → live event stream history
- `GET http://localhost:3000/api/diagnostics` → hive metrics including `hiveHealthPct`
- `GET http://localhost:3000/api/events/stream` → SSE endpoint for real-time updates

## Driving the hive

- `POST /api/hermes/command` with `{"command":"..."}` creates a mission, dispatches agents, and returns a decision/mission ID
- `POST /api/quick-actions/trigger` accepts `scenario` values: `high_performance_cluster`, `security_audit`, `energy_saving_sleep`, `quantum_crypto`, `refactor_core`
- `POST /api/demo/trigger` is the demo-tagged equivalent
- `POST /api/agents/{id}/{pause,resume,terminate,restart}` controls agent lifecycle
- `EventSource('/api/events/stream')` for live UI updates

## Persistence caveat

The current hive is in-memory only. Restarting `npm run dev` resets agents, missions, memory, events, and learning state. Do not treat post-restart state as continuous.

## Local model fallback caveat

Hermes config may reference `http://localhost:11434/v1` / `hermes3`, but Ollama is not guaranteed to be running on this Windows host. If local fallback is required, start Ollama explicitly before relying on `hermes3`.
