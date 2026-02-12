# Journey Mapping Workflow

Create customer journey maps that visualize the end-to-end experience for each persona, identifying pain points and improvement opportunities.

## Overview

Journey maps show:
1. The stages a user goes through
2. Touchpoints, actions, and emotions at each stage
3. Pain points and moments of truth
4. Opportunities for improvement

---

## Steps

### Step 1 — Load Context

Read:
- `.shaktra/settings.yml` — project context
- `.shaktra/personas/*.yml` — personas to map (required)
- `.shaktra/research/synthesis.yml` — pain points and insights
- `.shaktra/prd.md` — scope context

If no personas exist:
- Inform user: "Personas required for journey mapping. Run `/shaktra:pm personas` first."
- Stop workflow

### Step 2 — Select Personas

If multiple personas exist:
- Ask user: "Which personas should have journey maps?"
- Options: all, specific IDs, primary only

Default: create journey for all personas.

### Step 3 — Define Journey Scope

For each persona, determine journey scope:

> "What journey should we map for {persona.name}?
> Examples: New user onboarding, Daily workflow, Purchase decision"

If user doesn't specify, default to the primary interaction implied by PRD.

### Step 4 — Generate Journey Map

For each persona, spawn **product-manager** (mode: journey-create):

**Map through 5 phases:**

```yaml
stages:
  - name: "Problem Recognition"
    phase: awareness
    touchpoints:
      - channel: "<where interaction happens>"
        description: "<specific touchpoint>"
    actions:
      - "<what user does>"
    thoughts:
      - "<what user thinks>"
    emotions:
      valence: positive | neutral | negative | frustrated
      intensity: high | medium | low
      description: "<emotional state>"
    pain_points:
      - id: JP-01
        description: "<pain at this stage>"
        evidence_id: "<link to research>"
    opportunities:
      - id: JO-01
        description: "<improvement idea>"
        impact: high | medium | low
        effort: high | medium | low

  - name: "Solution Search"
    phase: consideration
    # ... same structure

  - name: "Signup / Purchase"
    phase: acquisition
    # ...

  - name: "Core Usage"
    phase: service
    # ...

  - name: "Renewal / Expansion"
    phase: loyalty
    # ...
```

**Moments of Truth:**
```yaml
moments_of_truth:
  - stage: "Signup / Purchase"
    description: "<critical decision point>"
    success_criteria: "<what must happen>"
    failure_impact: "<consequence of failure>"
```

### Step 5 — Link Evidence

For each pain point and opportunity:
- Link to research evidence where available
- Reference specific interview IDs, quotes
- Note assumptions where no evidence exists

### Step 6 — Prioritize Opportunities

Aggregate opportunities across stages and classify:

| Impact | Effort | Classification |
|---|---|---|
| High | Low | Quick Win — prioritize |
| High | High | Big Bet — plan carefully |
| Low | Low | Fill-in — if time permits |
| Low | High | Avoid — deprioritize |

### Step 7 — Validate Journey

| Check | Required |
|---|---|
| Persona ID exists in `.shaktra/personas/` | Yes |
| At least 3 stages defined | Yes |
| At least 1 moment of truth | Yes |
| Each stage has touchpoints | Yes |
| Each stage has emotions | Yes |
| Pain points reference evidence (if research exists) | Recommended |

### Step 8 — Write Journey Maps

Write each journey to `.shaktra/journeys/{persona_id}-journey.yml`.

Create directory if needed: `.shaktra/journeys/`

### Step 9 — Present Summary

```
## Journey Maps Created

**Personas Mapped:** {count}

### Journeys
| Persona | Journey | Stages | Opportunities |
|---|---|---|---|
| {persona.name} | {journey title} | {count} | {count} |

### Moments of Truth
1. {persona}: "{moment}" at {stage}
2. {persona}: "{moment}" at {stage}

### Top Opportunities
| Opportunity | Persona | Stage | Impact | Effort | Class |
|---|---|---|---|---|---|
| {description} | {persona} | {stage} | High | Low | Quick Win |

### Pain Points by Stage
- **Awareness:** {count} pain points
- **Consideration:** {count}
- **Acquisition:** {count}
- **Service:** {count}
- **Loyalty:** {count}

### Files Created
- .shaktra/journeys/{persona_id}-journey.yml

### Next Steps
1. Address Quick Win opportunities in upcoming PRD/stories
2. Plan Big Bets for future releases
3. Use moments of truth to define acceptance criteria
```

---

## Multiple Journeys Per Persona

If a persona has distinct journeys (e.g., onboarding vs daily use):
- Create separate files: `{persona_id}-onboarding-journey.yml`, `{persona_id}-daily-journey.yml`
- Each journey has its own scope and stages

---

## Integration Notes

**PRD:** Journey pain points validate or expand requirements. Moments of truth become acceptance criteria.

**Stories:** Opportunities translate to story candidates. Quick Wins → early sprint stories.

**TPM:** Journey maps inform design doc "Problem Statement" and "Goals" sections.
