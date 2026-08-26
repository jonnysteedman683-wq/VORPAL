# Local versus cloud project discovery

## Evidence tiers

- **Tier 1 — executable source:** tracked files, package manifests, entry points, tests, and live API routes.
- **Tier 2 — local runtime evidence:** running processes, workspace folders, generated build output, and local configuration.
- **Tier 3 — generated narrative:** agent reports, plans, scratch notes, conversation exports, and upgrade summaries.

Use Tier 1 to make implementation claims. Use Tier 2 to establish what is present on the machine. Use Tier 3 to reconstruct history and identify likely autonomous writers, but verify every important claim against executable source.

## Antigravity

On Windows, Antigravity may maintain local project/agent state beneath the user profile, separate from the actual project folder. Search both the known workspace root and the Antigravity state directory. Report the exact paths inspected. Avoid treating every UUID-named brain directory or report as a separate production project.

For an auto-upgrading project, inspect:

1. active project root and git status;
2. recent source modifications and generated artifacts;
3. agent definitions or automation configuration;
4. reports naming versions or upgrade phases;
5. process ownership and the write path when available.

Do not stop autonomous upgrading by deleting state or killing processes unless explicitly authorized. First preserve evidence and establish a reversible review path.

## Google AI Studio

Local access to an AI Studio export, API client, or generated code does not prove access to the user's cloud AI Studio dashboard. Cloud visibility requires an authenticated browser session or an explicit project/API integration. Never claim to see cloud projects merely because a local `.env`, Firebase config, Gemini client, or AI Studio-generated file exists.

A precise report should say one of:

- `local_export_found`: local code/artifacts are inspectable;
- `authenticated_dashboard_visible`: the cloud project list was actually viewed;
- `cloud_access_not_verified`: no authenticated dashboard or API project listing was checked.

## Reporting format

State:

1. what was actually visible;
2. exact local paths or live endpoints used as evidence;
3. what remains unverified;
4. the smallest next step to establish the missing boundary.

Avoid broad claims such as “I can see your projects” when only a local folder or generated report was found.
