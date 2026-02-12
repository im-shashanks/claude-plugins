# Research Analysis Workflow

Analyze customer research inputs (interview transcripts, surveys, feedback) to extract insights that inform personas, validate requirements, and guide product decisions.

## Overview

Research analysis transforms raw qualitative data into structured insights:
1. Extract findings from individual sources
2. Identify patterns across sources
3. Synthesize into themes with confidence levels
4. Generate actionable recommendations

---

## Steps

### Step 1 — Collect Research Inputs

Ask user to provide research materials:

> "What research do you have to analyze?
> - Interview transcripts (text files or paths)
> - Survey responses
> - Support tickets or feedback
> - User observation notes"

Supported formats:
- Plain text files
- Markdown files
- Pasted text
- File paths to read

### Step 2 — Load Context

Read:
- `.shaktra/settings.yml` — project context
- `.shaktra/prd.md` — if exists, for requirement validation
- `.shaktra/memory/decisions.yml` — prior decisions

### Step 3 — Extract Per-Source Findings

For each research input, spawn **product-manager** (mode: research-analyze) to extract:

**Pain Points:**
```yaml
pain_points:
  - id: PP-01
    description: "<what hurts>"
    severity: high | medium | low
    frequency: daily | weekly | monthly | rarely
    quote: "<verbatim if available>"
```

**Feature Requests:**
```yaml
feature_requests:
  - id: FR-01
    description: "<what they want>"
    priority: "<their stated priority>"
    context: "<why they want it>"
```

**Jobs-to-be-Done:**
```yaml
jobs_to_be_done:
  - situation: "When I..."
    motivation: "I want to..."
    outcome: "So I can..."
    current_solution: "<how they do it today>"
```

**Competitor Mentions:**
```yaml
competitor_mentions:
  - name: "<competitor>"
    context: "<what they said>"
    sentiment: positive | negative | neutral
```

**Key Quotes:**
```yaml
key_quotes:
  - quote: "<verbatim>"
    context: "<when/why they said it>"
    theme: "<which theme this supports>"
```

Write each analysis to `.shaktra/research/{interview_id}.yml`.

### Step 4 — Synthesize Findings

After all sources are analyzed, create synthesis:

**Theme Clustering:**
1. Collect all pain points across interviews
2. Group by similarity
3. Name each theme (e.g., "Slow Onboarding", "Confusing Permissions")
4. Calculate evidence count per theme
5. Assign confidence: high (3+ sources), medium (2), low (1 or conflicting)

**Output format:**
```yaml
themes:
  - id: TH-01
    name: "<theme name>"
    description: "<what this theme represents>"
    evidence_count: 4
    confidence: high
    supporting_interviews:
      - id: INT-001
        pain_point_id: PP-01
```

**Pattern Identification:**
```yaml
patterns:
  - name: "<behavioral pattern>"
    description: "<observed behavior>"
    frequency: common | occasional | rare
    evidence:
      - interview_id: INT-001
        observation: "<specific observation>"
```

**Recommendations:**
```yaml
recommendations:
  - id: REC-01
    recommendation: "<actionable recommendation>"
    rationale: "<why this matters>"
    priority: high | medium | low
    supporting_themes: [TH-01, TH-02]
    confidence: high | medium | low
```

Write synthesis to `.shaktra/research/synthesis.yml`.

### Step 5 — Validate Against PRD (If Exists)

If `.shaktra/prd.md` exists:
1. Map themes to PRD requirements
2. Identify:
   - Requirements validated by research (strong evidence)
   - Requirements with no research support (assumptions)
   - User needs not in PRD (potential gaps)
3. Report findings to user

### Step 6 — Identify Research Gaps

```yaml
gaps:
  - area: "<topic needing more research>"
    reason: "<why we need more data>"
    suggested_method: interview | survey | analytics | observation
```

### Step 7 — Present Summary

```
## Research Analysis Complete

**Sources Analyzed:** {count} interviews, {count} surveys, {count} other
**Themes Identified:** {count}
**Recommendations:** {count}

### Top Pain Points (by frequency)
1. {pain point} — {severity}, mentioned by {count} participants
2. {pain point}
3. {pain point}

### Themes
| Theme | Confidence | Evidence |
|---|---|---|
| {theme} | {confidence} | {count} sources |

### Top Recommendations
1. {recommendation} — {priority} priority
2. {recommendation}
3. {recommendation}

### Research Gaps
- {gap area} — suggested: {method}

### Files Created
- .shaktra/research/{id}.yml (x{count})
- .shaktra/research/synthesis.yml

### Next Steps
1. Run `/shaktra:pm personas` to create personas from this research
2. Review gaps and plan additional research if needed
3. Update PRD with validated insights: `/shaktra:pm prd`
```

EMIT `RESEARCH_SYNTHESIZED`

---

## Quality Checklist

| Check | Required |
|---|---|
| Each interview has at least 1 pain point | Yes |
| Each interview has at least 1 JTBD | Yes |
| Synthesis has at least 2 themes | Yes |
| Confidence levels match evidence criteria | Yes |
| At least 1 recommendation generated | Yes |

---

## Integration Notes

**Personas:** Research provides evidence for personas. Each persona's `evidence` section references interview IDs from this analysis.

**PRD:** Research validates or challenges PRD requirements. High-confidence themes should map to "Must Have" requirements.

**Journey Maps:** Pain points and JTBD from research inform journey stage details.
