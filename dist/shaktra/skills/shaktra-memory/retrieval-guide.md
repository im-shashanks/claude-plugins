# Retrieval Guide

Shared algorithm for generating per-story briefings from long-term memory. Used by orchestrators (Tier 1 inline) and the memory-retriever agent (Tier 2/3).

## Tier Selection

Before generating a briefing, determine the retrieval tier:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory_retrieval.py <story_dir> <settings_path>
```

Output: `{"tier": N, "total_entries": N, "chunks": [...]}`

| Tier | Condition | Action |
|---|---|---|
| 1 | total ≤ `retrieval_tier1_max` | Generate briefing inline (orchestrator does it) |
| 2 | total ≤ `retrieval_tier2_max` | Spawn memory-retriever in `briefing` mode |
| 3 | total > `retrieval_tier2_max` | Python already wrote chunks → spawn parallel chunk retrievers + consolidation |

## Retrieval Algorithm

Follow these steps for all tiers. In Tier 1, the orchestrator executes inline. In Tier 2/3, the memory-retriever agent executes.

### Step 1: Extract Story Context

Read the story YAML and extract:
- Title, description, acceptance criteria
- Scope (feature, bug_fix, refactor, etc.)
- Tags and keywords (from title words, description nouns, scope area)

### Step 2: Load and Filter Entries

Load entries from `principles.yml`, `anti-patterns.yml`, `procedures.yml` (or from the provided chunk file in Tier 3).

Exclude:
- Entries with `status: archived` or `status: superseded`
- Entries with `confidence < settings.memory.briefing_confidence_threshold`

### Step 3: Score Relevance

For each remaining entry, compute a relevance score:

```
relevance_score = semantic_relevance(0-10) × confidence
```

**Semantic relevance** — how much this entry's insight would change behavior for this specific story. Emphasize meaning over keyword overlap:
- 9-10: Directly describes a pattern, risk, or approach for this exact problem domain
- 6-8: Related domain, transferable insight
- 3-5: Tangentially related, might apply
- 1-2: Weak connection, unlikely to help
- 0: No relevance

**Anti-pattern trigger boost** — For anti-pattern entries with `trigger_patterns`, check each trigger against the story's keywords (from Step 1). If any trigger matches (case-insensitive substring), set `semantic_relevance = max(semantic_relevance, 8)`. This ensures known failure patterns surface proactively even when the semantic connection seems indirect.

### Step 4: Rank and Cap

Sort entries by `relevance_score` descending. Keep top `settings.memory.max_briefing_entries` entries.

### Step 5: Write Relevance and Roles

For each selected entry:
- Write a 1-sentence `relevance` explanation: why this entry matters for this story
- Assign `roles`: which agents should read this entry (developer, sw-engineer, architect, sw-quality, test-agent)

### Step 6: Write Briefing

Write `.briefing.yml` to the story directory following the briefing-schema.

## Tier 3: Chunk Processing

When `memory_retrieval.py` returns tier 3, it has already written chunk files to `<story_dir>/.chunks/`.

1. Read `.chunks/manifest.yml` for chunk paths
2. Spawn one memory-retriever per chunk in `chunk` mode (parallel)
3. Each chunk retriever scores its entries and writes a partial result
4. After all chunk retrievers complete, spawn one memory-retriever in `consolidate` mode
5. Consolidation retriever merges partials, deduplicates, re-ranks, caps, writes final `.briefing.yml`

## Dispatch Templates

Use these Task() prompts when spawning memory-retriever agents.

### Briefing Mode (Tier 2)

```
You are the shaktra-memory-retriever agent operating in briefing mode.

Story: {story_path}
Story directory: {story_dir}
Settings: {settings_path}
Memory directory: {memory_dir}
Mode: briefing

Read all memory files, score entries by relevance to the story, and write
.briefing.yml to the story directory. Follow retrieval-guide.md algorithm.
```

### Chunk Mode (Tier 3 — one per chunk)

```
You are the shaktra-memory-retriever agent operating in chunk mode.

Story: {story_path}
Chunk: {chunk_path}
Output: {partial_output_path}
Mode: chunk

Score entries in the chunk by relevance to the story. Write partial results
to the output path. Follow retrieval-guide.md algorithm (steps 1-3, 5).
```

### Consolidate Mode (Tier 3 — after all chunks)

```
You are the shaktra-memory-retriever agent operating in consolidate mode.

Story directory: {story_dir}
Partial results: {partial_paths}
Settings: {settings_path}
Mode: consolidate

Merge all partial results. Deduplicate entries that appear in multiple chunks.
Re-rank by relevance_score, cap at max_briefing_entries, write final .briefing.yml.
```
