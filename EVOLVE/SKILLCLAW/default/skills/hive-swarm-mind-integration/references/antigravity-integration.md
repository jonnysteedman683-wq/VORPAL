# Antigravity Integration Reference

## Context
- User runs Antigravity as cron agents on OMNIBUS with daily 5AM upgrade + hourly optimization.
- Jules bot handles PR automation separately.
- Integration goal: expose Antigravity through OMNIBUS backend so Sentinel/Swarm UI can trigger it without leaving the unified frontend.

## Windows Install Reality (2026-08-06)
- Electron app: `C:\Users\jonny\AppData\Local\Programs\antigravity\Antigravity.exe`
- Agent API wrapper: `C:\Users\jonny\.gemini\antigravity\bin\agentapi.bat`
- Language server: `C:\Users\jonny\AppData\Local\Programs\antigravity\resources\bin\language_server.exe`
- No standalone `agy.exe` on PATH by default.
- `command -v agy` returns not found.
- `Antigravity.exe --version` launches the app, not a version print.

## Backend Route
- Route: `POST /api/antigravity/run`
- Shells out to `AG_BIN` or `agy -p <task> --model <model> --print-timeout <ms>`
- Default task if missing: `Run OMNIBUS maintenance and suggest improvements.`
- Clamps `printTimeout` to `[1000, 20 * 60 * 1000]`
- Returns `{ success, command, workdir, timeoutMs, stdout, stderr, code }`
- Logs to telemetry as `antigravity-run` intent.

## Wrapper Requirement
If `agy` is not on PATH, either:
- Set `AG_BIN` env var to a real CLI wrapper path
- Create a wrapper script that invokes Antigravity non-interactively and set `AG_BIN` to it

## Pitfalls
- `npm list -g antigravity` timed out in this session; do not rely on npm global modules for Antigravity CLI presence on Windows.
- Electron app launch is interactive; `/api/antigravity/route` needs a non-interactive CLI entrypoint.
- `language_server.exe` requires Electron runtime context; it is not a direct CLI substitute for `agy -p`.
