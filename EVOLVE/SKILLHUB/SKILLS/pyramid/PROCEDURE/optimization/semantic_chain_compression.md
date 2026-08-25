---
procedure_id: "semantic_chain_compression"
type: "optimization"
related_skills: ["lingua_prima", "token_compressor"]
last_executed: "2026-08-19T15:00:00Z"
---

# Procedure: Semantic Chain Compression
## Purpose
Compress multi-concept semantic chains into minimal Unicode representations.

## Algorithm
1. Parse input as sequence of concept tokens
2. Attempt compound merge (2-char → 1 token with 50% compression)
3. Attempt macro substitution (3-char → 1-2 chars with 66%+ compression)
4. Assign shortest available alias for repeated patterns
5. Measure and report compression ratio

## Common Chain Optimizations

| Chain | Compressed | Savings |
|---|---|---|
| `analyze then build` | `a→b` | 57% |
| `generate then test then validate` | `g→t→v` | 63% |
| `steal and steal and steal` | `sss` | 50% |
| `optimize all critical errors` | `o9E` | 60% |

## Hash-Based Alias Assignment
For any concept not in dictionary:
- Generate SHA256 hash
- Take first byte as alias
- Register in ephemeral alias table
- Next occurrence reuses same alias
