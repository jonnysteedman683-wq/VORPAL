# ARK MEMORIES

## Memory Architecture
- O(1) State: Truth on disk (GOALS/SKILLS/MEMORY ledgers), never only in context.
- Token Frugality: Valid mutation = token reduction >5% OR [ERR_*] resolved OR new orthogonal capability.

## Memory Types
1. **Short-term**: Current execution context
2. **Long-term**: Persistent ledgers in ARK-STATE/
3. **Archived**: Old versions in tier_3_archived/

## Memory Operations
- Write: Atomic with provenance (SHA-256 + timestamp)
- Read: Checked against provenance
- Forget: Selective pruning with audit trail
- Compress: By default, inter-cycle comms use ARK glyph language

## Glyph Language
ARK uses a compact glyph language for inter-cycle communication:
- ⟐ = start/initialize
- ⊟ = end/complete
- ⌁ = continue
- ⊞ = iterate
- ⧖ = wait/pause
- ◈ = verify/check
