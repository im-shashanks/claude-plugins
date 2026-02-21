# Briefing Schema

Defines `.shaktra/stories/<story_id>/.briefing.yml` — a per-story filtered view of long-term knowledge, generated at workflow start and consumed by agents during execution.

## Schema

```yaml
story_context:
  id: string             # story ID (e.g., "ST-001")
  keywords: [string]     # extracted from story title, description, and scope

relevant_principles:
  - id: string           # PR-NNN
    text: string         # principle statement
    confidence: float    # current confidence score
    relevance: string    # why this principle matters for this story (1 sentence)
    roles: [string]      # which agents should read this

relevant_anti_patterns:
  - id: string           # AP-NNN
    failed_approach: string  # what went wrong
    recommended_approach: string # what to do instead
    severity: string     # P0-P3
    relevance: string    # why this anti-pattern is relevant
    roles: [string]      # which agents should read this

relevant_procedures:
  - id: string           # PC-NNN
    text: string         # procedure statement
    confidence: float    # current confidence score
    relevance: string    # why this procedure applies
    roles: [string]      # which agents should read this
```

## Generation Rules

### Tier Selection

Determine retrieval tier by calling `memory_retrieval.py` (counts active entries across all memory stores):

| Tier | Condition | Generator |
|---|---|---|
| 1 | total_entries ≤ `settings.memory.retrieval_tier1_max` | Orchestrator generates briefing inline |
| 2 | total_entries ≤ `settings.memory.retrieval_tier2_max` | Spawn single memory-retriever agent (briefing mode) |
| 3 | total_entries > `settings.memory.retrieval_tier2_max` | Spawn parallel chunk retrievers + consolidation retriever |

See `shaktra-memory/retrieval-guide.md` for the full retrieval algorithm and dispatch templates.

### Retrieval Algorithm (all tiers)

1. Read `principles.yml`, `anti-patterns.yml`, `procedures.yml`
2. Extract story keywords from title, description, acceptance criteria, and scope
3. Filter entries by:
   - `status: active` (exclude archived/superseded)
   - `confidence >= settings.memory.briefing_confidence_threshold`
   - Keyword/tag overlap with story context
   - Workflow type match (for procedures)
4. Score relevance: semantic relevance (0-10) × confidence — emphasize semantic matching over keyword overlap
5. Rank descending, cap at `settings.memory.max_briefing_entries`
6. For each matching entry, write a 1-sentence `relevance` explanation
7. Tag each entry with applicable `roles` for agent-filtered reading

## Agent Reading

Agents read the briefing filtered by their role:
- Developer reads entries where `roles` includes "developer"
- SW Quality reads entries where `roles` includes "sw-quality"
- Architect reads entries where `roles` includes "architect"

This ensures agents receive only relevant knowledge without loading the full memory stores.
