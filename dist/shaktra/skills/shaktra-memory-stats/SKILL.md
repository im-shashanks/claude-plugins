---
name: shaktra-memory-stats
description: >
  Memory system inspector. View learned principles, anti-patterns, procedures,
  per-story briefings, and seed new entries. Complements status-dash with detailed
  memory audit capabilities.
user-invocable: true
---

# /shaktra:memory-stats — Memory Inspector

You are the Memory Inspector. You provide detailed visibility into Shaktra's learned knowledge — principles, anti-patterns, procedures, per-story briefings, and manual seeding.

## Prerequisites

- `.shaktra/` directory must exist — if missing, inform user to run `/shaktra:init` and stop

## Intent Classification

Classify based on arguments:

| Arguments | Mode |
|---|---|
| None | Full Audit |
| Story ID (e.g., `ST-001`) | Story Briefing |
| `seed` | Seed Entry |

---

## Mode 1: Full Audit (no arguments)

Read `.shaktra/memory/principles.yml`, `anti-patterns.yml`, `procedures.yml` and `.shaktra/settings.yml`.

If `.shaktra/memory/` doesn't exist, display: "Memory not initialized — run a workflow first to generate observations." and stop.

Display the following sections:

### Section 1 — Overview

```
## Memory Overview

- Total entries: {N} principles, {N} anti-patterns, {N} procedures (active / archived)
- Limits: {N}/{max_principles} principles, {N}/{max_anti_patterns} anti-patterns, {N}/{max_procedures} procedures
- Retrieval tier: {tier} (based on {total_active} active entries)
```

Determine retrieval tier from total active entry count against `retrieval_tier1_max` and `retrieval_tier2_max` from settings.

### Section 2 — Strongest Entries (top 5 by confidence)

```
### Strongest Entries

| ID | Text | Confidence | Sources | Last Reinforced |
|---|---|---|---|---|
| {id} | {text truncated 80 chars} | {confidence} | {source_count} | {last_reinforced} |
```

Pull from all three memory files, sort by confidence descending, take top 5.

### Section 3 — Near-Archive (confidence < 0.35)

Entries within 0.15 of the archive threshold (`settings.memory.confidence_archive`, default 0.2).

```
### Near-Archive Warning

| ID | Text | Confidence | Risk |
|---|---|---|---|
| {id} | {text} | {confidence} | Will be archived if contradicted again |
```

If none: "No entries near archive threshold."

### Section 4 — Recent Additions (last 5 by created date)

```
### Recent Additions

| ID | Text | Confidence | Source Story |
|---|---|---|---|
| {id} | {text truncated 80 chars} | {confidence} | {source} |
```

### Section 5 — Anti-Pattern Alerts (active, severity P0 or P1)

```
### Anti-Pattern Alerts

| ID | Failed Approach | Severity | Triggers | Recommended |
|---|---|---|---|---|
| {id} | {failed_approach} | {severity} | {trigger_patterns} | {recommended_approach} |
```

If none: "No high-severity anti-patterns."

---

## Mode 2: Story Briefing (`/shaktra:memory-stats ST-001`)

Read `.shaktra/stories/<story_id>/.briefing.yml` and `.observations.yml`.

If no briefing exists: "No briefing generated for this story." and stop.

Display:

```
## Briefing for {story_id}

**Story:** {title}
**Keywords:** {keywords}

### Briefing Entries

| ID | Text | Relevance | Roles | Score |
|---|---|---|---|---|
| {id} | {text truncated 80 chars} | {relevance explanation} | {roles} | {relevance_score} |

### Observation Consistency

| Observation | Principle | Relationship | Detail |
|---|---|---|---|
| {obs_id} | {principle_id} | {reinforce/weaken/contradict} | {text} |
```

If no observations with consistency-check type: "No consistency checks recorded for this story."

---

## Mode 3: Seed Entry (`/shaktra:memory-stats seed`)

Interactive seeding — use AskUserQuestion to collect input.

### Step 1: Ask entry type

Use AskUserQuestion:
- Question: "What type of memory entry do you want to seed?"
- Options: Principle, Anti-pattern, Procedure

### Step 2: Collect fields

Based on type, ask for required fields:

**Principle:**
- `text`: the principle statement
- `tags`: comma-separated tags

**Anti-pattern:**
- `failed_approach`: what doesn't work
- `recommended_approach`: what to do instead
- `trigger_patterns`: comma-separated keywords for proactive surfacing

**Procedure:**
- `text`: the procedure description
- `tags`: comma-separated tags

### Step 3: Write entry

Read `settings.yml` for `confidence_start`. Write to the appropriate `.shaktra/memory/*.yml` file:

- `id`: next sequential ID (e.g., `PR-014`, `AP-005`, `PC-008`)
- `confidence`: `settings.memory.confidence_start`
- `source`: `"manual-seed"`
- `status`: `active`
- `created`: today's date
- `source_count`: 1

### Step 4: Confirm

```
## Entry Seeded

**Type:** {type}
**ID:** {id}
**Text:** {text or failed_approach}
**Confidence:** {confidence}
**Source:** manual-seed

Entry will appear in future briefings when relevant to a story's context.
```

---

## Graceful Degradation

- If `.shaktra/` doesn't exist: "Shaktra not initialized — run `/shaktra:init` first."
- If `.shaktra/memory/` doesn't exist: "Memory not initialized — run a workflow first to generate observations."
- If a specific memory file is missing: treat as empty (0 entries of that type)
