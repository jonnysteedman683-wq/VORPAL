---
name: skillclaw-integration
description: SkillClaw post-task evolution layer
author: jonny
version: 0.1.0
license: MIT
tags:
  - skill-evolution
  - aut-evolution
  - skill-management
related_skills:
  - skillclaw
trigger: Install SkillClaw for skill auto-evolution
---

# SKILLCLAW-INTEGRATION
**Trigger:** Install SkillClaw for skill auto-evolution.

**Behavior:** `pip install skillclaw` then `skillclaw doctor hermes` validates all skill files against HERM v1.1 schema, flags duplicates, syntax errors, removed tool references.

**Commands:**
```bash
pip install skillclaw

# Validate all skill files against HERM v1.1 schema before a batch run
skillclaw doctor hermes

# Roll back to last clean snapshot if a batch run corrupts skill state
skillclaw restore hermes

# Merge duplicate signatures
skillclaw dedup hermes
```

**Expected output of `skillclaw doctor hermes`:**
```
✓ 47 skills validated
⚠ 3 duplicate signatures found — run `skillclaw dedup hermes` to merge
✗ 1 skill references removed tool `search_v1` — update or delete
```

**If it fails:** `ModuleNotFoundError: No module named 'skillclaw'` → activate Hermes env first: `source ~/.hermes/env/bin/activate`, then reinstall.

**Pattern Proved:** Hermes creates skill files automatically after complex tasks. SkillClaw improves and deduplicates those files using real session data — they work together, not in competition.

**When to Use:** After running Hermes for a few weeks and accumulating 30–40 skills — SkillClaw manages the redundancy that naturally builds up.

## Evolve-server wiring (verified 2026-08-26 on VORPAL)
The skill-*evolution* engine is a separate daemon: `skillclaw-evolve-server` (source in `C:/Users/jonny/skillclaw/evolve_server/`).

- **Storage:** use `--storage-backend local --local-root <WS>` — no OSS/S3 needed. Workspace layout is `{WS}/{group-id}/{sessions,manifest.jsonl,skills/}` (group-id defaults to `default`, so sessions live under `default/sessions/*.json`, manifest at `default/manifest.jsonl`, skills flat at `default/skills/<name>/SKILL.md`).
- **LLM auth:** do NOT rely on the SkillClaw config's DeepSeek key (it can be dead — 402 Insufficient Balance). Use the Nous token from Hermes auth.json: `providers.nous.access_token`, with `OPENAI_BASE_URL=https://inference-api.nousresearch.com/v1` and `EVOLVE_MODEL=stealth/ox-alpha`.
- **Command:** `python -m evolve_server --engine workflow --once --storage-backend local --local-root <WS> --group-id default --publish-mode validated` (validated stages candidates; direct writes live).
- **Lifecycle:** drains `sessions/*.json` (consumes them), LLM decides per session: skip / create_skill / improve_skill / optimize_description. Evolved skills get versioned history `skills/<name>/history/vN.md + vN_evidence.md`. `--interval N` runs a daemon loop.
- **Pitfalls:** stale config (`skills.dir` pointing at deleted profile) breaks `doctor hermes` — fix with `skillclaw config skills.dir <dir>`. A run that hits LLM errors RETAINS sessions in queue (no data loss); a clean cycle consumes them.

**Skill Mutation:** ITERATE — refine doctor/dedup/restore commands per Hermes version.
---