# Consolidation Guide

The memory-curator runs this algorithm after every workflow to transform per-story observations into long-term knowledge.

## Input

**Workflow-level observations:** When processing observations from `.shaktra/observations/` (non-story workflows), skip consistency-check processing (no briefing exists to validate against). All other steps apply.

- `.shaktra/stories/<story_id>/.observations.yml` — observations from the completed workflow (or `.shaktra/observations/<workflow_id>.yml` for non-story workflows)
- `.shaktra/memory/principles.yml` — existing principles
- `.shaktra/memory/anti-patterns.yml` — existing anti-patterns
- `.shaktra/memory/procedures.yml` — existing procedures
- `.shaktra/settings.yml` — confidence thresholds and max limits

## Step 1: Classify Observations

For each observation, classify by its `type` and `tags`:

| Observation Type | Classification Target |
|---|---|
| `discovery` with pattern/technique tags | Principle candidate |
| `quality-loop-finding` with `resolved: true` | Principle candidate (learned fix) |
| `quality-loop-finding` with `resolved: false` | Anti-pattern candidate |
| `fix-rationale` | Principle candidate |
| `deviation` | Principle candidate (if justified) |
| `observation` with constraint tags | Principle candidate |
| `incident-learning` | Anti-pattern candidate (high confidence — production-confirmed failure) |
| `detection-gap` | Procedure candidate (quality gate improvement) |
| `consistency-check` | Reinforce/weaken/contradict existing entry |

## Step 2: Match Against Existing Entries

For each classified observation, search existing entries:

1. **Title similarity** — does the observation text overlap with an existing entry's `text`?
2. **Category overlap** — do the observation's tags map to the same categories?
3. **Guidance overlap** — does the observation imply the same actionable rules?

**Match threshold:** If 2 of 3 criteria overlap significantly (>60%), treat as a match.

## Step 3: Apply Confidence Math

All threshold values come from `settings.memory.*`:

| Action | Formula | Default |
|---|---|---|
| New entry created | `confidence = settings.memory.confidence_start` | 0.6 |
| Existing entry reinforced | `confidence += settings.memory.confidence_reinforce` | +0.08 |
| Existing entry weakened | `confidence -= settings.memory.confidence_weaken` | -0.08 |
| Existing entry contradicted | `confidence -= settings.memory.confidence_contradict` | -0.20 |
| Archive threshold | `confidence < settings.memory.confidence_archive` | < 0.2 |
| Incident multiplier | `adjustment *= settings.incident.incident_confidence_multiplier` when `workflow_type: incident` | 1.5x |

Confidence is clamped to the range [0.0, 1.0]. The incident multiplier applies to both new entry creation (start confidence) and reinforcement adjustments for observations from incident workflows.

## Step 4: Anti-Pattern Detection

Create an anti-pattern entry when:
- 2+ failure observations (`type: quality-loop-finding`, `resolved: false`) on the **same pattern** within 3 stories
- Pattern match: same tags and similar issue descriptions
- **Fast-track:** Create anti-pattern immediately (no 2-story wait) when source is `incident-learning` with importance >= 9. Production incidents are pre-confirmed failures.

Anti-pattern entry fields:
- `failed_approach`: what went wrong (from observation text)
- `failure_mode`: why it fails (from observation context)
- `severity`: highest severity from source observations
- `recommended_approach`: from the fix-rationale observation that eventually resolved it (if available)
- `trigger_patterns`: keywords from observation tags

## Step 5: Procedure Detection

Create a procedure entry when:
- 3+ workflow-level observations (`type: observation` or `type: deviation`) across **different stories**
- Observations describe the same workflow adaptation or risk pattern

Procedure entries capture workflow-level learnings (not code patterns — those are principles).

## Step 6: Deduplication

Merge entries with >80% guidance overlap:
- Keep the entry with higher confidence
- Combine `source_count` values
- Update `last_reinforced` to the more recent date

## Step 7: Archival and Rotation

1. **Archive:** Set `status: archived` on any entry where `confidence < settings.memory.confidence_archive`
2. **Rotate:** If active entry count exceeds the max limit, archive lowest-confidence entries first:
   - Principles: `settings.memory.max_principles` (default 200)
   - Anti-patterns: `settings.memory.max_anti_patterns` (default 100)
   - Procedures: `settings.memory.max_procedures` (default 50)

Archived entries remain in the file but are excluded from briefings and agent loading.

## Step 8: Role Inference

Map observation categories/tags to agent roles for the `roles` field:

| Category/Tag Pattern | Roles |
|---|---|
| correctness, reliability, performance | developer, sw-engineer |
| security | developer, sw-engineer, sw-quality |
| maintainability, testability | developer, sw-quality |
| consistency, patterns | developer, sw-engineer, architect |
| observability, scalability | developer, architect |
| workflow, process, planning | sdm (orchestrator-level) |
| incident, detection-gap, post-mortem | developer, sw-engineer, sw-quality, cr-analyzer |

## Output

- Updated `principles.yml`, `anti-patterns.yml`, `procedures.yml`
- Set `memory_captured: true` in the handoff file
