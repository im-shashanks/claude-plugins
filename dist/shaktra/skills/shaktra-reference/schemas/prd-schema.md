# PRD Schema

Defines the structure of Product Requirements Documents in `.shaktra/prd.md`. PRDs are the primary input for the TPM workflow and feed into design docs and story creation.

## Schema

```yaml
# .shaktra/prd.md (YAML frontmatter + markdown body)
---
id: string              # required — unique identifier (e.g., "PRD-001")
title: string           # required — product/feature name
version: string         # required — semantic version (e.g., "1.0.0")
status: string          # required — "draft" | "review" | "approved" | "deprecated"
created: date           # required — ISO date (YYYY-MM-DD)
updated: date           # required — last modification date
author: string          # required — primary author
stakeholders:           # required — key decision makers
  - name: string
    role: string
---
```

## Sections

| # | Section | Content | Required |
|---|---|---|---|
| 1 | **Problem Statement** | What problem this solves, who has it, why it matters now | Yes |
| 2 | **Users & Personas** | Target user segments, reference persona IDs if they exist | Yes |
| 3 | **Goals & Success Metrics** | Measurable outcomes, KPIs, target values | Yes |
| 4 | **Functional Requirements** | What the system must do, with MoSCoW priority | Yes |
| 5 | **Non-Functional Requirements** | Performance, security, scalability, reliability constraints | Yes |
| 6 | **Scope** | In-scope and out-of-scope boundaries | Yes |
| 7 | **Assumptions & Constraints** | Business, technical, and timeline constraints | Yes |
| 8 | **Risks & Mitigations** | Known risks with mitigation strategies | Yes |
| 9 | **Dependencies** | External systems, teams, or decisions required | No |
| 10 | **Timeline** | High-level milestones (not sprint-level) | No |

## MoSCoW Priority Levels

All functional and non-functional requirements use MoSCoW classification:

| Priority | Meaning | Implication |
|---|---|---|
| **Must** | Critical for launch — release blocked without it | 100% coverage in stories |
| **Should** | Important but workarounds exist | Included unless capacity constrained |
| **Could** | Nice to have — enhances value | Included only if time permits |
| **Won't** | Explicitly out of scope for this release | Not in current stories |

## Requirement Format

Each requirement in sections 4 and 5 should follow this structure:

```yaml
- id: REQ-001
  description: "<what the system must do>"
  priority: must | should | could | won't
  rationale: "<why this is needed>"
  persona_ids: [P-001, P-002]    # optional — which personas need this
  acceptance_test: "<how to verify this is met>"
```

## Persona References

If personas exist in `.shaktra/personas/`, requirements can reference them by ID. This creates traceability from user needs to requirements to stories.

```yaml
persona_ids: [P-001]  # Links to .shaktra/personas/P-001.yml
```

## Validation Rules

| Rule | Severity |
|---|---|
| All "must" requirements have acceptance_test | P0 |
| At least one measurable success metric exists | P0 |
| Problem statement defines the target user | P1 |
| Every requirement has a unique ID | P1 |
| Scope section has both in-scope and out-of-scope | P1 |

## Storage

PRDs are stored as `.shaktra/prd.md` — a single markdown file with YAML frontmatter. Only one active PRD per project at a time. Archive superseded PRDs to `.shaktra/archive/`.
