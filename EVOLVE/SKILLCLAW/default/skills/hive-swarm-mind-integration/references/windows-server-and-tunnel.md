# Windows Server and Tunnel Notes

## Port lifecycle on Windows

- Preferred check: `netstat -ano | grep '3001' | grep 'LISTENING'`
- Kill all listeners on port: `netstat -ano | grep '3001' | grep 'LISTENING' | awk '{print $5}' | sort -u | xargs -I{} taskkill /F /PID {}`
- After killing, wait a moment before rebinding.
- Background launch with Hermes tracking: `terminal(command="cd '/c/Users/jonny/OneDrive/Desktop/AQB/OMNIBUS' && PORT=3001 node server.cjs", background=true, notify_on_complete=true)`
- If a background launch exits with `EADDRINUSE`, do not blindly relaunch; verify the existing listener first.

## Live verification pattern

- `curl -s http://localhost:3001/api/neurocore/health`
- `curl -s -X POST http://localhost:3001/api/neurocore/connect -H 'content-type: application/json' -d '{}'`
- `curl -s -X POST http://localhost:3001/api/chat -H 'content-type: application/json' -d '{"message":"check","history":[]}'`

## Cloudflare quick tunnel

- Install: `winget install --id Cloudflare.cloudflared --accept-package-agreements --accept-source-agreements`
- Binary: `C:\Program Files (x86)\cloudflared\cloudflared.exe`
- Start: `cloudflared tunnel --url http://localhost:3001`
- Tunnel is ephemeral; capture the public URL from process output for temporary external access.
