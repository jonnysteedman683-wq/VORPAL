# Windows Port Recovery Reference

## Goal

Take over a localhost port on Windows safely when `EADDRINUSE` blocks a new OMNIBUS instance.

## Step-by-step

1. Find owner PID:
   - `netstat -ano | grep :3001`
   - Keep only the `LISTENING` entry; ignore `TIME_WAIT`, `FIN_WAIT_2`, `CLOSE_WAIT`.
2. Inspect owner:
   - `tasklist //FI "PID eq <PID>" //FO CSV`
3. Stop owner if it is a known OMNIBUS/Node instance:
   - `powershell -Command "Stop-Process -Id <PID> -Force -ErrorAction SilentlyContinue"`
   - Retry with `taskkill //F //PID <PID>` if needed.
4. Re-check:
   - `netstat -ano | grep :3001`
   - If still `LISTENING`, do not start another server on the same port.
5. If you cannot free the port:
   - switch to `PORT=3001 node server.cjs`
   - or another unused port.

## Notes

- `bash: no job control in this shell` during background `terminal()` runs is harmless MSYS noise.
- Do not kill system processes or unrelated browsers without user direction.
- Prefer `terminal(background=true, notify_on_complete=true)` for servers so Hermes owns the session.
