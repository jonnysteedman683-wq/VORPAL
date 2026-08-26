# Workspace vs Repository: verifying the real project root

A local folder named `Project` is not always the authoritative repository.
This is a recurrent trap when IDE-managed agents or git worktrees are in play.

## Red flags that a local folder is NOT authoritative

- `git status` shows **only deletions** of many files (worktree pointing elsewhere)
- Folder exists but `git ls-tree -r --name-only HEAD` returns nothing or unrelated paths
- `ls -la` shows an **empty** or nearly empty working directory
- Recent commit messages reference a different product name than the folder
- An IDE/agent owns writes (Antigravity, Cursor, etc.) — local working tree diverges from remote
- The folder is listed as a git **worktree** (`git worktree list`)

## Verification commands (run before editing)

```bash
git status --short --branch
git log --oneline -5
git ls-tree -r --name-only HEAD
git worktree list
stat <folder>                    # on Windows: Get-Item or dir
```

If the folder looks empty or stale, clone the remote fresh:

```bash
gh repo clone jonnysteadman683-wq/<REAL-REPO> /tmp/probe --depth 1
```

## Key lesson from session

Local `C:\Users\jonny\OneDrive\Documents\AEGIS\Sentinel` was an **empty worktree stub**.
The real Sentinel repo (125 React components, server.ts, tests) lives at
`github.com/jonnysteedman683-wq/Sentinel` and had to be `git clone`d to inspect.

Always verify with `git ls-tree -r --name-only HEAD` — not just `ls`.
