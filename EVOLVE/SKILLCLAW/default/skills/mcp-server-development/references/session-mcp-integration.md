# Verified Windows MCP integration notes

This reference records a reusable integration pattern from building a local adaptive model selector for Hermes on native Windows.

## Working sequence

1. Confirm the MCP SDK is available in Hermes's Python environment:

```bash
python -c "from mcp.server.fastmcp import FastMCP; print(FastMCP)"
```

2. Build and run offline unit tests before any Hermes registration. Standard-library `unittest` is sufficient when pytest is not installed.

3. Run a real stdio protocol smoke test using `mcp.ClientSession` and `stdio_client`. Assert initialization, tool names, a representative tool call, structured output, and clean shutdown.

4. Register with Hermes discovery-first:

```bash
printf 'Y\n' | hermes mcp add adaptive_router \
  --command python \
  --connect-timeout 10 \
  --args C:/absolute/path/to/adaptive_router.py
```

Use the actual server name and absolute path for other projects.

5. Verify:

```bash
hermes mcp list
hermes mcp test adaptive_router
hermes config get mcp_servers.adaptive_router --json
```

Expected evidence is `Connected`, the intended tool count, and a list-valued `args` field.

## Failure and recovery pattern

Hermes's generic `hermes config set` accepted a JSON-looking value for a nested MCP `args` key but persisted it as a scalar string. The MCP SDK then rejected it because `StdioServerParameters.args` requires a list. The durable fix was to remove/re-register the server with `hermes mcp add`, not to hand-edit YAML.

The discovery-first add flow also proved useful because it connected to the server, listed all tools, asked which tools to enable, and only then saved the configuration.

## Boundary-verification lesson

A successful `hermes mcp test` proves that Hermes can start the server and discover its tools. It does not prove that the server intercepts Hermes's internal model-dispatch path. Recommendation systems should return explicit metadata such as:

```json
{
  "dispatch_applied": false,
  "integration_status": "selector_only_mcp"
}
```

until native request-router behavior is separately demonstrated.

## Safety lessons

- Keep MCP stdout reserved for protocol traffic; send diagnostics to stderr.
- Use temporary state paths in protocol tests.
- Keep persistent state under the active Hermes home/profile.
- Do not store prompts, responses, credentials, or personal data in routing metrics.
- Start routing in recommendation or shadow mode and preserve a safe default and rollback mode.
- Do not send paid probes unless an explicit budget is configured; recording real outcomes is the safe baseline.
