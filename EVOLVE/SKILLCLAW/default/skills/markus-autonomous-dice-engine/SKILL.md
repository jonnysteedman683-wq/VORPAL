---
name: markus-autonomous-dice-engine
category: software-development
description: Use when driving MARKUS OS autonomous upgrade cycles — dice roll, stage selection, reward-weighted topology adaptation.
version: 1.0.0
author: Jonny Steedman
license: MIT
metadata:
  hermes:
    tags: [markus-os, dice-engine, autonomous, upgrade, reward]
    related_skills: [markus-upgrade-start, markus-os-development, self-evolution-and-code-optimization]
---

# MARKUS Autonomous Dice Engine

## When to Use
Use when selecting the next autonomous upgrade target for MARKUS OS. The dice engine
maps a random roll to an upgrade stage and adapts weights by reward feedback.

## Mechanics
- Dice faces: 1=UI refresh, 2=BACKEND, 3=AI agent re-sync, 4=Canvas/Electron, 5=Hardening.
- Reward `1.00` on a fully green cycle updates the dice weight table.
- Fallback to `secrets.choice([1..6])` if numpy is unavailable.
- Rolls are logged with the upgrade cycle in `~/.hermes/cron_log/upgrade-*.log`.

## Pitfalls
- A cycle that fails validation must NOT update reward weights.
- Stage 3 kernel probe: use `k.running` / `k.process_table`, never a `mode` attribute.
