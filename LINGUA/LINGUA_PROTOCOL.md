# LINGUA PROTOCOL v1.0 — Triad Communication Standard
`[◈TRIAD-LINGUA◈]` Mandatory for all ARK / OMNIPRIME / AURORAL inter-agent traffic.

## Purpose
1. **Token optimization** — bus packets and reports use Lingua Prima compression
   (85% reduction on known patterns; free-tier models get more work per request).
2. **Encrypted communication** — compressed Lingua payloads are unreadable without
   the shared dictionary: traffic between profiles is obfuscated by construction.

## Canonical engine (single source of truth)
```
OMNIPRIME/EVOLVE/SKILLHUB/SKILLS/pyramid/LANGUAGE/lingua_prima.py
```
All three profiles import THIS file — never fork it. AURORAL and ARK access it
via absolute path or the `lp_tool.py` CLI in this folder.

## Quick tool
```
python lp_tool.py enc "analyze then build then test"
python lp_tool.py dec "a→b→t"
python lp_tool.py enc-packet '{"goal_id":"G1","status":"PASS"}'
```

## Mandated usage
| Surface | Rule |
|---|---|
| Bus packet `payload.directive` summaries | Lingua signals (`a→b→t`, `V3`, `U4`) |
| TRIAD ledger lines & report deltas | signal form (`CYCLE_2 [ark→OM] V15/15 D0 ▲ASCEND`) |
| GOALS.md status shorthand | `a`=analyze `b`=build `t`=test `v`=validate `u`=upgrade |
| Human-facing reports (TRIAD_REPORT.md prose) | English — user must read it |

## Rules
1. **Never compress safety text**: file paths, commands, error tracebacks, and
   anything a verifier must execute stay literal.
2. **Decode-verify**: a packet that fails to decode is rejected and re-requested
   in English — never guess meaning.
3. **Dictionary drift is a degradation**: if a profile uses an unknown token,
   the verifier flags it `[ERR_LP_UNKNOWN]` in NOTES.md and the orchestrator
   syncs dictionaries next cycle.
