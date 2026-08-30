# Axiom Vault Architecture Comparison

## Your Axiom Vault (Citadel) vs. Alternative Architectures

### 1. Memory Layer Comparison

| Architecture | Storage | Query | Governance | Token Cost |
|--------------|---------|-------|------------|------------|
| **Your Citadel (Axiom)** | Markdown + SQLite | Regex/token search | Watermark + receipts | 72% reducible |
| **Mem0** | Vector + Graph | Embedding search | Auto-extraction | 90% reducible |
| **Zep** | Message DB | Semantic | Log-based | Session-bound |
| **Letta** | Block memory | Tool calls | Self-edit | Explicit control |

### 2. Key Differences

#### Your Citadel Advantages
1. **Version-controlled**: Git history provides rollback/audit
2. **Watermark provenance**: Every note has `HR-YYYYMMDD-NNN` receipt
3. **Section governance**: `ALLOWED_WRITE_SECTIONS` = {Memory, Decisions, Goals, Tasks, Reports}
4. **No vendor lock-in**: Pure markdown files, portable
5. **Cost-effective**: 0.005$/1M tokens for storage (local SQLite)

#### Mem0 Advantages
1. **Entity relationships**: Explicit graph edges between facts
2. **Auto-extraction**: LLM extracts facts during writes
3. **Multi-tenant scope**: user_id, session_id, agent_id, app_id
4. **Hybrid retrieval**: Vector + graph queries

#### Zep Advantages
1. **Temporal tracking**: Facts have timestamps, can reason over change
2. **Auto-summarization**: Session logs compressed automatically
3. **Session continuity**: Chat history never lost

#### Letta Advantages
1. **White-box memory**: Agents can inspect/edit their own memory
2. **Self-healing**: Agents update stale facts autonomously
3. **Complete runtime**: Not just memory, full agent framework

### 3. Upgrade Points for Your Axiom Vault

#### Immediate (0-3 months)
```python
# 1. Add token budgeting to search results
# citadel_recall.py already limits to 10-50 hits
# Add: budget=500 tokens for context injection

# 2. Implement hierarchical summaries
# Current: flat notes in Memory/
# Upgrade: summary.md at top of each folder

# 3. Add Jaccard deduplication
# citadel_recall.py uses token overlap scoring
# Upgrade: track similar notes, merge when >80% overlap
```

#### Medium-term (3-6 months)
```python
# 4. Temporal knowledge graph layer
# Add: timestamp edges between related notes
# Structure: {note_a} --(mentions)--> {note_b}

# 5. Auto-extraction pipeline
# Scan new notes -> extract entities -> create links
# Tool: spaCy NER + custom entity types (goals, decisions, etc.)

# 6. Ebbinghaus decay scoring
# Score = base_relevance * (1 - age_days/30) * access_frequency
# Low-score notes moved to Archives/
```

#### Long-term (6-12 months)
```python
# 7. Distributed shard layer
# Split vault by domain: Protocols/, Goals/, Memory/
# Each shard has its own index + query router

# 8. Selective sync protocol
# Only sync active shards to agent memory
# Others remain cold storage in git history

# 9. GraphQL MCP bridge
# Expose vault as MCP server with:
# - query(noteId)
# - listNotes(section, tags)
# - createNote(title, body, section)
```

### 4. Architectural Trade-off Matrix

| Feature | Citadel | Mem0 | Zep | Letta |
|---------|---------|------|-----|-------|
| **Deterministic pruning** | ✅ | ❌ | ❌ | ❌ |
| **SHA-256 verification** | ✅ | ❌ | ❌ | ❌ |
| **Entity relationships** | ❌ | ✅ | ❌ | ✅ |
| **Temporal reasoning** | ❌ | ❌ | ✅ | ✅ |
| **Agent-editable** | ✅ | ❌ | ❌ | ✅ |
| **Zero-token storage** | ✅ | ❌ | ❌ | ❌ |
| **Vector semantics** | ❌ | ✅ | ✅ | ✅ |
| **MCP native** | ✅ | API | API | API |

### 5. Recommendation

**Your axiom vault is architecturally sound for cost-conscious, deterministic operation.** 

**Upgrade Path**: Layer graph memory ON TOP of your markdown vault:
- Keep markdown + git as source of truth
- Add SQLite graph table for entity relationships
- Add auto-extraction to create edges
- Keep watermark/receipt system as gate

This gives you the best of both worlds:
- Deterministic pruning (from Citadel)
- Relationship reasoning (from Mem0/Zep)
- Zero vendor lock-in