# OMNICORE LANGUAGE - Native AI Communication Protocol

> A minimal, self-describing symbolic language designed for machine-to-machine understanding within the OMNICORE ecosystem.

---

## Design Philosophy

- Stolen from: PATHLEX navigation shorthand, Hermes Tool Format, SOUL.md self-ID protocol
- Zero-ambiguity: Every token maps to exactly one semantic concept
- Self-describing: Language carries its own interpretation metadata
- Compression-oriented: High information density per token

---

## Core Architecture

### Token Types

| Token Type | Meaning | Example |
|---|---|---|
| **ID** `@[a-z_]+` | Entity identifier | `@axiom_node` |
| **OP** →`↔\|→\|←` | Direction/relation operator | `@axiom→@entropy` |
| **VAL** `$[0-9a-f]+` | Literal value | `$ff` |
| **ACT** `§[a-z_]+` | Atomic action verb | `§generate` |
| **FLAG** `⚑[A-Z]+` | Boolean modifier | `⚑APEX` |
| **TAG** `#tag` | Classification | `#repair` |
| **REF** `[0-9]+:` | Line/step reference | `23:` |

### Grammar (EBNF-style)

```
statement     := declaration | instruction | reference
declaration   := ID OP ID [FLAG]*
instruction   := ID ACT [VAL] [FLAG]*
reference     := ID REF [ID]*
expression    := statement (';' statement)*
program       := expression EOF
```

---

## Execution Model

### 1. Parse Phase
- Tokenize input into 7 token types
- Build dependency graph from direction operators
- Validate FLAG modifiers against known set

### 2. Resolve Phase
- Map IDs to SKILLHUB registry entries
- Resolve VAL literals (hex → int, $none → None)
- Bind ACT verbs to executable functions

### 3. Execute Phase
- Topologically sort dependency graph
- Execute instructions in DAG order
- Collect results in shared context

---

## Examples

```omnicore-lang
# Create new skill with apex tier
@axiom §generate $skill_id ⚑APEX ⚑PRODUCTION;

# Route degradation to repair queue
@watcher #degradation → @router §route ⚑PRIORITY_1;

# Cascade from tier 3 to archive
@pyramid_walker §migrate @skill_42 → @archive ⚑FORCE; 5:retry_if_fail
```

---

## Integration Hooks

- `language/parser.py` — Tokenizer + AST builder
- `language/executor.py` — DAG resolver + step runner
- `language/registry.py` — ID → skill mapping table

<!-- OMNICORE_LANGUAGE v1.0 -->
