---
name: hermes-upgrade-check
description: "Check Hermes upgrades via gh CLI when web_search fails."
category: devops
version: 1.0.0
author: AURORAL
license: MIT
created: 2026-08-20
metadata:
  hermes:
    tags: [hermes, upgrade, github, gh-cli, devops]
    related_skills: [hermes-agent]
---

# Hermes / GitHub Upgrade Check (no web tools)

## When to Use
- User asks "search GitHub for hermes upgrades" / "what's the latest version" / "am I behind"
- `web_search` returns "Web tools are not configured" / no Firecrawl credits
- Any task that needs release notes, version deltas, or update availability for a GitHub-backed tool
- User wants to actually PERFORM a Hermes upgrade (not just check)

## STEP-BY-STEP (CHECK phase — safe, no mutation)

1. **Confirm web tools are dead** (skip if you already know):
   `web_search` → if error mentions FIRECRAWL_API_KEY / no paid credits, route everything through `gh`.

2. **Check current install vs latest tag** (Hermes-specific):
   - Current: `hermes --version`  (prints e.g. `Hermes Agent v0.20.0 (2026.8.3)`)
   - Available: `hermes update --check`  (prints "Update available (behind origin/main)" or "up to date")

3. **Pull release tags + notes from upstream** (works for any repo):
   ```
   gh api repos/NousResearch/hermes-agent/releases --paginate \
     -q '.[] | "\(.tag_name)  \(.published_at)  \(.name)"'
   ```
   Then for each tag you care about:
   ```
   gh api repos/NousResearch/hermes-agent/releases/tags/<TAG> --jq '.body'
   ```

4. **Latest commit activity / specific fixes**:
   ```
   gh api repos/NousResearch/hermes-agent/commits --paginate \
     -q '.[] | "\(.commit.author.date)  \(.commit.message | split("\n")[0])"'
   ```

5. **Search across the user's own repos** (if looking for their upgrade commits):
   ```
   gh search commits "hermes upgrade" --owner=jonnysteedman683-wq --limit 10 \
     --json repository,sha,commit,url
   ```
   NOTE: valid `--json` fields for `gh search commits` are
   `author, commit, committer, id, parents, repository, sha, url`.
   There is NO `commitDate` field — passing it errors with "Unknown JSON field".
   Use `commit.author.date` / `commit.committer.date` from the `commit` object instead.

6. **Auth check** (needed once): `gh auth status` → expect
   `✓ Logged in to github.com account jonnysteedman683-wq (keyring)`.

## UPGRADE LOOP (PERFORM phase — Windows)

**CRITICAL WINDOWS FACT (proven 2026-08-20):** A Hermes upgrade is only
COMPLETE when the venv dependency reinstall lands. That step requires the
venv's native `.pyd` files to be unlocked. Any running Hermes process
(desktop backends, skill workers, your active chat session) holds those
locks. So:

- `hermes update` (plain): if other Hermes processes hold `.pyd`, it does
  the backup + git pull + launcher refresh + gateway restart, then **SKIPS
  the venv reinstall** and exits 0 — leaving you on OLD deps, version
  string unchanged. This is a PARTIAL upgrade, not success.
- `--force`: only lifts the `hermes.exe` concurrent-process guard (lets a
  reboot-deferred .exe swap proceed). It does NOT bypass the venv lock.
- `--force-venv`: required to mutate the venv while other processes hold
  it. But it can only succeed cleanly if the RUNNING process itself is not
  one of the holders — i.e. fire it from a fresh, non-holding process
  (cron, or after closing the desktop app), NOT from inside an active
  desktop-session chat.

**Safe completion paths:**
- **Option A (interactive):** close the Hermes desktop app + all other
  Hermes windows/terminals, then `hermes update --force-venv --yes`.
- **Option B (no disruption, RECOMMENDED if app is open):** schedule a cron
  job that runs `hermes update --backup --force-venv --yes` off-peak. The
  cron fires from a fresh Hermes process with no desktop backend holding
  `.pyd`, so the venv updates cleanly, then reboots. Set `deliver='all'`
  so the result reaches you (local-only cron output is NOT auto-delivered
  to a CLI/TUI session).

**Verify after upgrade (mandatory):**
```
hermes --version          # must advance past v0.20.0
hermes doctor             # must pass
```
A version string that did NOT change = the venv update did not land. Retry
with `--force-venv` from a clean process.

**Flags reference:**
- `--yes` / `-y`: skip interactive prompts (API-key entry skipped)
- `--backup`: force full pre-update zip of HERMES_HOME
- `--force`: bypass hermes.exe concurrent guard only (NOT venv)
- `--force-venv`: mutate venv despite holders (needs non-holding process)

## PITFALLS
- **web_search disabled** → symptom: `Error searching web: Web tools are not configured.
  Set FIRECRAWL_API_KEY...`. Fix: use `gh` CLI / `gh api` exclusively. This is the
  default in this Nous runtime.
- **`gh search commits` commitDate field** → symptom: `Unknown JSON field: "commitDate"`.
  Fix: drop it; read date from `commit.author.date` inside the `commit` object.
- **Partial upgrade from in-session `hermes update`** → symptom: exit 0, but
  `hermes --version` unchanged and gateway memory dropped (desktop backends
  restarted). Fix: the venv reinstall was skipped because the session holds
  `.pyd`. Complete via Option A or B above. Do NOT trust a bare exit-0.
- **`--force` is not enough** → symptom: assumed `--force` bypasses the
  venv lock; it does not. Fix: use `--force-venv` AND ensure the launching
  process isn't a `.pyd` holder.
- **SkillEvaluator scanning (v0.20.4+)** → symptom: warnings on skill installs post-update.
  Fix: know that 0.20.4 added NVIDIA SkillEvaluator Tier-1 advisory (license + security)
  scans; some of the ~150 local skills may flag. Not a failure — advisory only.

## VERIFICATION
- A skill use is correct when `gh api repos/<owner>/<repo>/releases` returns real tag rows
  and `hermes update --check` agrees with the installed vs latest comparison.
- CHECK phase is verified by real `gh` output + `hermes update --check`.
- PERFORM phase is verified ONLY by `hermes --version` advancing AND `hermes doctor` passing.
  If `gh` itself errors, run `gh auth status` and re-authenticate before retrying.

## REAL RUN (2026-08-20, AURORAL)
- Started: v0.20.0 (2026.8.3), 5 live Hermes.exe incl. 648 MB desktop host + auroral- session.
- `hermes update --backup --yes --force` → backup zip 599 MB in
  `~\AppData\Local\hermes/backups/pre-update-2026-08-21-001647.zip`, gateway
  restarted, BUT venv reinstall SKIPPED (holders: omnicore-base, omniprime,
  auroral- desktop backends + 2 adaptive-model-switcher workers). Version stayed v0.20.0.
- Resolution: scheduled cron `hermes-offpeak-upgrade` (job 2b57a01c6cf0) at
  03:00 daily with `hermes update --backup --force-venv --yes`, deliver='all'.

## REFERENCES
- Upstream: https://github.com/NousResearch/hermes-agent (releases/tags visible via gh api)
- Local skills dir (Win): C:\Users\jonny\AppData\Local\hermes\skills\
- Install dir (Win): C:\Users\jonny\AppData\Local\hermes\hermes-agent\
