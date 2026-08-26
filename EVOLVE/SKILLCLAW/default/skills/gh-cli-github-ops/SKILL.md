---
name: gh-cli-github-ops
description: "GitHub ops via gh CLI when web_search is dead: releases."
category: devops
version: 1.0.0
author: AURORAL
license: MIT
created: 2026-08-20
metadata:
  hermes:
    tags: [github, gh, cli, releases, search, devops]
    related_skills: [hermes-upgrade-check, hermes-agent]
---

# GitHub Ops via gh CLI

## When to Use
- `web_search` / `web_extract` are disabled (no Firecrawl credits in this Nous runtime)
- Need release notes, version deltas, commit history, PR status, or repo search
- Any GitHub lookup that would normally go through a web search

## STEP-BY-STEP

1. **Auth** (once): `gh auth status` → expect
   `✓ Logged in to github.com account jonnysteedman683-wq (keyring)`.
   If not, `gh auth login`.

2. **Release tags + notes**:
   ```
   gh api repos/<owner>/<repo>/releases --paginate \
     -q '.[] | "\(.tag_name)  \(.published_at)  \(.name)"'
   gh api repos/<owner>/<repo>/releases/tags/<TAG> --jq '.body'
   ```

3. **Commit history**:
   ```
   gh api repos/<owner>/<repo>/commits --paginate \
     -q '.[] | "\(.commit.author.date)  \(.commit.message | split("\n")[0])"'
   ```

4. **Search** (commits/repos/code/issues/PRs):
   ```
   gh search repos "hermes" --owner=NousResearch --limit 10 \
     --json name,url,updatedAt
   gh search commits "hermes upgrade" --owner=jonnysteedman683-wq --limit 10 \
     --json repository,sha,commit,url
   gh search prs --owner=<owner> --repo=<repo> "fix" --limit 10 --json title,url,state
   ```

5. **PR / issue inspection**:
   ```
   gh pr list --repo <owner>/<repo> --limit 10 --json number,title,state
   gh issue view <num> --repo <owner>/<repo>
   gh api repos/<owner>/<repo>/pulls --paginate -q '.[].title'
   ```

6. **Clone / inspect a repo locally** (when you need file contents):
   ```
   gh repo clone <owner>/<repo> /tmp/<repo> -- --depth 1
   ```

## PITFALLS
- **web_search disabled** → symptom: `Error searching web: Web tools are not configured.
  Set FIRECRAWL_API_KEY...`. Fix: route ALL GitHub lookups through `gh` CLI.
- **`gh search commits` commitDate field** → symptom: `Unknown JSON field: "commitDate"`.
  Fix: drop it; valid fields are `author, commit, committer, id, parents,
  repository, sha, url`. Read the date from `commit.author.date` inside `commit`.
- **Pagination limits** → `gh api` truncates without `--paginate`; large repos
  need it. `gh search` caps at `--limit` (max 100).
- **Wrong owner for search** → `gh search repos` with `--owner` scopes to that
  org/user; omit it for global search.

## VERIFICATION
- A `gh api repos/<owner>/<repo>/releases` call returning real tag rows confirms
  the repo path and auth are correct. If it 404s, check owner/repo spelling.
