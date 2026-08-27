---
name: self-evolution-and-code-optimization
category: software-development
description: Use when a system self-optimizes code, iterates on debate verdicts, or captures PHOENIX CLI AST insights. MARKUS OS evolution feedback loop.
version: 1.0.0
author: Jonny Steedman
license: MIT
metadata:
  hermes:
    tags: [markus-os, self-evolution, code-optimization, phoenix-cli, debate-pipeline]
    related_skills: [markus-os-development, markus-os-dev-operations, markus-upgrade-start]
---

# Self-Evolution & Code Optimization

## When to Use
Use when MARKUS OS (or any agent loop) captures an improvement signal from the debate
pipeline, PHOENIX CLI AST validation, or reflexion passes, and needs to fold that insight
back into code or process.

## Core Loop
1. **Signal** — a cortex thought matches an evolution pattern (debate verdict, AST result, reflexion critique)
2. **Pattern Match** — CortexSkillPatcher matches the thought against `SKILL_UPGRADE_PATTERNS`
3. **Patch** — a MICRO-APPEND / ITERATE patch is appended under the Auto-Patch Section below
4. **Verify** — `python -m py_compile` + green `phoenix_cli.py batch .` before promotion

## Pitfalls
- Never overwrite the Auto-Patch Section — it is machine-managed.
- A patch that fails py_compile must be reverted, not left in place.
- Reward weights in the dice engine update only AFTER a verified green patch.

# === Auto-Patch Section ===
- Pattern: Debate pipeline effectiveness. Verdict: Debate verdict: markus-forensic-sentinel (confidence=24.8%, consensus=BLOCKED) (auto-appended 1787715080)
- Pattern: Debate pipeline effectiveness. Verdict: Debate verdict: markus-forensic-sentinel (confidence=25.6%, consensus=BLOCKED) (auto-appended 1787714731)
- Pattern: Debate pipeline effectiveness. Verdict: Debate verdict: markus-forensic-sentinel (confidence=24.9%, consensus=BLOCKED) (auto-appended 1787680420)
- Pattern: Debate pipeline effectiveness. Verdict: Debate verdict: markus-forensic-sentinel (confidence=25.0%, consensus=BLOCKED) (auto-appended 1787680346)
# This section is auto-managed by CortexSkillPatcher. Do not edit manually.
- Pattern: Debate pipeline effectiveness. Verdict: Debate verdict: markus-forensic-sentinel (confidence=25.0%, consensus=BLOCKED) (auto-appended 1787680051)
