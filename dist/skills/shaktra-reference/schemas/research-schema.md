# Research Schema

Defines the structure of customer research artifacts in `.shaktra/research/`. Research feeds into personas, validates requirements, and provides evidence for product decisions.

## Interview Analysis Schema

```yaml
# .shaktra/research/{interview_id}.yml
id: string              # required — unique identifier (e.g., "INT-001")
type: interview         # required — "interview" | "survey" | "observation"
date: date              # required — when conducted
participant:
  role: string          # required — job title or user type
  segment: string       # required — user segment
  anonymized_id: string # required — anonymous identifier (e.g., "P12")

pain_points:            # required — problems they described (min 1)
  - id: string          # unique within interview (e.g., "PP-01")
    description: string # what hurts
    severity: string    # "high" | "medium" | "low"
    frequency: string   # "daily" | "weekly" | "monthly" | "rarely"
    quote: string       # verbatim quote if available

feature_requests:       # optional — explicit asks
  - id: string
    description: string
    priority: string    # participant's stated priority
    context: string     # why they want it

jobs_to_be_done:        # required — observed JTBD patterns (min 1)
  - situation: string
    motivation: string
    outcome: string
    current_solution: string  # how they solve it today

competitor_mentions:    # optional
  - name: string
    context: string     # what they said about it
    sentiment: string   # "positive" | "negative" | "neutral"

key_quotes:             # required — notable verbatim quotes (min 2)
  - quote: string
    context: string
    theme: string       # which theme this supports

notes: string           # optional — analyst notes
```

## Research Synthesis Schema

```yaml
# .shaktra/research/synthesis.yml
id: string              # required — synthesis identifier
created: date           # required
updated: date           # required
interview_ids:          # required — which interviews inform this synthesis
  - string

themes:                 # required — recurring patterns (min 2)
  - id: string          # e.g., "TH-01"
    name: string        # short theme name
    description: string # what the theme represents
    evidence_count: integer  # how many interviews support it
    confidence: string  # "high" | "medium" | "low"
    supporting_interviews:
      - id: string
        pain_point_id: string  # reference to specific finding

patterns:               # required — behavioral patterns observed
  - name: string
    description: string
    frequency: string   # "common" | "occasional" | "rare"
    evidence:
      - interview_id: string
        observation: string

recommendations:        # required — actionable insights (min 1)
  - id: string          # e.g., "REC-01"
    recommendation: string
    rationale: string
    priority: string    # "high" | "medium" | "low"
    supporting_themes:
      - string          # theme IDs
    confidence: string

gaps:                   # optional — areas needing more research
  - area: string
    reason: string
    suggested_method: string
```

## Confidence Levels

| Level | Criteria |
|---|---|
| **High** | 3+ interviews with consistent findings |
| **Medium** | 2 interviews with aligned findings |
| **Low** | 1 interview or conflicting findings |

## Validation Rules

| Rule | Severity |
|---|---|
| Each interview has at least 1 pain point | P0 |
| Each interview has at least 1 JTBD | P0 |
| Synthesis has at least 2 themes | P0 |
| All theme evidence IDs reference existing interviews | P1 |
| Confidence levels match evidence count criteria | P1 |

## Storage

- Individual interviews: `.shaktra/research/{interview_id}.yml`
- Synthesis: `.shaktra/research/synthesis.yml`
