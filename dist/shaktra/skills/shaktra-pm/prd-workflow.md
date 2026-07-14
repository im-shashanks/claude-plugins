# PRD Creation Workflow

Create a schema-compliant Product Requirements Document ready for TPM
consumption. Template choice and section input gathering happen in the main
loop (AskUserQuestion); generation and the quality gate run in
`workflows/pm-artifacts.js` (prd target), executed by the product-manager agent.

## Step 1 — Load Context

`.shaktra/pm/brainstorm.md` (input if it exists), `.shaktra/personas/*.yml`,
`.shaktra/journeys/*.yml`, `.shaktra/research-synthesis.md`,
`.shaktra/memory/principles.yml`, `.shaktra/settings.yml`.

## Step 2 — Template Selection (main loop)

Ask via AskUserQuestion: **Standard PRD (6-8 weeks)** — complex features
requiring design docs — or **One-Page PRD (2-4 weeks)** — smaller,
well-understood features. Auto-selection heuristics when the user defers:
greenfield or multiple external integrations → Standard; enhancement or
single-component change → One-Page. Templates: `templates/prd-standard.md`,
`templates/prd-one-page.md`.

## Step 3 — Section Inputs (Standard template order)

Gather per section, defaulting from brainstorm notes where available:

1. **Problem Statement** — brainstorm `problem` + evidence points
2. **Users & Personas** — reference existing personas
3. **Goals & Success Metrics** — at least one quantifiable metric
4. **Functional Requirements** — each with description, MoSCoW priority, and
   acceptance test; work Must → Should → Could → explicit Won't
5. **Non-Functional Requirements** — performance/scalability/reliability/
   security, only where relevant
6. **Scope** — explicit in-scope AND out-of-scope (brainstorm
   `opportunity.out_of_scope`)
7. **Assumptions & Constraints** — the ones that would change the approach if wrong
8. **Risks & Mitigations** — top 3-5 with likelihood/impact/mitigation
9. **Dependencies**, **Timeline** — optional, milestone-level only

## Step 4 — Generate & Gate

The product-manager agent writes `.shaktra/prd.md` from the template and
inputs; every requirement traces to a persona need or journey opportunity.
The PRD then passes the standard quality loop against these rules (findings
needing product decisions escalate to the user):

| Rule | Severity |
|---|---|
| All "must" requirements have acceptance_test | P0 |
| At least one measurable success metric | P0 |
| Problem statement defines the target user | P1 |
| Every requirement has a unique, stable ID | P1 |
| Scope has both in-scope and out-of-scope | P1 |

**Existing PRD:** ask — replace, or new version (increment frontmatter
version, archive the old one)? For updates: ask which sections to modify,
apply, increment version, re-run the quality gate.

## Step 5 — Approval & Report

Present the summary (problem, users, requirement counts by MoSCoW, review
iterations, accepted P1 warnings) and offer the annotatable HTML review. Full
workflow: record explicit approval before continuing to TPM. Standalone:
recommend `/shaktra:tpm` next.

## Integration with TPM

`/shaktra:tpm` reads `.shaktra/prd.md`: the architect for design context, the
PM for gap answering and coverage, stories via `REQ-XXX` ids. Requirement IDs
must stay stable — changing them breaks story references.
