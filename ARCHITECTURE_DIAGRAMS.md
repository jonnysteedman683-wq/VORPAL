# Axiom Vault Architecture Diagrams

## Diagram 1: Three-Tier Memory Stack (ContextNest + Mem0 + Zep)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THREE-TIER MEMORY ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  Layer 1: ContextNest (Governed Corporate Knowledge)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Git-Tracked Markdown Vault                                       │   │
│  │  ├─ Directives/     (policies, constraints)                       │   │
│  │  ├─ Protocols/     (workflows, procedures)                        │   │
│  │  ├─ Decisions Log/(architectural, product decisions)             │   │
│  │  ├─ Goals/          (active objectives)                          │   │
│  │  ├─ Tasks/          (actionable work items)                      │   │
│  │  ├─ Memory/         (patterns, lessons learned)                │   │
│  │  └─ Archives/       (superseded material)                        │   │
│  │                                                                   │   │
│  │  Governance: SHA-256 hash chains, steward approvals                │   │
│  │  Query: Deterministic pruning, never returns stale facts           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    ▲                                        │
│                                    │ MCP/Native Protocol                     │
│                                    │                                        │
┌────────────────────────────────────┼─────────────────────────────────────────┐
│  Layer 2: Mem0 (Personalization Memory)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Semantic Graph Database                                           │   │
│  │  ├─ User preference nodes (IDE configs, habits, hobbies)           │   │
│  │  ├─ Session context graphs                                           │   │
│  │  ├─ Entity relationships (mentions, references, dependencies)      │   │
│  │  │                                                                │   │
│  │  │  [user_123] ──prefers──► {haiku}                               │   │
│  │  │        │                                      │                   │   │
│  │  │        └──ordered──► {coffee}                                   │   │
│  │  │                                        │                       │   │
│  │  │  [task_456] ──visited──► [[Protocols/Token Optimization]]     │   │
│  │  └───────────────────────────────────────────────────────────────│   │
│  │                                                                   │   │
│  │  Write: Auto-extraction from chat during runtime                   │   │
│  │  Read: Hybrid vector + graph retrieval                             │   │
│  └──┬───────────────────────────────────────────────────────────────┘   │
│     │                                                                    │
│     │ API/SDK Integration                                                │
┌────┴────┬───────────────────────────────────────────────────────────────┐
│  Layer 3: Zep (Session Log Memory)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Message Database with Auto-Summarization                           │   │
│  │  ├─ Raw conversation transcripts                                   │   │
│  │  ├─ Semantic indexes                                               │   │
│  │  ├─ Summarized session history                                     │   │
│  │  │                                                                │   │
│  │  │  Session 2026-08-29-1430                                        │   │
│  │  │  ├─ User: "reduce token costs"                                 │   │
│  │  │  ├─ Assistant: "best practices are..."                         │   │
│  │  │  └─ Summary: User researching cost optimization techniques       │   │
│  │  │                                                                │   │
│  │  │  Session 2026-08-29-1500                                        │
│  │  │  ├─ User: "yes"                                                 │   │
│  │  │  └─ Assistant: "built token-optimizer skill..."                │   │
│  │  └───────────────────────────────────────────────────────────────│   │
│  │                                                                   │   │
│  │  Write: Continuous logging during conversations                    │   │
│  │  Read: Query recent sessions, auto-summarized                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  How the Layers Work Together                                              │
│                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                   │
│  │   Query     │───▶│   Context   │───▶│   Response  │                   │
│  │  (Agent)    │    │Composition  │    │   (LLM)     │                   │
│  └─────────────┘    └─────────────┘    └─────────────┘                   │
│       │                     │                   │                      │
│       ▼                     ▼                   ▼                      │
│  ┌─────────────┐    ┌─────────────────────────────────────┐             │
│  │  Token      │───▶│ Layer 3: Zep (recent session)       │             │
│  │  Budget     │    │ - Last 2-3 sessions                 │             │
│  │  Check      │    │ - Auto-summarized                   │             │
│  └─────────────┘    └─────────────────────────────────────┘             │
│       │                     │                                           │
│       ▼                     ▼                                           │
│  ┌─────────────────────────────────────┐                                │
│  │ Layer 2: Mem0 (user preferences)    │                                │
│  │ - Top 3-5 relevant memories         │                                │
│  │ - Filtered by Jaccard similarity      │                                │
│  └─────────────────────────────────────┘                                │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────┐                                │
│  │ Layer 1: ContextNest (governed facts│                                │
│  │ - Only approved, non-stale docs     │                                │
│  │ - Pruned by SHA-256 verification    │                                │
│  └─────────────────────────────────────┘                                │
│                                                                          │
│  Result: 500-800 tokens of verified context (vs 5000+ naive injection) │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Diagram 2: Your Axiom Vault Memory Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AXIOM VAULT DIRECTORY STRUCTURE                        │
└─────────────────────────────────────────────────────────────────────────────┘

                        ╔══════════════════════════════════╗
                        ║    AXION VAULT (Markdown Files)  ║
                        ╚══════════════╤═══════════════════╝
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
               ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
               │ Memory/ │        │ Goals/  │        │ Tasks/  │
               │         │        │         │        │         │
               │ Pattern │        │ ACTIVE  │        │ TODO    │
               │ Lesson  │        │ ✓ DONE  │        │ DOING   │
               │ 2026... │        │ Archive │        │ Queue   │
               └─────────┘        └─────────┘        └─────────┘
                    │                  │                  │
                    │    ┌─────────────┼─────────────┐      │
                    │    │             │             │      │
               ╔════▼════╗     ╔══════▼══════╗   ╔════▼═════╗  │
               ║ Search  ║     ║ Mark        ║   ║ Allocate ║  │
               ║ (regex) ║     ║ Complete    ║   ║ Priority ║  │
               ╚═════════╝     ╚═════════════╝   ╚══════════╝  │
                    │                  │                  │      │
                    └──────────────────┼──────────────────┘      │
                                       │                         │
                          ┌────────────▼────────────┐            │
                          │   citadel_recall.py     │            │
                          │   (search + read + write)           │
                          │   Watermark: HR-YYYYMMDD-NNN        │
                          │   Evidence: [VERIFIED]/[MEDIUM]/[LOW] │
                          └─────────────────────────┘            │
                                       │                         │
                                       ▼                         │
                          ┌─────────────────────────┐            │
                          │   Token Optimization    │◀───────────┘
                          │   Layer (token-optimizer.skill)
                          │   Budget: 800 tokens    │
                          │   Filter: top 3 memories│
                          │   Route: model by task  │
                          └─────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                    WATERMARK PROVENANCE FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  User Request              Agent Action                  Vault Write

     │                         │                              │
     ▼                         ▼                              ▼
  "Save this insight"    c.create_note(               Memory/2026-08-30_...",
                          title="Token Optimization"                      │
                          content="Budget 800 tokens..."                    │
                          section="Memory"                                  │
                          source_run_id="hermes:..."                   │
                          reason="pattern for cost control")           │
                                                ┌─────────────────────┴───┐
                                                │  VAULT WRITE            │
                                                │  1. render_watermark()  │
                                                │    - origin_system:Her. │
                                                │    - origin_agent:cit.  │
                                                │    - receipt_id:HR-...  │
                                                │  2. append_handoff_log() │
                                                │  3. atomic write + SHA256 │
                                                └─────────────────────────┘
                                                                │
                                                                ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Memory/2026-08-30_Token_Optimization.md                               │
  │  ---                                                                  │
  │  watermark:                                                           │
  │    origin_system: "Hermes"                                            │
  │    origin_agent: "citadel_recall"                                     │
  │    created: "2026-08-30T14:00:00"                                     │
  │    modified: "2026-08-30T14:00:00"                                   │
  │    source: "hermes:session_abc123"                                    │
  │    receipt_id: "HR-20260830-001"                                      │
  │  ---                                                                  │
  │  # Token Optimization                                                 │
  │                                                                       │
  │  [VERIFIED]                                                           │
  │                                                                       │
  │  Source run: `hermes:session_abc123`                                  │
  │  Reason: pattern for cost control in skill architecture               │
  │  Receipt: `HR-20260830-001`                                           │
  │                                                                       │
  │  Core insight: Budget-based memory injection achieves 75% token       │
  │  reduction vs full injection.                                         │
  └─────────────────────────────────────────────────────────────────────────┘
```

## Diagram 3: Token Optimization Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     TOKEN OPTIMIZATION PIPELINE                              │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌────────────────────────────┐
                    │  User Query:              │
                    │  "research token opt..." │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │  citadel_recall.search()   │
                    │  - Query: "token optimization"│
                    │  - Section: Memory/        │
                    │  - Limit: 10               │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │  Rank by score (0.0-1.0)   │
                    │  - 1. Mark: 0.95 (decision)│
                    │  - 2. Mark: 0.82 (pattern) │
                    │  - 3. Mark: 0.71 (experiment)│
                    │  - ...                     │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │  budget_inject(entries,  │
                    │           budget=800)     │
                    │                            │
                    │  Selected: 3 entries        │
                    │  Tokens: 756 (under budget)│
                    │  Overflow: 5 entries        │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │  Generate Context:        │
                    │  - entry1                  │
                    │  - entry2                  │
                    │  - entry3                  │
                    │  -                         │
                    │  [Note: 5 entries omitted] │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │  route_to_model("research",│
                    │           effort="normal")│
                    │  → sonnet (cost-effective) │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │  LLM Response (sonnet)     │
                    │  - Contains patterns       │
                    │  - References receipt IDs  │
                    │  - Suggests implementation │
                    └────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  COST BREAKDOWN:                                                            │
│  - Memory injection: 800 tokens                                           │
│  - Model input (sonnet): 1,200 tokens                                     │
│  - Output: ~300 tokens                                                    │
│  - Total: ~2,300 tokens                                                   │
│  - Estimated cost: $0.001 (sonnet) @ $0.003/1K tokens                    │
└─────────────────────────────────────────────────────────────────────────────┘
```