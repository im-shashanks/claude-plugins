# Prioritization Workflow

Enhanced feature prioritization using RICE scoring, weighted scoring, and MoSCoW classification. Helps decide what to build first based on impact, reach, confidence, and effort.

## Overview

Prioritization ranks existing stories or feature ideas to guide sprint planning. Multiple frameworks available:
- **RICE** (default) — Reach, Impact, Confidence, Effort
- **Weighted Scoring** — Custom criteria with weights
- **MoSCoW** — Must/Should/Could/Won't classification

---

## Steps

### Step 1 — Load Context

Read:
- `.shaktra/settings.yml` — project context, PM settings
- `.shaktra/stories/*.yml` — stories to prioritize (required for RICE)
- `.shaktra/prd.md` — requirement priorities for context
- `.shaktra/personas/*.yml` — user segments for reach estimation
- `.shaktra/journeys/*.yml` — opportunities for cross-reference

### Step 2 — Select Framework

Ask user:

> "Which prioritization framework?
> 1. **RICE** (Recommended) — Reach × Impact × Confidence / Effort
> 2. **Weighted Scoring** — Custom criteria with weights
> 3. **MoSCoW** — Must/Should/Could/Won't classification"

Default: RICE

### Step 3 — Execute Framework

#### Option A: RICE Scoring

For each story, calculate:

| Component | How to Score (1-10) |
|---|---|
| **Reach** | Users/systems affected. Config=2, single feature=5, cross-cutting=9 |
| **Impact** | Value delivered. Minor improvement=2, major pain solved=8 |
| **Confidence** | Certainty of estimates. High=10, medium=7, low=4 |
| **Effort** | Story points mapped. 1pt=1, 3pt=3, 8pt=8, 13pt=10 |

```
RICE = (Reach × Impact × Confidence) / Effort
```

Spawn **product-manager** (mode: rice) with stories directory.

**Output:**
```yaml
stories_ranked:
  - story_id: ST-001
    rice_score: 45.0
    components:
      reach: 7
      impact: 9
      confidence: 8
      effort: 3
    classification: Quick Win
    priority: high
```

#### Option B: Weighted Scoring

Define criteria and weights:

```yaml
criteria:
  - name: user_value
    weight: 0.3
    description: "How much does this help users?"
  - name: business_value
    weight: 0.25
    description: "Revenue/strategic impact"
  - name: technical_feasibility
    weight: 0.2
    description: "How easy to implement?"
  - name: risk
    weight: 0.15
    description: "What's the downside risk? (inverse)"
  - name: dependencies
    weight: 0.1
    description: "Does this unblock other work?"
```

Score each item 1-10 per criterion, multiply by weight, sum.

```
Weighted Score = Σ (criterion_score × weight)
```

#### Option C: MoSCoW Classification

For each story/feature, classify:

| Class | Criteria | Sprint Implication |
|---|---|---|
| **Must** | Launch blocked without it | Include in current sprint |
| **Should** | Important, workarounds exist | Include if capacity allows |
| **Could** | Nice to have | Include only if time |
| **Won't** | Out of scope this release | Backlog or reject |

### Step 4 — Classify Results

For RICE and Weighted Scoring, apply quadrant classification:

| Quadrant | Criteria | Action |
|---|---|---|
| **Quick Win** | High score (> median) AND low effort (≤ 3 points) | Do first |
| **Big Bet** | High impact (≥ 7) AND high effort (≥ 8 points) | Plan carefully |
| **Fill-in** | Low score AND low effort | Do if time |
| **Avoid** | Low score AND high effort | Deprioritize |

### Step 5 — Generate Recommendations

Based on results:

1. **Sprint Goal Suggestion:** Theme that connects top-priority items
2. **Recommended Sprint Composition:**
   - 2-3 Quick Wins for momentum
   - 1 Big Bet for impact (if capacity)
   - Fill-ins to round out capacity
3. **Deprioritization Candidates:** Items to move to backlog or reject

### Step 6 — Present Results

```
## Prioritization Complete

**Framework:** {RICE | Weighted | MoSCoW}
**Items Scored:** {count}

### Top Priority Items
| Rank | Item | Score | Class | Effort |
|---|---|---|---|---|
| 1 | {story_id}: {title} | {score} | Quick Win | {points}pts |
| 2 | {story_id}: {title} | {score} | Big Bet | {points}pts |

### Classification Summary
- **Quick Wins:** {count} ({total points} pts)
- **Big Bets:** {count} ({total points} pts)
- **Fill-ins:** {count} ({total points} pts)
- **Avoid:** {count} ({total points} pts)

### Sprint Goal Suggestion
> "{suggested theme based on top items}"

### Recommended Sprint
1. {Quick Win story} — {points}pts
2. {Quick Win story} — {points}pts
3. {Big Bet story} — {points}pts
**Total:** {points} / {capacity} capacity

### Deprioritize
- {story}: Low impact, high effort — move to backlog
- {story}: Dependencies not ready — defer

### Next Steps
1. Run `/shaktra:tpm sprint` to allocate stories to sprints
2. Review Big Bets with stakeholders before committing
3. Re-prioritize after each sprint: `/shaktra:pm prioritize`
```

---

## Settings Integration

Prioritization reads from `settings.pm`:

```yaml
pm:
  default_framework: rice          # rice | weighted | moscow
  rice_reach_boost_for_personas: 1.2  # Multiply reach if persona-aligned
  quick_win_effort_threshold: 3    # Max points for Quick Win
  big_bet_impact_threshold: 7      # Min impact for Big Bet
```

---

## Re-Prioritization

Prioritization can be run multiple times:
- After new stories are created
- After sprint completion (learnings change confidence)
- After market changes (impact/reach shift)

Each run produces fresh scores — does not persist previous scores.

---

## Integration Notes

**TPM:** Prioritization feeds into sprint planning. TPM's Sprint workflow uses RICE results to allocate stories.

**Scrummaster:** Scrummaster owns `sprints.yml`. Prioritization provides recommendations; scrummaster makes final allocation respecting capacity.
