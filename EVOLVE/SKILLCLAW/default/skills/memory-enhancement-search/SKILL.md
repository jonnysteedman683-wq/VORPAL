---
name: memory-enhancement-search
description: Research memory provider upgrades for AI agents.
version: 1.0.0
author: Jonny Steedman
license: MIT
tags:
  - memory
  - research
  - agent-capabilities
  - skills-ecosystem
metadata:
  hermes:
    tags: [memory, research, agent-capabilities]
    related_skills: [hermes-agent, skillclaw-integration, autonomous-coding-workflow]
---

# Memory Enhancement Search

## Trigger
When asked to investigate how agent memory systems can be upgraded or when researching compatible memory providers.

## Behavior

### 1. Multi-source Research Pipeline
```
web_search → web_extract → github_search → skill_view
```
- Always check: Hermes docs, Supermemory docs, Agent Skills spec (agentskills.io), VoltAgent awesome-agent-skills, HermesAtlas top-skills.
- Compare approaches: memory-as-layer (Mem0/Supermemory), self-improving agent (Hermes), vector store, hybrid.

### 2. Evaluation Criteria
- **Interoperability:** Does it support the agentskills.io open standard?
- **Token efficiency:** Does it use lazy loading or progressive disclosure?
- **Security:** Injected memory scan for prompt injection? Credential filtering?
- **Recency:** Last update date, issue response time.
- **Ecosystem fit:** Stars, forks, community integration with Claude/Codex/Cursor.

### 3. GitHub Search Patterns
- `repo:NousResearch/hermes-agent` — official bundled skills
- `repo:VoltAgent/awesome-agent-skills` — curated community collection
- `topic:claude-skills OR topic:codex-skills` — cross-platform compatibility
- `topic:agent-skills` — any standard-compliant skill

### 4. Signal Detection
Watch for these first-class signals during research:
- User frustrated by verbosity: record in `references/style-notes.md`
- Tool failure with retry pattern: store full transcript in `references/failure-patterns.md`
- New discovery after failed attempt: capture workaround (NOT the failure)
- Cross-session insight: may need memory provider vs skill

## Pattern Proved
Multi-modal research (web + GitHub + docs) surfaces both official bundled skills AND external registry content that can be installed via `hermes skills tap add` + `hermes skills install`.

## Skill Mutation
This skill will be updated as new memory providers are discovered and evaluated.

## Verification Checklist
- [ ] Research covers docs, GitHub repos, and skill registries
- [ ] Cross-platform compatibility noted
- [ ] Security considerations documented
- [ ] Concrete install commands provided for each discovered provider