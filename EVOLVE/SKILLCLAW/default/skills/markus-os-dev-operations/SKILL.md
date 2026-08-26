---
name: markus-os-dev-operations
category: software-development
description: Use when operating, deploying, or monitoring MARKUS OS — server lifecycle, port 8128, rolling logs, git flow.
version: 1.0.0
author: Jonny Steedman
license: MIT
metadata:
  hermes:
    tags: [markus-os, devops, server, monitoring, deploy]
    related_skills: [markus-upgrade-start, markus-os-development, self-evolution-and-code-optimization]
---

# MARKUS OS Dev Operations

## When to Use
Use when running, restarting, monitoring, or shipping MARKUS OS.

## Operations
- Server: `python markus_server.py` → serves UI + SSE stream on **port 8128**.
- Health: `curl http://localhost:8128/api/status` → expect `"status": "ONLINE"`.
- Rolling logs: `~/.hermes/cron_log/upgrade-YYYYMMDD-HHMM.log`.
- Integration gate: `python markus_integration_test.py` → expect 9/9 PASS.
- Git flow: commit + push to `origin/master` on a clean green tree.

## Pitfalls
- Do NOT kill PID 8128 to run tests — the integration harness never binds that port.
- `markus_private` runtime root is `Desktop/New folder/markus_private`; repo is `Desktop/MARKUS-OS`.
- Upgrade cycles do not restart the live server; edits to `markus_server.py` require a manual restart.
