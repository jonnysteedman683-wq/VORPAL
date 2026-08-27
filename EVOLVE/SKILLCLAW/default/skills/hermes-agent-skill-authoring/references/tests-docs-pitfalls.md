# Hermes skill authoring — tests, docs, and pitfalls

Load this file when you're at the point of **shipping** an in-repo
skill: adding its test, regenerating docs with scope discipline, and
avoiding the common review-blocking mistakes. The authoring
standards and body structure stay in `SKILL.md`.

## Tests and Docs (required for repo skills)

1. **Tests** live at `tests/skills/test_<skill>_skill.py` — stdlib + pytest + `unittest.mock` only, no live network. Run via `scripts/run_tests.sh tests/skills/test_<skill>_skill.py -q`. (The generic `tests/tools/test_skill_manager_tool.py` passing proves nothing about YOUR skill.)
2. **Docs regen:** run `python website/scripts/generate-skill-docs.py`, then apply scope discipline — the generator rewrites EVERY auto-gen page. `git checkout --` everything that isn't yours; the final diff must show only your SKILL.md, your one per-skill docs page, a one-line catalog row, and a one-line `website/sidebars.ts` insertion (verify with `search_files(pattern='<your-slug>', path='website/sidebars.ts')` — exactly one hit, or the page is an orphan).
3. **`.env.example`** (only if the skill needs new env vars): one clearly delimited commented block; touch nothing else in the file.

## Common Pitfalls

1. **Using `skill_manage(action='create')` for an in-repo skill.** It writes to `~/.hermes/skills/`, not the repo tree. Use `write_file`.
2. **Trusting the validator's limits as the standard.** The validator allows 1024-char descriptions; review rejects anything over 60. The validator doesn't check `platforms:`, author format, tests, or docs — review does.
3. **`author: Hermes Agent` on a contributed skill.** Credit the human first.
4. **Leading whitespace before `---`.** Validation fails on any leading blank line or BOM.
5. **Description too generic or trigger buried past char 57.**
6. **`related_skills` pointing at skills that don't exist in-repo** (user-local, planned, or in a sibling PR).
7. **Duplicating a peer.** Survey the category first; extend rather than sibling.
8. **Skipping the docs generator or pushing its unrelated drift.** Both directions are wrong: no regen = orphan skill with no docs page; blind regen = a ballooned diff full of other skills' drift.
9. **Expecting the current session to see the new skill.** The loader is initialized at session start.
10. **Letting skills accumulate sediment.** When adding a rule, remove the old wording it replaces.
