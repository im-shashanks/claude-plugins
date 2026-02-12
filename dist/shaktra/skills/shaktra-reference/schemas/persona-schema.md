# Persona Schema

Defines the structure of user personas in `.shaktra/personas/`. Personas ground requirements in real user needs and enable traceability from research to PRD to stories.

## Schema

```yaml
# .shaktra/personas/{persona_id}.yml
id: string              # required — unique identifier (e.g., "P-001")
name: string            # required — archetype name (e.g., "Power User Paula")
role: string            # required — job title or user type
segment: string         # required — user segment (e.g., "enterprise", "prosumer", "casual")

demographics:
  age_range: string     # optional — e.g., "25-35"
  location: string      # optional — geographic context
  tech_savviness: string # optional — "low" | "medium" | "high"

goals:                  # required — what they want to achieve (min 2)
  - string

frustrations:           # required — current pain points (min 2)
  - string

behaviors:              # required — how they currently work (min 2)
  - string

jobs_to_be_done:        # required — JTBD format (min 1)
  - situation: string   # "When I..."
    motivation: string  # "I want to..."
    outcome: string     # "So I can..."

evidence:               # required — sources that informed this persona
  - type: string        # "interview" | "analytics" | "survey" | "support_ticket" | "observation"
    id: string          # reference ID (e.g., "INT-003", "analytics-q4-2024")
    insight: string     # what this source contributed

quote: string           # optional — representative verbatim quote

created: date           # required — ISO date
updated: date           # required — last modification date
```

## Evidence Requirements

Personas must be grounded in real data, not assumptions:

| Evidence Type | Minimum Count | Notes |
|---|---|---|
| Interview | 1+ | Reference `.shaktra/research/` entries |
| Analytics | 0+ | Quantitative behavior patterns |
| Survey | 0+ | Self-reported preferences |
| Support ticket | 0+ | Real pain points from support |
| Observation | 0+ | Direct user observation |

**Total evidence entries:** Minimum 2 from any combination.

## JTBD Format

Jobs-to-be-Done follow the standard structure:

> "When [situation], I want to [motivation], so I can [outcome]."

Example:
```yaml
jobs_to_be_done:
  - situation: "When I'm reviewing code at 2am before a release"
    motivation: "I want to quickly identify security issues"
    outcome: "So I can ship confidently without staying up longer"
```

## Validation Rules

| Rule | Severity |
|---|---|
| At least 2 evidence entries | P0 |
| At least 1 job-to-be-done | P0 |
| Goals and frustrations each have min 2 entries | P1 |
| All interview evidence IDs exist in `.shaktra/research/` | P1 |

## Storage

Personas are stored as individual YAML files: `.shaktra/personas/{persona_id}.yml`
