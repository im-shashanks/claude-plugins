# Journey Map Schema

Defines the structure of customer journey maps in `.shaktra/journeys/`. Journey maps visualize the end-to-end experience for a persona and identify improvement opportunities.

## Schema

```yaml
# .shaktra/journeys/{persona_id}-journey.yml
id: string              # required — unique identifier
persona_id: string      # required — links to .shaktra/personas/{id}.yml
title: string           # required — journey name (e.g., "New User Onboarding")
scope: string           # required — what this journey covers
created: date           # required
updated: date           # required

stages:                 # required — journey stages (min 3)
  - name: string        # stage name
    phase: string       # "awareness" | "consideration" | "acquisition" | "service" | "loyalty"

    touchpoints:        # required — where interaction happens
      - channel: string # e.g., "website", "email", "app", "support"
        description: string

    actions:            # required — what the user does
      - string

    thoughts:           # required — what the user thinks
      - string

    emotions:           # required — emotional state
      valence: string   # "positive" | "neutral" | "negative" | "frustrated"
      intensity: string # "high" | "medium" | "low"
      description: string

    pain_points:        # optional — problems at this stage
      - id: string
        description: string
        evidence_id: string  # link to research finding

    opportunities:      # optional — improvement ideas
      - id: string
        description: string
        impact: string  # "high" | "medium" | "low"
        effort: string  # "high" | "medium" | "low"

moments_of_truth:       # required — critical decision points (min 1)
  - stage: string       # which stage
    description: string
    success_criteria: string
    failure_impact: string

overall_sentiment: string  # "positive" | "mixed" | "negative"

evidence:               # required — sources backing this journey
  - type: string        # "interview" | "analytics" | "observation"
    id: string
```

## Journey Phases

Standard 5-phase customer lifecycle:

| Phase | Description | Typical Stages |
|---|---|---|
| **Awareness** | User discovers a problem or solution | Problem recognition, initial search |
| **Consideration** | User evaluates options | Comparison, trial, research |
| **Acquisition** | User commits to solution | Purchase, signup, onboarding |
| **Service** | User actively uses the product | Core workflows, support |
| **Loyalty** | User becomes advocate or churns | Renewal, referral, expansion |

## Opportunity Prioritization

Opportunities use a simple impact/effort matrix:

| Impact | Effort | Priority |
|---|---|---|
| High | Low | Quick Win — do first |
| High | High | Big Bet — plan carefully |
| Low | Low | Fill-in — if time permits |
| Low | High | Avoid — deprioritize |

## Validation Rules

| Rule | Severity |
|---|---|
| Persona ID exists in `.shaktra/personas/` | P0 |
| At least 3 stages defined | P0 |
| At least 1 moment of truth defined | P0 |
| Pain points reference valid research evidence IDs | P1 |
| Each stage has at least 1 touchpoint | P1 |
| Each stage has emotions defined | P1 |

## Storage

Journey maps are stored as: `.shaktra/journeys/{persona_id}-journey.yml`

One journey map per persona. If a persona has multiple distinct journeys (e.g., onboarding vs. daily use), use descriptive IDs: `{persona_id}-{journey_type}-journey.yml`
