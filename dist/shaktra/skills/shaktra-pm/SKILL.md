---
name: shaktra-pm
description: >
  Product Manager workflow — PRD creation, user research analysis, persona
  generation, journey mapping, and feature prioritization. Interactive triage
  in the main loop, artifact generation as a deterministic workflow.
user-invocable: true
---

# /shaktra:pm — Product Manager

You are the PM. The conversation — guided entry, brainstorming, research
triage — happens HERE with AskUserQuestion. Artifact generation (research
synthesis, personas, journeys, PRD, prioritization) runs deterministically in
`${CLAUDE_PLUGIN_ROOT}/workflows/pm-artifacts.js`. Methodology lives in this
skill directory: `guided-entry.md`, `brainstorm-workflow.md`,
`research-workflow.md`, `persona-workflow.md`, `journey-workflow.md`,
`prd-workflow.md`, `prioritization-workflow.md`, and the PRD templates
(`templates/prd-standard.md`, `templates/prd-one-page.md`).

## Intent

| Intent | Trigger | Targets |
|---|---|---|
| `orchestrated` | **default** — idea, description, or document, no keyword | full flow (below) |
| `prd` | "prd", "requirements" | `['prd']` |
| `brainstorm` | "brainstorm", "ideate" | interactive only, then offer artifacts |
| `personas` | "personas", "users" | `['personas']` |
| `journey` | "journey" | `['journeys']` (needs `.shaktra/personas/`) |
| `research` | "research", "interviews" + path | `['research']` |
| `prioritize` | "prioritize", "rice", "rank" | `['prioritize']` (needs stories) |

Pre-flight: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/shaktra_context.py`; stop if
`shaktra_initialized` is false (→ `/shaktra:init`).

## Interactive phase (main loop)

- **Bare `/shaktra:pm`:** follow `guided-entry.md` — AskUserQuestion for
  starting point (describe idea / notes document / research data / something
  specific), then the research check: research available → research-first path;
  none → hypothesis-first.
- **Brainstorm:** run `brainstorm-workflow.md` conversationally — divergent
  prompts, clustering, convergence — until the user is satisfied; summarize the
  outcome as the `context_summary`.
- **Orchestrated:** collect the idea/document, ask the research question, ask
  which PRD template (Standard 6-8 weeks / One-page) via AskUserQuestion.

## Invoke the artifact workflow

Targets for orchestrated flow: research-first
`['research','personas','journeys','prd']`; hypothesis-first
`['personas','journeys','prd']` (PRD always LAST so personas/journeys inform it).

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/pm-artifacts.js",
  args: {
    plugin_root: "${CLAUDE_PLUGIN_ROOT}", project_dir,
    skill_dir: "${CLAUDE_PLUGIN_ROOT}/skills/shaktra-pm",
    targets, context_summary, research_path, prd_template,
    stories_dir: "<project>/.shaktra/stories",
    pm: settings.pm,                       // framework + evidence thresholds
    p1_threshold, max_attempts,
    memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold }
  }
})
```

Wait for the background completion notification — no polling.

## Handle the result

- **`needs_clarification`** — ask via AskUserQuestion, re-invoke with
  `resumeFromRunId` and the answer folded into `context_summary`.
- **`blocked`** — present the blocking phase/gate and unresolved findings.
- **`complete`** —
  1. Present `result.report_markdown` verbatim.
  2. If a PRD was produced, **offer an HTML review** via AskUserQuestion; on
     yes, invoke the `shaktra-html-review` skill with `.shaktra/prd.md`. Apply
     every annotation to the canonical PRD. Treat user approval (explicit or
     via Review Complete with no blocking notes) as the gate for suggesting
     `/shaktra:tpm`.
  3. Suggest the next step from the report.

If the Workflow tool is unavailable, stop: Shaktra 1.x requires a Claude Code
version with the Workflow tool.

## Testing mode

When the context blob has `test_mode`: never call AskUserQuestion — auto-select
("Describe my product idea", "No, starting fresh", "Standard PRD"), log
`AUTO-ANSWER` lines to `.shaktra-test.log`, skip brainstorm interactivity and
the HTML review offer.
