# Observation Guide

Instructions for agents writing observations during workflow execution.

## When to Observe

Write an observation when you encounter:
- **Non-obvious discovery** — a codebase pattern, API behavior, or constraint that wasn't documented
- **Quality loop finding** — a quality gate blocked and required fixes
- **Fix rationale** — why a specific fix approach was chosen over alternatives
- **Deviation from plan** — implementation diverged from the agreed plan
- **Pattern decision** — a new design pattern was introduced or an existing one was followed/deviated from
- **Consistency check** — an existing principle was validated, weakened, or contradicted

## When NOT to Observe

Do not write observations for:
- Routine operations ("tests passed", "coverage met", "build succeeded")
- Obvious behavior ("the function returns the expected value")
- Tool output without interpretation ("npm install completed")
- Duplicate observations within the same story

## Observation Schema

Write observations to `.shaktra/stories/<story_id>/.observations.yml`:

```yaml
observations:
  - id: "OB-001"          # sequential within story
    agent: "developer"     # your agent name
    phase: "code"          # current TDD phase
    type: "discovery"      # see Type Reference
    text: "description"    # 1-3 sentences
    tags: ["pattern", "api"]  # freeform, used for matching
    importance: 7          # 1-10 scale
```

## Type Reference

| Type | When | Example |
|---|---|---|
| `discovery` | Found a non-obvious pattern or constraint | "All API handlers in this project use middleware chaining with error boundaries" |
| `quality-loop-finding` | Quality gate blocked and required fixes | "Missing timeout on external HTTP call flagged as P0" |
| `fix-rationale` | Explains why a fix was chosen | "Used circuit breaker instead of simple retry because upstream has cascading failure risk" |
| `deviation` | Implementation diverged from plan | "Added caching layer not in original plan due to observed N+1 query pattern" |
| `observation` | General workflow or risk observation | "Stories touching the auth module consistently need extra security review" |
| `consistency-check` | Validated or challenged existing principle | "PR-003 (always use DI for external services) confirmed applicable here" |
| `incident-learning` | Post-incident finding about systemic failure or process gap | "Production timeout was caused by unbounded query — no pagination enforced at API layer" |
| `detection-gap` | Quality gate gap identified during incident analysis | "Code review checked error handling but not timeout behavior on the external call" |

## Importance Scale

| Range | Meaning | Example |
|---|---|---|
| 1-3 | Minor — noted but unlikely to change behavior | "Consistent use of camelCase in test names" |
| 4-6 | Moderate — useful context for similar work | "This API requires pagination for lists > 100 items" |
| 7-8 | High — would materially change future planning | "Repository pattern doesn't work here due to multi-tenant isolation" |
| 9-10 | Critical — ignoring this caused or would cause production issues | "Race condition in session handling under concurrent requests" |

**Incident observations** (`incident-learning`, `detection-gap`) default to importance 8-10. Production incidents represent the strongest signal about quality gate gaps and systemic failures.

## Optional Fields

Add these only when the type warrants them:

| Field | Types | Purpose |
|---|---|---|
| `severity` | quality-loop-finding | P0-P3 severity of the finding |
| `resolved` | quality-loop-finding | Whether the finding was fixed |
| `iterations` | quality-loop-finding | Number of fix attempts |
| `principle_id` | consistency-check | ID of the principle being checked |
| `relationship` | consistency-check | "reinforce", "weaken", or "contradict" |

## Workflow-Level Observations

For workflows without stories (analysis, PM brainstorm/research), write observations to:

`.shaktra/observations/<workflow_id>.yml`

- `workflow_id` format: `<type>-<YYYY-MM-DD>` (e.g., `analysis-2026-02-18`, `brainstorm-2026-02-18`)
- Same schema as story observations
- Types limited to: `discovery`, `observation` (no `consistency-check` — no briefing to validate)
- Create the `.shaktra/observations/` directory if it doesn't exist
