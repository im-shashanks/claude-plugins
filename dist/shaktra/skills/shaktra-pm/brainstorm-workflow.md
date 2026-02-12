# Brainstorm Workflow

Guided ideation process for exploring the problem space before committing to requirements. Can be used standalone or as Phase 1 of the full PM workflow.

## Overview

Brainstorming produces structured notes that feed into PRD creation. The goal is exploration, not commitment — surface options, identify constraints, and align on opportunity before writing formal requirements.

---

## Steps

### Step 1 — Load Context

Read:
- `.shaktra/settings.yml` — project type, language, architecture
- `.shaktra/memory/decisions.yml` — prior decisions that might constrain options
- `.shaktra/memory/lessons.yml` — past learnings relevant to ideation

### Step 2 — Problem Exploration

Guide the user through problem definition:

**Questions to explore:**
- What problem are we solving?
- Who has this problem? (Be specific — not "users" but "developers who deploy multiple times per day")
- What's the impact of not solving it? (Cost, time, frustration, risk)
- Why is this problem worth solving now? (Market timing, business driver, user demand)

**Output format:**
```yaml
problem:
  statement: "<1-2 sentence problem statement>"
  affected_users: ["<specific user type>", "..."]
  impact:
    - type: "<cost | time | frustration | risk | revenue>"
      description: "<specific impact>"
  urgency:
    driver: "<market | business | user | technical debt>"
    reasoning: "<why now>"
```

### Step 3 — User Needs

Identify and prioritize user needs:

**Questions to explore:**
- Who are the primary users? Secondary users?
- What do they currently do to solve this problem? (Workarounds, competitors)
- What would success look like for them?
- What constraints do they operate under?

**Output format:**
```yaml
users:
  primary:
    description: "<who they are>"
    current_solution: "<how they solve it today>"
    success_looks_like: "<desired outcome>"
  secondary:
    - description: "<who>"
      relationship: "<to primary user>"
```

### Step 4 — Market Context

Understand the competitive and market landscape:

**Questions to explore:**
- How do competitors solve this? What do they miss?
- What trends make this easier or harder to solve?
- Are there constraints (regulatory, technical, business) we must respect?
- What adjacent opportunities might this open?

**Output format:**
```yaml
market:
  competitors:
    - name: "<competitor>"
      approach: "<how they solve it>"
      gaps: ["<what they miss>"]
  trends:
    - trend: "<relevant trend>"
      implication: "<how it affects our approach>"
  constraints:
    - type: "<regulatory | technical | business | resource>"
      description: "<constraint>"
```

### Step 5 — Opportunity Definition

Synthesize into a clear opportunity statement:

**Questions to answer:**
- What's the opportunity?
- What's our unique angle or advantage?
- What's the scope we should target?
- What's explicitly out of scope?

**Output format:**
```yaml
opportunity:
  statement: "<1-2 sentence opportunity statement>"
  unique_angle: "<what we can do that others can't or won't>"
  target_scope: "<what we're aiming to build>"
  out_of_scope: ["<what we're explicitly not doing>"]
```

### Step 6 — Write Brainstorm Notes

Compile all sections into `.shaktra/pm/brainstorm.md`:

```markdown
# Brainstorm Notes

Generated: {date}
Project: {settings.project.name}

## Problem

{problem section}

## Users

{users section}

## Market Context

{market section}

## Opportunity

{opportunity section}

## Open Questions

{list of unresolved questions surfaced during brainstorm}

## Next Steps

- [ ] Create PRD from these notes: `/shaktra:pm prd`
- [ ] Conduct user research to validate assumptions
- [ ] Review with stakeholders
```

### Step 7 — Present Summary

Present a concise summary to user:

```
## Brainstorm Complete

**Problem:** {1-line problem statement}
**Primary Users:** {primary user description}
**Opportunity:** {1-line opportunity statement}

**Key Insights:**
- {top 3 insights from brainstorm}

**Open Questions:**
- {questions that need resolution}

**Output:** .shaktra/pm/brainstorm.md

**Next Step:** Run `/shaktra:pm prd` to create a PRD from these notes.
```

---

## Quality Checklist

Before completing brainstorm, verify:

| Check | Required |
|---|---|
| Problem statement is specific (not "improve X") | Yes |
| At least one primary user identified | Yes |
| Impact quantified or described concretely | Yes |
| Current solutions/workarounds documented | Yes |
| Opportunity statement is actionable | Yes |
| Out-of-scope explicitly stated | Yes |

If any check fails, iterate with user before finalizing.

---

## Standalone vs Full Workflow

**Standalone (`/shaktra:pm brainstorm`):**
- Produces brainstorm notes only
- User decides next step
- Good for early exploration before committing to PRD

**Full workflow (Phase 1):**
- Automatically flows to Phase 2 (PRD) after user confirmation
- Brainstorm notes become PRD input
- More structured handoff
