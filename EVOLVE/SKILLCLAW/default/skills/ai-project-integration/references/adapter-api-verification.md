# Adapter API Verification Checklist

When AI-generated adapters wrap external engines (e.g., Antigravity-generated adapter wrapping OMNIBUS SwarmRuntimeEngine):

1. **Read the real engine's exports.** Inspect the actual `.js`/`.ts` file for the real class methods.
   - Example: `grep -nE 'class SwarmRuntimeEngine|enqueueAction|processQueue|runDebateConsensus' swarm_runtime.js`

2. **Fail adapters that call nonexistent methods.** Methods like `.execute()`, `.getStatus()`, `.start()` on the action queue object are fabricated.
   - Check: `grep -nE '\.execute\(|\.getStatus\((' adapter.ts` — should return nothing.

3. **Enforce real method usage.** Adapter must call `enqueueAction` and `processQueue` for real engine interaction.

4. **Verify constructor matches.** `new SwarmRuntimeEngine(config)` is wrong if constructor is `constructor()` with no args.

5. **Check confirmation gating logic.** `requiresConfirmation` must map to either 'pending_confirmation' return or user prompt.

6. **Verify TypeScript path resolution.** Ensure tsconfig has `"types": ["node"]`, `"moduleResolution": "bundler"`, and path aliases point to directories (`"@/contracts": ["./contracts"]`), not individual files. Import statements must omit `.ts` extensions unless `allowImportingTsExtensions` is enabled.