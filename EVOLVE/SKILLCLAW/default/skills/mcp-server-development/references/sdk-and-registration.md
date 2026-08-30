# SDK class, `--args` last, protocol result field

Condensed from Citadel MCP wiring (2026-08-28). Complements `session-mcp-integration.md`.

## Server class

Hermes venv `mcp` exposes `MCPServer`, not FastMCP:

```python
from mcp.server.mcpserver import MCPServer
mcp = MCPServer("citadel")
@mcp.tool()
def query_section(topic: str, section: str = "", limit: int = 10) -> dict: ...
mcp.run(transport="stdio")
```

Probe: `from mcp.server.mcpserver import MCPServer`. Only use FastMCP if that import fails.

Diagnostics: `print(..., file=sys.stderr)` only. Path insert via `os.path.abspath(__file__)`, not `Path.resolve()`.

## `hermes mcp add` flag order

`--args` is greedy (must be last). Wrong:

```bash
hermes mcp add citadel --command python --args C:/path/server.py --env CITADEL_VAULT_PATH=C:/vault
```

Persisted `args` as `[server.py, "--env", "CITADEL_VAULT_PATH=..."]`, `enabled: false`. First connect can fail; `hermes mcp test` may still work later.

Right:

```bash
printf 'Y\n' | hermes mcp add citadel \
  --command C:/Users/jonny/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe \
  --connect-timeout 25 \
  --env CITADEL_VAULT_PATH=C:/Users/jonny/OneDrive/Desktop/The-Citadel-Vault/The-Citadel-Vault \
  --args C:/Users/jonny/OneDrive/Desktop/The-Citadel-Vault/The-Citadel-Vault/scripts/citadel_mcp.py
```

If polluted: `hermes mcp remove <name>` then re-add. Confirm:

```bash
hermes config get mcp_servers.<name> --json
# args: list of script path only
# env: map
# enabled: true
hermes mcp test <name>   # Connected + tool count
```

New session required before `mcp_<name>_*` tools appear in chat.

## Protocol smoke test

`CallToolResult` uses `is_error` (not `isError`). Guard:

```python
def _is_error(result) -> bool:
    return bool(getattr(result, "is_error", False) or getattr(result, "isError", False))
```

Point tests at a temp vault via env (`CITADEL_VAULT_PATH`), not the live vault.

## Knowledge / vault MCPs

If the user rejected git auto-sync: expose query/read/write only. No `commit_knowledge`. Writes stamp domain provenance (watermark + receipt) in-process; git stays human-gated.
