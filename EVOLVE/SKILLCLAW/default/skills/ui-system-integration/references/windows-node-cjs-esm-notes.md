# Windows CommonJS/ESM Module Friction

## The Problem

Node.js on Windows running a **CommonJS server** (`server.cjs`) that needs to load an **ESM Neurocore package** hits this error:

```
[neurocore-bridge] Spike comm module not available: module is not defined in ES module scope
This file is being treated as an ES module because it has a '.js' file extension 
and 'C:\...\neurocore\package.json' contains "type": "module".
```

## Root Cause

- Neurocore's `package.json` declares `"type": "module"` (ESM-only)
- neurocore-bridge was originally `.js` (treated as ESM in that context)
- Server.cjs tries `require()` it → CommonJS attempting to require ESM module → `module` not in scope

## Solution

**Rename to `.cjs` extension.** The `.cjs` extension overrides `"type": "module"` and forces CommonJS parsing.

**neurocore-bridge.cjs** is now the entry point.

## Require Path Fix

**Don't use hardcoded Windows paths:**
```javascript
// ❌ BREAKS on new machines / different OneDrive paths
const neurocoreBridge = require('C:/Users/jonny/OneDrive/Documents/AEGIS/neurocore/neurocore-bridge.cjs');

// ✅ WORKS everywhere
const neurocoreBridge = require(path.resolve(__dirname, '../../../Documents/AEGIS/neurocore/neurocore-bridge.cjs'));
```

Always use `path.resolve(__dirname, '...')` with forward slashes.

## Verification

Before backgrounding server after a bridge change:

```bash
node --check server.cjs
# Should print: (nothing, exit 0)
```

## Cross-Module Communication Pattern

When CommonJS server needs to call ESM modules dynamically:

1. **Bridge module (`.cjs`)** does the `require()`
2. **Bridge module** uses `import()` internally to load ESM (await-wrapped)
3. **Bridge exposes sync/async getters** that server.cjs can call
4. **Server calls bridges's exported functions**, not ESM modules directly

neurocore-bridge.cjs follows this pattern: it safely wraps ESM imports and re-exports for CommonJS use.
