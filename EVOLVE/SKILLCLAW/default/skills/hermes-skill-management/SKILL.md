---
name: hermes-skill-management
description: "Use when installing or enabling Hermes skills via CLI."
version: 1.0.0
author: ox-alpha session 2026-08-26
license: MIT
metadata:
  hermes:
    tags: [hermes, skills, install, cli]
    related_skills: [hermes-upgrade-check]
category: devops
---

# Hermes Skill Management (acquire / verify / enable)

## When to Use
- User wants a new skill acquired ("install X skill", "we can acquire new skills")
- A newly installed skill shows `disabled` in `hermes skills list`
- Scouting GitHub for high-value agent skills when web tools are dead

## Install

```bash
hermes skills install <owner/repo[/path/to/skill]> --yes
```

- Identifier is `owner/repo/skill-name` **including any nested directory path**.
- PITFALL (proven 2026-08-26): if the repo nests skills under `skills/<name>/`, a bare
  `owner/repo/skill-name` fails with `Could not fetch ... from any source`. List the repo
  contents first (`gh api repos/<o>/<r>/contents/skills -q '.[].name'`) and use the FULL
  path, e.g. `tigerless-labs/paper-radar/skills/paper-radar`.
- Direct SKILL.md URLs also work; use `--name` when frontmatter lacks `name:`.
- Each install runs a security scan (provenance + hash + rules). Read the verdict;
  `--force` overrides a block — avoid unless user directs.

## Enabling a skill that shows "disabled"

PITFALL (proven 2026-08-26): there is NO `hermes skills enable` subcommand.
Valid actions: trust, untrust, browse, search, install, inspect, list, check, update,
audit, uninstall, reset, list-modified, diff, opt-out, opt-in, repair-official, publish,
snapshot, tap, config.

Disabled state = the skill's name listed in `config.yaml` under `skills.disabled`.
To enable:
1. Check why: `hermes skills list | grep <name>` → status column shows `enabled/disabled`.
2. Remove it from the list: `hermes config set skills.disabled "[remaining,names]"`.
   YAML flow-list syntax works; a warning about unrecognized key is benign.
3. Verify: `hermes skills list | grep <name>` → must show `enabled`.

Note: `skills.opt-in` is unrelated — it re-seeds BUNDLED skills via `.no-bundled-skills`
marker; it does not take a skill name.

## Verification (mandatory before reporting success)

```
hermes skills list            # new entry present, trusted, enabled
```
For script-bearing skills, smoke-test the actual script (run its `--help`, then one real
invocation in `$LOCALAPPDATA/Temp`) before telling the user it works.

## Scouting sources

- Official pack: `anthropics/skills/skills/<name>` (skill-creator, mcp-builder,
  webapp-testing, frontend-design, web-artifacts-builder, pdf, docx, xlsx, pptx).
- Discovery when web tools are dead: `gh search repos "agent skills"` /
  `gh api repos/<o>/<r>/contents/skills`.

## Real run (2026-08-26)
- paper-radar: bare identifier failed → full nested path worked; smoke test passed
  (use `--no-scrape` for quick runs; author-block scraping ~130s per 300 papers).
- anthropics pack: all 9 installed trusted; docx/pdf/xlsx initially disabled via stale
  `skills.disabled` entries; removed from list → enabled.
