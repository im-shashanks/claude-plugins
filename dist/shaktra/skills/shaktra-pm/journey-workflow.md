# Journey Mapping Workflow

Create customer journey maps that visualize the end-to-end experience for each
persona: stages, touchpoints, emotions, pain points, moments of truth, and
improvement opportunities. Executed by the product-manager agent (journeys
target of `workflows/pm-artifacts.js`).

## Steps

**1 — Load context:** `.shaktra/personas/*.yml` (required — no personas means
the orchestrator should have run the personas target first),
`.shaktra/research-synthesis.md` (pain-point evidence, if present),
`.shaktra/prd.md` (scope).

**2 — Scope:** map the primary journey for each persona (the interaction the
PRD implies — e.g. onboarding, daily workflow, purchase decision). Distinct
journeys for one persona get separate files
(`{persona_id}-onboarding-journey.yml`, `{persona_id}-daily-journey.yml`).

**3 — Map through the 5 phases** — awareness → consideration → acquisition →
service → loyalty — per `journey-schema.md`. Each stage:

- `name`, `phase`
- `touchpoints[]` {channel, description}
- `actions[]`, `thoughts[]`
- `emotions` {valence: positive|neutral|negative|frustrated, intensity, description}
- `pain_points[]` {id JP-NN, description, evidence_id}
- `opportunities[]` {id JO-NN, description, impact: high|medium|low, effort: high|medium|low}

Plus `moments_of_truth[]` {stage, description, success_criteria,
failure_impact} — the critical decision points.

**4 — Link evidence:** pain points and opportunities cite research ids/quotes
where available; mark assumptions explicitly where none exists.

**5 — Prioritize opportunities** across stages:

| Impact | Effort | Classification |
|---|---|---|
| High | Low | Quick Win — prioritize |
| High | High | Big Bet — plan carefully |
| Low | Low | Fill-in — if time permits |
| Low | High | Avoid — deprioritize |

**6 — Validate each journey:** persona ID exists in `.shaktra/personas/`;
stages ≥ `pm.min_journey_stages`; at least 1 moment of truth; every stage has
touchpoints and emotions; pain points reference evidence when research exists.

**7 — Write** each journey to `.shaktra/journeys/{persona_id}-journey.yml`
(create the directory if needed).

**8 — Summarize:** journeys table (persona, title, stage/opportunity counts),
moments of truth, top opportunities with classification, pain points by phase,
files created.

## Integration Notes

- **PRD:** journey pain points validate or expand requirements; moments of
  truth become acceptance criteria.
- **Stories:** opportunities are story candidates — Quick Wins → early sprints.
- **TPM:** journeys inform the design doc's problem statement and goals.
