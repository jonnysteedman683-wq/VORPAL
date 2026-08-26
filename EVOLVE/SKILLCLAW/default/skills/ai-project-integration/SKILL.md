---
name: ai-project-integration
description: "Use when integrating AI projects with Hermes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [integration, ai-projects, neural-interface, swarm, antigravity, ai-studio, discovery, audit]
    related_skills: [agent-orchestration, autonomous-coding-workflow, mcp-server-development]
---

# AI Project Integration and Boundary Audit

## Overview

Use this skill when Hermes must work with an existing AI application, IDE-managed project, autonomous coding agent, neural-interface prototype, or swarm runtime. The goal is to establish a verified integration boundary before changing production code.

This skill prevents a common category error: seeing local project files or agent-generated reports does not prove that Hermes can control the application, and application control does not prove access to neural hardware or physical actuation.

## Core Model: Three Separate Claims

Always distinguish these claims:

1. **Local project access** — source files, generated reports, workspace metadata, logs, and runtime processes can be inspected on the host.
2. **Application control** — Hermes can call a documented HTTP, IPC, MCP, CLI, or other control boundary exposed by the application.
3. **Hardware/neural control** — a reviewed EEG/BCI/device adapter exposes typed signals and, if applicable, bounded actuation controls.

Never infer a higher claim from a lower one. Report the exact verified boundary using explicit status fields such as `local_files_only`, `app_control_plane_only`, or `hardware_adapter_verified`.

## Discovery Workflow

1. **Identify the real project root.** Search likely workspace locations, then inspect package metadata, README files, project instructions, git status, and entry points. Do not assume the current chat directory is the production project.
2. **Separate source from generated artifacts.** IDE/agent folders, reports, plans, scratch files, conversation logs, and upgrade notes are useful evidence about prior work, but they are not authoritative implementation. Prefer tracked source and runtime configuration.
3. **Find the control boundary.** Inventory API routes, IPC handlers, MCP servers, CLI entry points, WebSocket channels, queues, and device adapters. Record methods, payload schemas, authentication, side effects, and failure behavior.
4. **Audit autonomous writers.** If a project is auto-upgrading, identify which process or agent writes files, whether writes are committed, what paths are affected, and how to review or roll back changes. Never silently overwrite unrelated user changes.
5. **Map the swarm.** Record agent roles, task lifecycle, state storage, communication path, concurrency, model/provider calls, and whether pause, resume, cancellation, and audit events exist.
6. **Map the neural/device layer separately.** Look for explicit EEG/BCI/serial/BLE/USB/device SDK integrations and typed signal schemas. Absence of an adapter must be reported as an absence, not filled with assumptions.

## Hermes Integration Pattern

Prefer a narrow typed control plane over direct edits to a monolithic application:

- Read-only health, capability, and status operations are separate from mutating operations.
- Swarm deployment is explicit and confirmation-gated when it can cause multiple model calls, provider costs, code changes, or external actuation.
- Tool results are deterministic JSON with `ok`, `integration_status`, operation identifiers, current state, and structured errors.
- Bound task size, polling time, collection history, and response payloads.
- Keep secrets in the supported credential store or `.env`; do not place credentials in project reports, generated prompts, or telemetry.
- Keep raw biosignals out of prompts by default; expose derived, minimized features unless raw data is explicitly required.
- Add disconnect, timeout, safe-stop, and rollback states before enabling hardware actuation.

## Verification Levels

Do not claim completion from import success or file presence alone. Verify progressively:

1. Source/module import or syntax check.
2. Pure-logic tests for validation, confirmation gates, bounded polling, and failure handling.
3. Protocol smoke test: initialize the MCP/IPC/HTTP boundary, enumerate operations, and call a representative read-only operation.
4. Application integration test: call the real local endpoint and inspect structured output.
5. Hardware test only with the actual adapter, explicit authorization, safe limits, disconnect handling, and an emergency-stop path.

The final report must state which level passed and which boundary remains unverified.

## Autonomous Upgrade Safety

When another agent is upgrading the project automatically:

- Inspect current git status and the existing diff before editing.
- Treat uncommitted changes as user-owned until proven otherwise.
- Do not stage or commit unrelated changes.
- Record generated upgrade artifacts separately from production source.
- Prefer additive, modular integration points and reversible changes.
- Do not declare that the system is self-improving or production-ready merely because versioned reports exist; verify executable behavior.

## Bridge Patterns

### ESM TypeScript → CommonJS `require()` bridge

When integrating an ESM TypeScript module (e.g. Neurocore `lib/*.ts`) into a
CommonJS server (`server.js` using `require()`), use a dedicated bridge file:

```js
// bridge.cjs
async function loadModules() {
  // Windows: node's ESM loader needs file:// URLs
  // Linux/macOS: plain paths work too, but file:// is portable
  const url = process.platform === 'win32'
    ? 'file://' + path.replace(/\\/g, '/')
    : path;
  const mod = await import(url);
  return mod;
}

module.exports = { loadModules, isAvailable };
```

**Key rules:**
- Use a single bridge file — never scatter `import()` calls across the server.
- Cache the dynamic import result to avoid module re-evaluation.
- Test the bridge in isolation before wiring endpoints.
- On Windows, the `file://` prefix is mandatory for any `import()` of a local
  path — omitting it throws `Received protocol 'c:'`.

### Verifying adapter APIs against real engine exports

**Pitfall:** Generated adapter code calls methods that don't exist on the target.
For example, an adapter calling `.execute()` or `.getStatus()` on
`SwarmRuntimeEngine` is wrong because the real engine uses `enqueueAction()`
and `processQueue()`.

**Rule:** Before wiring an adapter, read the real exported interface:

```js
// Check what's actually exported
const realModule = require('./real-swarm.ts');
console.log(Object.getOwnPropertyNames(realModule.SwarmRuntimeEngine.prototype));
// → ['constructor', 'enqueueAction', 'processQueue', ...]
```

Cross-reference every adapter method call against the real prototype. Flag any
call not present as an integration error.

---

## Common Pitfalls

1. **Confusing local visibility with cloud access:** local Antigravity or workspace artifacts do not imply access to a Google AI Studio account or cloud dashboard.
2. **Confusing a swarm UI with swarm control:** a visualizer may only start and poll tasks; inspect the actual server route and side effects.
3. **Confusing app control with neural control:** an HTTP endpoint for an AI app is not an EEG/BCI interface.
4. **Treating generated reports as source of truth:** reports can be stale, speculative, or produced by a different workspace revision.
5. **Triggering expensive work during discovery:** use read-only health/capability calls first; gate swarm starts and paid probes.
6. **Claiming internal Hermes dispatch replacement from MCP discovery:** MCP proves tool availability, not interception of Hermes's own model-routing path.
7. **Launching interactive software unnecessarily:** prefer headless inspection and protocol tests unless visual validation is required.
8. **Confusing workspace folders with real project repositories:** a local folder that appears empty, is a git worktree stub, or is managed by an external IDE/agent is not authoritative. Always inspect the remote repository (e.g. via `gh` or full clone) to find the real source of truth. A folder named `Project` in the filesystem may not match the GitHub repo of the same name.

9. **Verifying adapter outputs against actual engine APIs:** generated adapter code must be checked against the real underlying engine's exported methods. For example, a generated adapter calling `.execute()` or `.getStatus()` on `SwarmRuntimeEngine` is wrong because the real engine uses `enqueueAction()` and `processQueue()`. Always verify adapters call real methods, not invented ones. See `references/adapter-api-verification.md`.
10. **Failing to separate cron/automation boundaries:** when Antigravity runs as a cron agent, distinguish its local filesystem mutations from cloud-managed entities like AI Studio. A cron job modifying local files does NOT imply cloud integration — cron agents operate only on local filesystems they have write access to.

## References

- `references/antigravity-ai-studio-discovery.md` — practical local-vs-cloud discovery notes and evidence handling for IDE agents and AI Studio projects.

## Verification Checklist

- [ ] Project root and active revision identified
- [ ] Source, generated artifacts, and user changes separated
- [ ] Control boundary and side effects documented
- [ ] Swarm roles, lifecycle, and cancellation behavior checked
- [ ] Neural/device adapter independently verified or explicitly absent
- [ ] Read-only health/capability operation tested
- [ ] Mutating operations confirmation-gated
- [ ] Secrets and raw biosignals handled safely
- [ ] Final report states the exact integration boundary proven

See `references/neurocore-integration-bridge.md` for a verified ESM/CJS bridge
pattern and working server endpoints used in the Hive Swarm Mind integration.
