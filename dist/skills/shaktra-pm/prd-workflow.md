# PRD Creation Workflow

Standalone workflow for creating Product Requirements Documents. Can be invoked directly or as Phase 2 of the full PM workflow.

## Overview

PRD creation follows a structured process: gather context, select template, guide through sections, quality review, and write. The output is a schema-compliant PRD ready for TPM consumption.

---

## Steps

### Step 1 — Load Context

Read:
- `.shaktra/settings.yml` — project type, language, architecture
- `.shaktra/pm/brainstorm.md` — if exists, use as input
- `.shaktra/memory/decisions.yml` — prior decisions
- `.shaktra/research/synthesis.yml` — if exists, for user insights
- `.shaktra/personas/*.yml` — if exist, for user references

### Step 2 — Template Selection

Determine which template to use:

**Use AskUserQuestion tool:**

Ask the user: "Which PRD template fits your feature?"
- **Standard PRD (6-8 weeks)** — Full PRD for complex features requiring design docs
- **One-Page PRD (2-4 weeks)** — Abbreviated PRD for smaller, well-understood features

Wait for user response before proceeding.

**Auto-selection heuristics (if user doesn't specify):**
- Greenfield project → Standard
- Enhancement to existing feature → One-Page
- Multiple external integrations → Standard
- Single-component change → One-Page

Templates are in `templates/prd-standard.md` and `templates/prd-one-page.md`.

### Step 3 — Guided Input

For each PRD section, gather information from the user. Use brainstorm notes as defaults where available.

**Section flow (Standard template):**

1. **Problem Statement**
   - Use brainstorm `problem` section if available
   - Ask for evidence points if not in brainstorm

2. **Users & Personas**
   - Reference existing personas if they exist
   - Otherwise, ask: "Who are the target users?"

3. **Goals & Success Metrics**
   - Ask: "What does success look like? How will you measure it?"
   - Ensure at least one quantifiable metric

4. **Functional Requirements**
   - For each requirement, capture: description, MoSCoW priority, acceptance test
   - Start with "Must Have" — what's blocking launch?
   - Then "Should Have" — important but not blocking
   - Then "Could Have" — nice to have
   - Finally "Won't Have" — explicit exclusions

5. **Non-Functional Requirements**
   - Ask about: performance, scalability, reliability, security
   - Only include what's relevant — don't force all categories

6. **Scope**
   - Explicitly state in-scope and out-of-scope
   - Use brainstorm `opportunity.out_of_scope` if available

7. **Assumptions & Constraints**
   - Technical, business, timeline, resource constraints
   - Assumptions that, if wrong, would change the approach

8. **Risks & Mitigations**
   - Identify top 3-5 risks
   - For each: likelihood, impact, mitigation strategy

9. **Dependencies** (optional)
   - External teams, systems, decisions needed

10. **Timeline** (optional)
    - High-level milestones only — not sprint-level

### Step 4 — Generate PRD

Spawn **product-manager** (mode: prd-create) with:
- Gathered inputs
- Selected template
- Settings context

PM generates the PRD following the template structure.

### Step 5 — Quality Review

Run quality loop:

```
attempt = 0
max_attempts = 3

WHILE attempt < max_attempts:
  attempt += 1

  # Review against schema rules
  findings = review_against_prd_schema()

  IF no findings:
    EMIT QUALITY_PASS
    BREAK

  # Fix findings
  FOR each finding:
    IF fixable by PM:
      auto_fix(finding)
    ELSE:
      collect_user_input(finding)

  CONTINUE

IF attempt == max_attempts AND findings remain:
  EMIT MAX_LOOPS_REACHED
  present_findings_to_user()
```

**Schema validation rules:**
| Rule | Severity |
|---|---|
| All "must" requirements have acceptance_test | P0 |
| At least one measurable success metric | P0 |
| Problem statement defines target user | P1 |
| Every requirement has unique ID | P1 |
| Scope has both in-scope and out-of-scope | P1 |

### Step 6 — Write PRD

Write the approved PRD to `.shaktra/prd.md`.

If a PRD already exists:
- Ask user: "PRD already exists. Replace or create new version?"
- If replace: overwrite
- If new version: increment version in frontmatter, archive old version

EMIT `PRD_COMPLETE`

### Step 7 — Present for Approval (Full Workflow Only)

If running as part of full workflow:
- Present PRD summary to user
- Wait for explicit approval
- EMIT `PRD_APPROVED` on approval

If standalone:
- Present PRD summary
- Recommend next step: `/shaktra:tpm` for design and stories

---

## Completion Report

```
## PRD Created

**File:** .shaktra/prd.md
**Template:** {standard | one-page}
**Status:** {draft | approved}

### Summary
- **Problem:** {1-line problem statement}
- **Users:** {primary user segment}
- **Requirements:** {count must} must, {count should} should, {count could} could

### Quality
- Review iterations: {count}
- Final status: PASS

### Validation Warnings
- {any P1 findings accepted by user}

### Next Steps
1. Review .shaktra/prd.md and refine as needed
2. Run `/shaktra:tpm` to create design docs and stories
```

---

## PRD Updates

To update an existing PRD:

1. User invokes `/shaktra:pm prd` with existing PRD
2. Detect existing PRD at `.shaktra/prd.md`
3. Ask: "Update existing PRD or create from scratch?"
4. If update:
   - Load current PRD
   - Ask which sections to modify
   - Apply changes, increment version
   - Re-run quality review
5. Write updated PRD

---

## Integration with TPM

The TPM workflow (`/shaktra:tpm`) consumes the PRD:

- Reads `.shaktra/prd.md` as input
- Architect uses PRD for design context
- PM uses PRD for gap answering and coverage analysis
- Stories reference PRD requirements via `REQ-XXX` IDs

Ensure requirements have stable IDs — changing IDs breaks story references.
