# PM Orchestrated Workflow

Default workflow when you describe what you want to build. Guides the complete product definition process with user approval gates.

## Two Paths

Based on whether you have existing research:

| Path | When to Use | Flow |
|---|---|---|
| **Research-First** | Have interviews, surveys, user feedback | Research → Personas → Journeys → PRD |
| **Hypothesis-First** | Starting fresh, no research yet | Brainstorm → Personas → Journeys → PRD |

Both paths end with PRD creation that incorporates persona and journey insights.

---

## Phase 0 — Triage

**Purpose:** Determine which path to take.

### Steps

1. Read `.shaktra/settings.yml` for project context

2. **Collect user input:**
   - If user provided a **file path** → read the document
   - If user provided **inline description** → note it
   - If **no input** → ask: "What would you like to build? Describe it or provide a path to your notes."

3. **Ask about research:**
   > "Do you have existing user research to work from?
   > - Interview transcripts, survey responses, support tickets, user feedback
   >
   > If your document contains research data, let me know."

4. **Route based on answer:**
   - **Has research** → execute `full-workflow-research.md`
   - **No research** → execute `full-workflow-hypothesis.md`

---

## Shared Phases (Both Paths)

After path-specific phases complete, both paths continue with:

### PRD Creation (Final Phase in Both Paths)

PRD is created LAST, after personas and journeys, so it incorporates:
- Persona goals and frustrations → requirements
- Journey pain points → requirements
- Journey opportunities → potential features
- Moments of truth → acceptance criteria

### Prioritization (If Stories Exist)

1. Check `.shaktra/stories/` for existing stories
2. If stories exist: spawn PM (mode: rice), score and classify
3. If no stories: skip — user runs `/shaktra:tpm` first

### Memory Capture (Mandatory)

1. Spawn **memory-curator** with workflow artifacts
2. Append lessons to `.shaktra/memory/lessons.yml`

---

## Completion Report

```
## PM Workflow Complete

**Path:** {Research-First | Hypothesis-First}

### Artifacts Created
- Research: {count} sources (or "skipped")
- Personas: {count}, evidence quality: {high | medium | low}
- Journeys: {count}, {N} opportunities identified
- PRD: .shaktra/prd.md (approved)

### What Flowed Into PRD
- {N} persona goals → requirements
- {N} journey pain points → requirements
- {N} journey opportunities → considered

### Prioritization
- Skipped — no stories exist yet (stories created by TPM)
- Run `/shaktra:pm prioritize` after TPM creates stories

### Next Steps
1. `/shaktra:tpm` to create design docs and stories
2. `/shaktra:pm prioritize` to score and classify stories (after TPM)
```

---

## Error Handling

**User cancellation:** Preserve artifacts, report progress, user can resume with individual commands.

**Quality loop exhaustion:** Present findings, ask user to resolve, don't proceed until addressed.

**Missing prerequisites:** Warn, offer alternatives, or pause for user input.
