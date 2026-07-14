# Retrieval Guide

Shared algorithm for generating work briefings from long-term memory. Executed
by the memory-retriever agent, dispatched by `workflows/lib/memory.js` in
briefing mode. Tier sizing comes from `scripts/shaktra_context.py`
(`memory.retrieval_tier` in the context blob).

## Tier Selection

| Tier | Condition | Dispatch shape |
|---|---|---|
| 1 | total active entries ≤ `retrieval_tier1_max` | One retriever reads all three stores |
| 2 | total ≤ `retrieval_tier2_max` | Same as Tier 1 (single retriever) |
| 3 | total > `retrieval_tier2_max` | One retriever per store file in parallel; `lib/memory.js` merges and caps |

There are no chunk files — for large stores the fan-out unit is the store file
itself, and the merge happens deterministically in the workflow layer.

## Retrieval Algorithm

### Step 1: Extract Work Context

From the work context supplied at dispatch (story summary, workflow type,
roles involved), extract: the problem domain, scope (feature, bug_fix,
refactor, …), and keywords (title words, description nouns, scope area).

### Step 2: Load and Filter Entries

Load entries from the store file(s) named at dispatch (`principles.yml`,
`anti-patterns.yml`, `procedures.yml`; a missing file is an empty store).

Exclude:
- Entries with `status: archived` or `status: superseded`
- Entries with `confidence` below the threshold supplied at dispatch

### Step 3: Score Relevance

For each remaining entry, compute a relevance score:

```
relevance_score = semantic_relevance(0-10) × confidence
```

**Semantic relevance** — how much this entry's insight would change behavior
for this specific work. Emphasize meaning over keyword overlap:
- 9-10: Directly describes a pattern, risk, or approach for this exact problem domain
- 6-8: Related domain, transferable insight
- 3-5: Tangentially related, might apply
- 1-2: Weak connection, unlikely to help
- 0: No relevance

**Anti-pattern trigger boost** — For anti-pattern entries with
`trigger_patterns`, check each trigger against the work keywords (Step 1). If
any trigger matches (case-insensitive substring), set
`semantic_relevance = max(semantic_relevance, 8)`. Known failure patterns
surface proactively even when the semantic connection seems indirect.

### Step 4: Rank and Cap

Sort by `relevance_score` descending. Keep at most the entry cap supplied at
dispatch (in Tier 3 each per-store retriever applies the cap; the workflow
layer re-caps the merged result).

### Step 5: Return the Briefing

Return selected entries in-band per the structured-output schema supplied at
dispatch — id and text verbatim, plus `roles` (which agents should read this
entry: developer, sw-engineer, architect, sw-quality, test-agent). The
orchestrator persists the briefing into `handoff.briefing` for story workflows.
