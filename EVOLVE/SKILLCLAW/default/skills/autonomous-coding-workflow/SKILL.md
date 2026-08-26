---
name: autonomous-coding-workflow
description: "Use for autonomous coding: inspect, build, test, commit."
version: 1.0.0
author: Jonny Steedman + Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [coding, implementation, testing, debugging, git, autonomous]
    related_skills: [github-auth, github-repo-management, plan, spike]
---

# Autonomous Coding Workflow

## Overview

Use this skill for software changes where the desired outcome is clear enough to execute without turning the interaction into a planning exercise. The goal is a verified working artifact, not a description, stub, or untested patch.

Favor momentum and concrete progress: inspect the existing project, make the smallest coherent implementation, exercise it, fix failures, review the diff, and leave the repository in a clean, understandable state.

## When to Use

Use for:

- Implementing a feature or subsystem
- Fixing a bug or crash
- Refactoring an existing codebase
- Upgrading a prototype into a usable tool
- Adding tests, validation, configuration, or documentation alongside code
- Multi-file changes that require iterative execution

Do not use as a substitute for clarification when requirements materially conflict, when the requested behavior is unsafe or destructive, or when access to a required external system is missing.

## Operating Rules

1. **Act on the obvious interpretation.** Ask only when ambiguity changes the implementation or could cause meaningful harm.
2. **Inspect before editing.** Identify the project root, repository state, instructions, entry points, dependencies, tests, and existing architecture.
3. **Preserve working behavior.** Prefer targeted changes over broad rewrites unless the existing structure blocks the requested result.
4. **Finish the loop.** Every implementation must be executed or tested before being reported complete.
5. **Use real output.** Never invent test results, file contents, API responses, or completion claims.
6. **Fix forward.** When a test or run fails, diagnose the root cause, patch it, and rerun the relevant checks.
7. **Keep user control.** Do not delete repositories, rewrite history, publish releases, deploy, send messages, or modify production systems without explicit authorization.
8. **Do not auto-launch interactive applications** unless the user explicitly asks; use headless validation where possible.
9. **Commit completed work by default** when operating in a Git repository, unless the user says not to commit or the repository has uncommitted user work that would be mixed into the commit.

## Workflow

### 1. Establish scope and constraints

Translate the request into a short acceptance checklist. Record assumptions only when they affect implementation. Identify whether the task is a feature, bug fix, refactor, or investigation.

**Done when:** the requested outcome and verification conditions can be stated in concrete terms.

### 2. Discover the project

Inspect the current directory and repository without changing files:

```bash
pwd
git status --short --branch
```

Find the relevant source, tests, package metadata, and project instructions. Read `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.hermes.md`, and README files when present. Check the current diff before touching anything.

Separate pre-existing user changes from changes made during this task. Do not overwrite unrelated work.

**Done when:** the project entry points, relevant files, test commands, and local rules are known.

### 3. Choose the smallest viable design

Use the existing conventions, APIs, naming, and dependency choices. For uncertain or high-risk behavior, make a small spike or focused experiment before integrating it. Avoid speculative abstractions and unnecessary dependencies.

For larger requests, maintain a compact checklist rather than producing a plan-only response. Break work into independently verifiable slices.

**Done when:** each slice has a clear implementation target and a check that can prove it works.

### 4. Implement in coherent slices

Edit files deliberately. Keep changes focused and preserve compatibility with existing data, configuration, and public interfaces unless a breaking change is explicitly requested.

Add or update tests for new behavior and regression cases. Update documentation or examples when the user-facing behavior changes. For simulations and games, prioritize performance, save compatibility, and headless checks; do not rely on visual launch as the only validation.

**Done when:** the requested behavior exists in the source and the changed paths are accounted for.

### 5. Run fast checks immediately

Start with cheap checks that catch syntax and import errors, then run focused tests, then the broader suite:

- Syntax/type/lint checks appropriate to the project
- Unit tests for changed behavior
- Integration or smoke tests for affected boundaries
- Build/package checks when applicable

On Jonny's Windows environment, use `python` rather than `python3` for the Python 3.11 project toolchain. Avoid launching Pygame or other interactive apps during verification unless explicitly requested.

**Done when:** relevant checks have actually run and their output is captured.

### 6. Debug failures systematically

For each failure:

1. Read the complete error and identify the first meaningful failure.
2. Trace it to the smallest responsible code path.
3. Patch the root cause rather than masking the symptom.
4. Rerun the failed check.
5. Rerun nearby regression tests.

Do not disable tests, weaken assertions, swallow exceptions, or report a workaround as a fix unless that trade-off is explicit.

**Done when:** failures are fixed, intentionally accepted with an explanation, or reported as a genuine blocker with evidence.

### 7. Review the result

Inspect the final diff and status:

```bash
git diff --check
git diff --stat
git status --short
```

Check for accidental files, debug prints, secrets, temporary artifacts, unrelated edits, stale comments, missing tests, and API inconsistencies. Verify that every acceptance item is satisfied.

**Done when:** the diff contains only intentional changes and the working tree state is understood.

### 8. Commit the verified change

If the repository is suitable and no unrelated user changes are included, create a focused commit with a descriptive message:

```bash
git add <intentional-files>
git commit -m "< concise imperative summary >"
```

Never stage the entire repository blindly when unrelated changes exist. If a commit cannot be made, report why and provide the exact remaining status.

**Done when:** the commit succeeds and `git status --short --branch` confirms the resulting state.

### 9. Report with evidence

Give a concise completion report containing:

- What changed
- Files or subsystems affected
- Checks actually run and their results
- Commit hash and message, if committed
- Any assumptions, limitations, or follow-up items

If blocked, state the blocker, the command or output proving it, and the smallest next action needed. Do not conceal incomplete work behind optimistic wording.

## Special Cases

### Existing uncommitted changes

Do not reset, stash, or overwrite user work automatically. Identify the baseline diff, edit only the requested paths, and stage files selectively. If separation is impossible, stop before committing and explain the conflict.

### Missing tests

Add a focused smoke or regression test when practical. If the project has no test harness, run the narrowest executable validation available and state the limitation.

### Dependency changes

Prefer existing dependencies. Before adding one, confirm it is necessary, update the appropriate lock or requirements file, install or resolve it, and run the affected checks.

### GUI, game, and simulation projects

Validate logic headlessly where possible. Check initialization, save/load compatibility, dimensions and action counts, performance-sensitive loops, and clean shutdown. Never claim visual correctness without actually inspecting the UI when visual output is part of acceptance.

### GitHub operations

Local implementation and verification come first. Push, open pull requests, modify issues, or publish artifacts only when explicitly requested. Authentication status alone is not authorization to perform remote writes.

## Common Pitfalls

1. **Stopping after writing code:** run it and verify the requested behavior.
2. **Editing before inspecting:** read project rules, status, and relevant files first.
3. **Using a giant rewrite for a narrow fix:** preserve architecture and reduce regression surface.
4. **Mixing unrelated user changes into a commit:** stage only intentional paths.
5. **Treating a passing syntax check as completion:** run behavior-focused tests or smoke checks.
6. **Masking a failure:** fix the root cause and retain meaningful assertions.
7. **Launching interactive software unnecessarily:** prefer headless validation and respect the no-auto-launch preference.
8. **Claiming GitHub work from local authentication:** login proves capability, not permission or completion.
9. **Leaving temporary artifacts behind:** inspect status and the final diff before reporting.
10. **Windows path translation in Bash:** use the native Windows `workdir` for npm/Bun commands; `/c/...` can be misread as `C:\c\...`. Remove generated `tsconfig.tsbuildinfo` before committing.
10. **Treating a no-candidate cron exit as a completed verification:** independently confirm the expected remote ref pattern with `git ls-remote --heads origin 'refs/heads/<pattern>*'`; report test/type/safety checks as not run when the script exits before them.
11. **Leaving tracked credentials or runtime artifacts behind:** scan tracked text for credential patterns, remove local env files from Git, and ignore database journals/runtime state before committing.
12. **Using protocol bytes as socket health probes:** use a non-consuming `MSG_PEEK` probe; never inject sentinel bytes into a live application protocol.

## Verification Checklist

- [ ] Request translated into concrete acceptance criteria
- [ ] Project instructions and repository state inspected
- [ ] Existing user changes preserved
- [ ] Relevant implementation and tests updated
- [ ] Fast checks, focused tests, and broader checks run as applicable
- [ ] Failures fixed or reported with evidence
- [ ] `git diff --check` passes
- [ ] Final diff contains only intentional changes
- [ ] No secrets or temporary artifacts added
- [ ] Commit created when authorized and safe
- [ ] Final report includes real commands/results and any limitations
