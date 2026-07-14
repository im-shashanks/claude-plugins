---
name: shaktra-incident
description: >
  Incident Response workflow — post-mortem analysis, operational runbook
  generation, and detection gap assessment for completed bugfixes, run as a
  deterministic workflow. Closes the learning loop from production incident to
  enhanced quality gates.
user-invocable: true
---

# /shaktra:incident — Incident Response

Where `/shaktra:bugfix` answers "what broke and how to fix it," you answer
"what do we learn and how do we prevent it." A bug that reached production
passed every quality gate — understanding why each gate missed it is more
valuable than the fix. The pipeline runs in
`${CLAUDE_PLUGIN_ROOT}/workflows/incident.js`; methodology lives in this skill
directory (`postmortem-methodology.md`, `runbook-template.md`,
`detection-gap-framework.md`, `incident-schema.md`), loaded by the
incident-analyst persona.

## Intent

| Intent | Triggers |
|---|---|
| `post_mortem` | "post-mortem", "retro", "incident review" + bug/story reference |
| `runbook` | "runbook", "playbook", "response procedure" + bug/story reference |
| `detection_gap` | "detection gap", "why didn't we catch" + bug/story reference |

Ambiguous → ask which analysis.

## Pre-flight

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/shaktra_context.py`; stop if
   `shaktra_initialized` is false (→ `/shaktra:init`).
2. Extract the bug ID; locate `.shaktra/stories/diagnosis-<bug_id>.yml`.
   **Missing diagnosis** → stop: "No diagnosis artifact found for {bug_id}.
   Run `/shaktra:bugfix` first, then return here."
3. Resolve the story path and handoff from the diagnosis; ensure
   `.shaktra/incidents/<bug_id>/` exists.

## Invoke

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/incident.js",
  args: {
    plugin_root: "${CLAUDE_PLUGIN_ROOT}", project_dir,
    intent,                                 // post_mortem | runbook | detection_gap
    bug_id, diagnosis_path, story_path, handoff_path,
    incident_dir: "<project>/.shaktra/incidents/<bug_id>",
    auto_detection_gap, runbook_auto_generate,          // settings.incident
    incident_confidence_multiplier, action_item_default_priority,
    memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold }
  }
})
```

Wait for the background completion notification — no polling.

## Handle the result

1. Present `result.report_markdown` verbatim; if
   `result.detection_gaps_found`, call the gaps out prominently — they are the
   highest-value output.
2. Suggest next steps: create stories for action items via `/shaktra:tpm`,
   review detection gaps with the team, store the runbook in team docs.

If the Workflow tool is unavailable, stop: Shaktra 1.x requires a Claude Code
version with the Workflow tool.

## Testing mode

When the context blob has `test_mode`: never call AskUserQuestion (log
`AUTO-ANSWER` lines to `.shaktra-test.log`).
