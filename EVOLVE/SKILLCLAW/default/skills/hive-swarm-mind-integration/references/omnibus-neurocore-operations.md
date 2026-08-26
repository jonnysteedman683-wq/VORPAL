---
name: omnibus-neurocore-operations
description: Start/restart OMNIBUS and verify Neurocore on Windows.
---

# OMNIBUS / Neurocore Operations

Manage the OMNIBUS backend lifecycle and verify Neurocore integration on Windows. Use when the user asks to start, restart, verify, or debug the local OMNIBUS server, `/api/neurocore/*` endpoints, or the Neurocore bridge.

## Pre-flight

1. Check whether something already owns the target port:
   - `netstat -ano | grep :3000` (or the configured port)
2. If another PID is listening, do not blindly start a second server.
3. Identify the owner process. If it is a stale OMNIBUS instance, stop it safely; otherwise pick a different port.

## Safe port takeover on Windows

Preferred kill order:
- `powershell -Command "Stop-Process -Id <PID> -Force -ErrorAction SilentlyContinue"`
- If that fails, retry with taskkill or accept that the port is owned by an unrelated process.

After stopping, wait a moment and re-check `netstat` before rebinding.

## Background server launch

Launch OMNIBUS under Hermes process control so it survives across actions and can be inspected later:

- `terminal(background=true, command="cd '<OMNIBUS_PATH>' && node server.cjs", notify_on_complete=true)`
- Record the returned `session_id`; use `process(action='log'/'poll')` to inspect live output.
- Do not use foreground `node server.cjs` for long-running servers.

## Port override

If port `3000` is unavailable, use the environment variable the server already supports:

- `PORT=3001 node server.cjs`

Health check after launch:
- `curl http://localhost:<PORT>/api/neurocore/health`

## Neurocore connect flow

OMNIBUS requires an explicit connect before intent dispatch.

1. `POST /api/neurocore/connect`
2. Expect `success: true`, `status: connected`, and `capabilities`.
3. Only then call `POST /api/neurocore/intent`.

If `/api/neurocore/intent` returns `Swarm adapter not connected`, the connect step was skipped or failed.

## Endpoint verification checklist

- `GET /api/neurocore/health` → `status: healthy` or `connected`
- `POST /api/neurocore/connect` → `success: true`
- `POST /api/neurocore/intent` with `confidence: 0.9` → returns `actionId`, `status: completed`
- `agent_system.dispatch()` in browser should call `/api/neurocore/intent` first, fallback to `/api/chat`

## Neurocore bridge ESM/CJS fix

If the server logs contain `module is not defined in ES module scope` and point to `spike-comm.js`, the root cause is a CJS file under an ESM package.

Fix:
1. Rename `neurocore/adapters/omnibus-swarm/spike-comm.js` → `spike-comm.cjs`
2. Update `neurocore-bridge.cjs` to import `spike-comm.cjs`
3. Restart OMNIBUS

## Sentinel unified UI mount

To make Sentinel the root UI instead of OMNIBUS HTML:
1. Mount Sentinel `dist/` assets at `/assets` and `/sentinel/assets`
2. Inject OMNIBUS overlay HTML before `</head>` in Sentinel's `index.html`
3. Register `/` and `/sentinel` before `app.use(express.static(__dirname))`, otherwise the root static handler will serve OMNIBUS `index.html` first
4. Keep `/api/*` routes registered before Sentinel mounts, or ensure Sentinel's catch-all does not shadow API routes

## Background server pattern on Windows

Use `terminal(background=true, notify_on_complete=true)` for long-running servers. Foreground `node server.cjs` will time out and force unnecessary restarts.

## Cloudflare quick tunnel

To expose localhost publicly without account setup:
- `cloudflared tunnel --url http://localhost:3001`
- The quick tunnel URL is ephemeral; use named tunnels for production

## Pitfalls

- `bash: no job control in this shell` is harmless background noise from MSYS; ignore it.
- `EADDRINUSE` means another instance already owns the port; do not retry the same bind.
- `netstat` on Windows shows `LISTENING` and `TIME_WAIT`; only `LISTENING` means the port is actively owned.
- Do not kill system processes or unrelated Node servers; confirm the PID belongs to OMNIBUS before stopping.
- Route order matters: static middleware before route handlers can swallow root paths; put UI mounts before `express.static(__dirname)` if you want Sentinel at `/`.

## Continuous Refinement & Upgrade Cadence

- **24/7 Autonomous Loops**: Run upgrade refinement, optimizations, and review passes at 2x cadence (`every 30m` via Hermes cron jobs `continuous-upgrade-refinement` and `hermes-review-ag-cadence`).
- **Safety Gate**: All passes must enforce `npm test` + `tsc --noEmit` + zero forbidden execution patterns before merge.

## References

- `references/windows-process-management.md` — exact Windows command sequences for port/process inspection and safe takeover.
