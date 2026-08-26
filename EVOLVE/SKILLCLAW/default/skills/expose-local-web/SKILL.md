---
name: expose-local-web
description: "Expose local server to web via tunnel; precheck the port."
category: devops
version: 1.0.0
author: AURORAL
license: MIT
created: 2026-08-20
metadata:
  hermes:
    tags: [tunnel, cloudflared, ngrok, expose, web, devops]
    related_skills: [omnibus-neurocore-operations, hermes-cron-patterns]
---

# Expose Local Web Server

## When to Use
- User says "launch to a web URL", "make it public", "expose localhost"
- Need a public HTTPS URL for a local server (OMNIBUS, Sentinel, Hive, demos)
- Quick share without deploying to a host

## STEP-BY-STEP

1. **Precheck the port is actually listening** (don't tunnel a dead server):
   ```
   netstat -ano | grep :<PORT>
   ```
   Only `LISTENING` means owned. If nothing listens, start the server first
   (background terminal), THEN tunnel.

2. **Pick the tunnel tool**:
   - **cloudflared** (preferred, no account for quick tunnels):
     ```
     cloudflared tunnel --url http://localhost:<PORT>
     ```
     Prints an `https://*.trycloudflare.com` URL. Ephemeral — dies with the process.
   - **ngrok** (if cloudflared unavailable):
     ```
     ngrok http <PORT>
     ```
     Needs an authtoken for sustained use; free tier gives a random subdomain.

3. **Verify the public URL serves** before handing it off:
   ```
   curl -fsS https://<tunnel-url>/api/health    # or / or /health
   ```
   Report the URL only after a 2xx/3xx from the tunnel, not just from localhost.

4. **Keep the tunnel alive**: run it in a background terminal
   (`terminal(background=true, notify_on_complete=true)`); record session_id.
   A tunnel is a long-running process — never foreground it.

## PITFALLS
- **Tunneling a not-yet-up server** → symptom: URL returns connection refused.
  Fix: confirm `LISTENING` + a localhost curl FIRST.
- **EADDRINUSE on the server** → the app didn't start, so the tunnel has nothing
  to serve. Fix: resolve the port conflict (see omnibus-neurocore-operations)
  before tunneling. Prefer `PORT=3001`.
- **Ephemeral URLs** → cloudflared quick tunnel URL changes every restart. For a
  stable URL use a named tunnel (`cloudflared tunnel create <name>` + DNS CNAME).
- **Public exposure = security surface** → only expose dev servers you control;
  never tunnel a server that handles secrets/creds without auth in front.

## VERIFICATION
- `curl -fsS <tunnel-url>/<health-or-root>` returns success from OUTSIDE
  (the tunnel URL, not localhost). Report that URL.
