---
name: citadel-brain
description: Use when querying or writing Citadel vault notes.
version: 0.1.0
author: Jonny Steedman, Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [Citadel, Obsidian, Recall, Watermark, Handoff]
    related_skills: [obsidian]
---

# Citadel Brain

Query and write the Citadel vault through `citadel_recall.py`. Writes stamp P5 watermarks and P6 `HR-` receipts. Do not git-commit from this skill.

## When to Use

- Looking up Citadel notes (Memory, Decisions, Protocols, Goals)
- Capturing a decision, task, or memory into the vault
- Anything that should carry a watermark / handoff receipt

Don't use for: editing `.obsidian/` plugin state, SmartEnv, or git/PRs.

## Prerequisites

- Python 3.11 (`python`)
- Vault scripts at `C:/Users/jonny/OneDrive/Desktop/The-Citadel-Vault/The-Citadel-Vault/scripts/`
- MSYS: pass `C:/Users/...` paths to `python`, never `/c/Users/...`

## How to Run

```bash
python C:/Users/jonny/OneDrive/Desktop/The-Citadel-Vault/The-Citadel-Vault/scripts/citadel_recall.py "MARKUS handoff" --limit 5
```

Import from `scripts/` (add that directory to `sys.path` with `os.path.abspath`, not `Path.resolve()`):

```python
import os, sys
scripts = os.path.dirname(os.path.abspath(r"C:/Users/jonny/OneDrive/Desktop/The-Citadel-Vault/The-Citadel-Vault/scripts/citadel_recall.py"))
sys.path.insert(0, scripts)
import citadel_recall as c
hits = c.search("watermark protocol", limit=5)
note = c.read_note(hits[0]["path"])
created = c.create_note(
    "Title",
    "body",
    section="Memory",
    source_run_id="hermes:<session>",
    reason="why this note exists",
    evidence="[MEDIUM]",
)
# created["receipt_id"] like HR-20260828-001
```

Indexer (no git):

```bash
python C:/Users/jonny/OneDrive/Desktop/The-Citadel-Vault/The-Citadel-Vault/scripts/citadel_indexer.py droplet start
python C:/Users/jonny/OneDrive/Desktop/The-Citadel-Vault/The-Citadel-Vault/scripts/citadel_indexer.py droplet capture "Title" "Body" Memory
```

`citadel_indexer.py … sync` prints `refused:` — do not work around it.

## Procedure

1. **Search** — `c.search(query, limit=5, section=None)`. Done when you have ranked hits with `path`, `score`, `evidence`.
2. **Read** — `c.read_note(rel_path)` for the top 3. Done when the answer is grounded in note text, not the hit snippet.
3. **Write** — `c.create_note(...)` only to `Memory`, `Decisions Log`, `Goals`, `Tasks`, `Reports`. Done when the return dict has `receipt_id` matching `HR-YYYYMMDD-NNN` and `sha256`.
4. **Do not commit.** Leave the working tree dirty. Human-gate git.

## Pitfalls

- Empty `source_run_id` / `reason` is rejected.
- `../Information` and other non-allowlist sections raise `ValueError`.
- `Path(__file__).resolve()` under MSYS can yield `C:\c\Users\...`. Use `os.path.abspath`.
- Token cost: never dump the whole vault; search then read.
- Plugin / SmartEnv files are not notes. Ignore them.

## Verification

```bash
python C:/Users/jonny/OneDrive/Desktop/The-Citadel-Vault/The-Citadel-Vault/scripts/hermes_verify_citadel_recall.py
```

Expected: `OVERALL: PASS` including watermark frontmatter, receipt id, handoff log append, receipt sequence.
