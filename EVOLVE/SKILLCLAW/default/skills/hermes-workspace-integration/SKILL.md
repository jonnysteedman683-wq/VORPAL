---
name: hermes-workspace-integration
description: hermes-workspace sidecar GUI setup
author: jonny
version: 0.1.0
license: MIT
tags:
  - gui
  - workspace
  - sidecar
related_skills:
  - hermes-workspace
trigger: Install hermes-workspace GUI
---

# HERMES-WORKSPACE-INTEGRATION
**Trigger:** Install hermes-workspace GUI.

**Behavior:** Clones `outsourc-e/hermes-workspace`, installs `npm install && npm run dev`, opens at `localhost:3000`. Hermes agent must run separately. Session inspector auto-populates from `~/.hermes/`.

**Command:**
```bash
git clone https://github.com/outsourc-e/hermes-workspace
cd hermes-workspace
npm install && npm run dev
```

**Verification:** `Cannot connect to agent` → start Hermes with `hermes start`, then reload workspace.

**Pattern Proved:** hermes-workspace is a sidecar alongside CLI, not a replacement. Session inspector saves hours debugging corrupted skill chains.

**When to Use:** When you work with Hermes daily and want to manage skills or browse memory without touching the terminal.

**Skill Mutation:** ITERATE — refine install commands per OS (WSL2 vs macOS vs native Windows).