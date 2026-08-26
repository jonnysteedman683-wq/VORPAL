---
name: mcp-server-development
description: "Use when building or integrating Hermes MCP servers."
version: 1.0.0
author: Jonny Steedman + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mcp, server, tools, stdio, integration, testing, hermes]
    related_skills: [hermes-agent, autonomous-coding-workflow]
---

# Hermes MCP Server Development

## Overview

Build reliable local Model Context Protocol servers that Hermes can discover and use as first-class tools. This skill covers server design, stdio protocol hygiene, safe configuration, discovery-first registration, offline testing, protocol smoke tests, and honest reporting of integration boundaries.

The target is a working MCP artifact backed by real tool discovery and tool-call output—not merely a Python module or configuration snippet.

## When to Use

Use when:

- Creating a local stdio MCP server for Hermes
- Exposing a selector, database, API, filesystem, or workflow as MCP tools
- Registering, testing, or troubleshooting Hermes MCP integrations
- Adding persistence, telemetry, or safe fallback behavior to an MCP server
- Verifying that discovered tools actually execute through the MCP protocol

Do not use this as a substitute for native Hermes changes when the server must intercept internal request dispatch. An MCP server can recommend or provide tools without automatically changing Hermes's own model-routing path.

## Core Rules

1. **Protocol-clean stdout:** MCP JSON-RPC owns stdout. Send diagnostics, warnings, and debug output to stderr or a redacted log.
2. **Fail safe:** invalid configuration, corrupt state, or router failure must return a safe result or explicit error—not drop the request or invent success.
3. **Separate policy and secrets:** keep model/provider policy in configuration and credentials in Hermes's supported credential system or `.env`; never log either unnecessarily.
4. **Use typed tool contracts:** arguments and return values must be deterministic, JSON-serializable, and documented in tool descriptions.
5. **Test the protocol boundary:** importing the server is insufficient; initialize an MCP client over stdio, list tools, call a representative tool, and inspect the structured result.
6. **Keep integration claims precise:** tool discovery proves MCP connectivity, not that Hermes's internal dispatch has been replaced.
7. **Use supported Hermes registration:** prefer `hermes mcp add` for discovery-first setup. Avoid hand-editing `config.yaml`.

## Implementation Workflow

### 1. Define the contract

List each tool with required arguments, defaults, return schema, side effects, privacy constraints, and failure behavior. Keep tools narrow enough that a caller can predict what will happen.

For a routing or recommendation service, return the candidate identity, score, estimated cost, constraints, reason, mode, and integration status. Include a safe default or fallback when no candidate qualifies.

**Done when:** every tool has a stable name, typed inputs, a documented JSON result, and a failure policy.

### 2. Implement the server

For Python servers using the installed MCP SDK:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def health() -> dict:
    return {"ok": True}

if __name__ == "__main__":
    mcp.run()
```

Do not print banners or logging to stdout. Use `print(..., file=sys.stderr)` for diagnostics. Resolve configuration from explicit arguments or environment variables, and use an active-profile-aware state path such as `$HERMES_HOME/<server>/state.json`.

**Done when:** the server starts under the intended interpreter and its stdout remains protocol-clean.

### 3. Add bounded persistence

Use SQLite transactions or atomic JSON replacement. Persist only metadata needed for the workflow. Bound rolling history, include schema/version fields, and recover to a safe baseline after malformed state.

Never persist prompts, full responses, API keys, bearer tokens, or personal data unless the user explicitly requires it and the storage policy supports it.

**Done when:** state survives restart, remains bounded, and corrupt state produces a safe recovery path.

### 4. Build offline tests first

Test pure logic without credentials or network calls:

- Empty state and safe defaults
- Validation and hard constraints
- Cost or quota arithmetic
- Capability and context filtering
- Failure categorization and fallback
- Persistence and restart behavior
- Deterministic tie-breaking
- Disabled/shadow modes and rollback

Use the repository's available test runner; Python's standard `unittest` is a dependable fallback when pytest is unavailable.

**Done when:** tests exercise both normal and failure paths with no external side effects.

### 5. Test the MCP protocol

Use `mcp.ClientSession` and `stdio_client` to launch the server with a temporary state path. Verify initialization, expected tool names, one representative call, structured output, and clean shutdown.

A minimal shape is:

```python
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        result = await session.call_tool("health", {})
        assert not result.isError
```

**Done when:** the client discovers all intended tools and a real call returns the expected structured data.

### 6. Register through Hermes

Use discovery-first registration:

```bash
hermes mcp add my_server \
  --command python \
  --connect-timeout 10 \
  --args C:/absolute/path/to/server.py
```

When prompted to enable tools, explicitly select `Y` for all or choose the required subset. Then verify:

```bash
hermes mcp list
hermes mcp test my_server
hermes config get mcp_servers.my_server --json
```

The persisted `args` value must be a YAML list, not a string containing JSON text. If it is a string, Hermes's MCP client rejects it because `StdioServerParameters.args` requires a list. Re-register with `hermes mcp add` rather than manually repairing YAML.

**Done when:** Hermes reports the server enabled, connects successfully, and discovers the expected tool count.

### 7. Verify the actual boundary

Separate these claims:

- **Server import passed:** Python can import the module.
- **Protocol passed:** an MCP client initialized, listed tools, and called one.
- **Hermes integration passed:** `hermes mcp test` connected and discovered tools.
- **Internal dispatch changed:** only claim this with evidence from the Hermes request path.

For recommendation systems, include explicit fields such as `dispatch_applied: false` and `integration_status: selector_only_mcp` until a native request-router hook is verified.

**Done when:** the final report states exactly which boundary was tested and what remains outside the integration.

## Safe Configuration Patterns

Keep server runtime configuration separate from Hermes registration. Use an absolute script path for Windows registration and keep model IDs, price metadata, capabilities, and safe defaults in a dedicated server config. Do not put API keys in that file.

For paid providers, do not send probes by default. Require an explicit budget before any network probe and prefer recording real request outcomes. Unknown prices should be excluded under strict budgeting or surfaced with a warning.

## Common Pitfalls

1. **Printing logs to stdout:** corrupts MCP JSON-RPC. Send logs to stderr.
2. **Testing only by importing:** import success does not prove MCP transport correctness.
3. **Using `hermes config set` for nested list values:** on this Hermes build, list-shaped MCP `args` can be persisted as a scalar string; use `hermes mcp add` and verify the type. Always run `hermes config get mcp_servers.<name> --json` after registration. If `args` is a string instead of a list, delete and re-add with `hermes mcp remove` + `hermes mcp add`.

   **Verification pattern (always do this):**
   ```bash
   hermes mcp list          # server should show as enabled
   hermes mcp test <name>   # must report "Connected" + tool count
   hermes config get mcp_servers.<name> --json | grep args  # type must be list
   ```
   A server listed as "enabled" without a successful `hermes mcp test` proves nothing — tools cannot be discovered until the MCP transport initializes successfully.
4. **Skipping discovery-first registration:** a server can be configured but unusable; let Hermes list tools before saving.
5. **Claiming automatic model switching from an MCP selector:** tool availability is not a request interceptor.
6. **Unbounded metrics:** cap history and use atomic writes or transactions.
7. **Paid health checks by default:** no-cost baseline should record real outcomes instead.
8. **Persisting sensitive content:** keep telemetry to redacted routing metadata.
9. **No rollback:** provide disabled mode, safe default, and explicit fallback.
10. **Not testing after registration:** run both the standalone protocol test and `hermes mcp test`.

## Verification Checklist

- [ ] Tool names and typed contracts are defined
- [ ] Server starts with the intended interpreter
- [ ] stdout is protocol-clean
- [ ] Diagnostics go to stderr or redacted logs
- [ ] State is bounded, versioned, and atomically persisted
- [ ] Secrets, prompts, and responses are not stored in telemetry
- [ ] Offline tests cover constraints, failures, persistence, and rollback
- [ ] MCP client smoke test lists tools and calls a real tool
- [ ] Hermes registration used `hermes mcp add`
- `mcp_servers.<name>.args` is a list, not a JSON string (verify via `hermes config get`)
- `hermes mcp test <name>` connects successfully and reports tool count
- [ ] `hermes mcp test <name>` succeeds
- [ ] Final report distinguishes tool integration from internal Hermes dispatch

## References

- `references/session-mcp-integration.md` — verified Windows discovery, registration, typed-args failure, and recovery sequence.
