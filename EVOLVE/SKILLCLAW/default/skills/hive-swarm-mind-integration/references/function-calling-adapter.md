# Function-Calling Adapter Reference

## Adapter File

- Path: `C:\Users\jonny\OneDrive\Documents\AEGIS\neurocore\adapters\function-call-adapter.ts`
- Module class: `FunctionCallAdapter`
- Registration methods:
  - `registerTool(name, schema, handler)`
  - `unregisterTool(name)`
- Dispatch method:
  - `callTool(name, args)` -> `{ ok, result, tool, latencyMs }`
- Introspection:
  - `listTools()` -> `ToolSchema[]`
  - `history` -> `FunctionCallResult[]`

## Built-in Tools

- `echo` -> echoes message back
- `system_status` -> returns `{ status: 'ok' }`

## Neurocore Bridge Loading

- Loaded via dynamic `import('file://' + path.join(NEUROCORE_ROOT, 'adapters', 'function-call-adapter.ts').replace(/\\/g, '/'))`
- Accessors on `neurocore-bridge.cjs`:
  - `getFunctionCallAdapter()`
  - `getFunctionCallAdapterAsync()`

## Server Routes

- `GET /api/neurocore/tools`
  - Calls `await neurocoreBridge.loadNeurocoreModules()` before accessor
  - Returns `{ success, connected, tools }`
- `POST /api/neurocore/tools/call`
  - Calls `await neurocoreBridge.loadNeurocoreModules()` before accessor
  - Body: `{ tool: string, arguments: object }`
  - Returns tool execution result or `503` if adapter unavailable

## Bridge Loading Behavior

- `getFunctionCallAdapter()` is synchronous and returns `null` until `_moduleCache` is populated.
- On the first request, `_moduleCache` may still be `null` unless the route explicitly awaits `loadNeurocoreModules()`.
- If the route does not await loading, the endpoint can return `function_call_adapter_unavailable` even though the module is present and loadable.

## Verified Behavior

- Neurocore tests: `5/5` pass via `npm run test`
- OMNIBUS tests: `41/41` pass via `npx tsx --test tests/*.test.ts`
- Adapter instantiated successfully in bridge: `tools [ 'echo', 'system_status' ]`
