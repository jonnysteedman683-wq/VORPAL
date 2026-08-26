# SUPRIME Bridge Verified State

This reference documents the exact integration state that was verified in-session.

## Repos

- Hermes Hive: `C:/Users/jonny/HERMES-HIVE`
- SUPRIME: `C:/Users/jonny/SUPRIME`
- SUPRIME bridge module: `suprime/bridge.py`

## Install

```bash
cd C:/Users/jonny/SUPRIME
pip install -e ".[bridge]"
```

## Start bridge

```bash
cd C:/Users/jonny/SUPRIME
python -m suprime bridge --port 8123
```

## Verified bridge endpoints

- `GET http://localhost:8123/health`
- `POST http://localhost:8123/swarm/start`
- `POST http://localhost:8123/swarm/stop`
- `GET http://localhost:8123/swarm/status`
- `GET http://localhost:8123/tasks`
- `POST http://localhost:8123/tasks/submit`
- `POST http://localhost:8123/worker/:kind`
- `GET/POST http://localhost:8123/store/:key`

## Verified Hermes Hive proxy routes

- `GET http://localhost:3000/api/suprime/health`
- `POST http://localhost:3000/api/suprime/swarm/start`
- `POST http://localhost:3000/api/suprime/swarm/stop`
- `GET http://localhost:3000/api/suprime/status`
- `POST http://localhost:3000/api/suprime/worker/:kind`
- `POST http://localhost:3000/api/suprime/tasks/submit`
- `GET http://localhost:3000/api/suprime/tasks`

## Verified proxy pattern

Each proxy route in `src/server/apiMiddleware.ts` must wrap the bridge call in `try/catch` and return `502` on failure. This keeps Hermes authoritative when SUPRIME is unreachable.

**Mirroring Hermes commands into SUPRIME:** when `/api/hermes/command` processes a human command, optionally mirror it as a SUPRIME task with `kind: 'hermes_command'` and payload `{ command, result }`. Swallow mirror errors so Hermes stays the source of truth.

```ts
// inside /api/hermes/command handler
const result = await hermesEngine.processHumanCommand(command);
try {
  await suprimeBridge.submitTask('hermes_command', { command, result: result as Record<string, unknown> });
} catch {
  // Hermes remains authoritative
}
```

## Verified behavior

- Bridge starts with auto-assigned TCP port.
- Submitting a task returns `{"status":"submitted","task_id":"...","kind":"..."}`.
- Listing tasks returns `{"status":"ok","tasks":[...]}` with task `state`, `owner`, `result`, and `error`.
- Registering a worker kind returns `{"status":"registered","kind":"...","node_id":"..."}`.

## Windows startup pitfall

If startup fails with `NameError: name 'os' is not defined` in `suprime/cli.py`, the file is missing `import os`. Add it at the top before retrying.
