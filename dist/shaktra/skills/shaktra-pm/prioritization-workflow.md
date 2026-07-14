# Prioritization Workflow

Rank stories/features to guide sprint planning. Three frameworks; the default
comes from `settings.pm.default_framework`. Executed by the product-manager
agent (prioritize target of `workflows/pm-artifacts.js`).

## Inputs

`.shaktra/stories/*.yml` (required), `.shaktra/prd.md` (requirement
priorities), `.shaktra/personas/*.yml` (reach estimation),
`.shaktra/journeys/*.yml` (opportunity cross-reference). Framework choice is
asked in the main loop when not configured.

## Frameworks

**RICE (default):** `RICE = (Reach × Impact × Confidence) / Effort`

| Component | Scoring (1-10) |
|---|---|
| Reach | Users/systems affected: config=2, single feature=5, cross-cutting=9 |
| Impact | Value delivered: minor improvement=2, major pain solved=8 |
| Confidence | Certainty: high=10, medium=7, low=4 |
| Effort | Story points mapped: 1pt=1, 3pt=3, 8pt=8, 13pt=10 |

Output per story: `{story_id, rice_score, components{reach,impact,confidence,effort},
classification, priority}`.

**Weighted scoring:** define criteria with weights summing to 1.0 (suggested:
user_value 0.3, business_value 0.25, technical_feasibility 0.2, risk-inverse
0.15, dependencies 0.1); score each item 1-10 per criterion;
`score = Σ(criterion × weight)`.

**MoSCoW:** Must (launch-blocking → current sprint) · Should (important,
workarounds exist → if capacity) · Could (nice to have → if time) · Won't
(out of scope → backlog or reject).

## Quadrant Classification (RICE and Weighted)

| Quadrant | Criteria | Action |
|---|---|---|
| Quick Win | score > median AND effort ≤ `pm.quick_win_effort_threshold` points | Do first |
| Big Bet | impact ≥ `pm.big_bet_impact_threshold` AND effort ≥ 8 points | Plan carefully |
| Fill-in | low score AND low effort | Do if time |
| Avoid | low score AND high effort | Deprioritize |

## Recommendations & Report

Produce: a sprint-goal suggestion (the theme connecting top items); a
recommended sprint composition (2-3 Quick Wins for momentum, 1 Big Bet if
capacity, fill-ins to round out); deprioritization candidates with reasons.
Report the ranked table, classification summary with point totals, and next
steps (`/shaktra:tpm sprint` to allocate; review Big Bets with stakeholders;
re-prioritize after each sprint).

## Rules

- Each run produces fresh scores — previous scores are not persisted.
  Re-run after new stories, sprint completions, or market changes.
- **Never write `sprints.yml`** — prioritization recommends; the scrummaster
  owns allocation and capacity.
