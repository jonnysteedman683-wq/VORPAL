# Windows process/port commands for OMNIBUS

These are the exact command shapes used during recent sessions.

## Inspect port owner

```bash
netstat -ano | grep :3000
```

Output includes `LISTENING` entries with the owning PID.

## Kill owner process

```bash
powershell -Command "Stop-Process -Id 17564 -Force -ErrorAction SilentlyContinue"
```

## Background launch under Hermes control

```bash
terminal(background=true, command="cd '/c/Users/jonny/OneDrive/Desktop/AQB/OMNIBUS' && PORT=3001 node server.cjs", notify_on_complete=true)
```

## Poll server status

```bash
curl http://localhost:3001/api/neurocore/health
```

## Notes

- `tasklist //FI "PID eq <PID>"` may return no rows from MSYS bash even when the process exists.
- After `Stop-Process`, wait a few seconds before rebinding.
- `TIME_WAIT` and `FIN_WAIT_2` do not block rebinding; `LISTENING` does.
