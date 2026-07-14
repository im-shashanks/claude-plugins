---
name: shaktra-bugfix
description: >
  Bug Fix workflow — structured diagnosis followed by TDD remediation.
  Investigates bugs through triage, root cause analysis, and blast radius
  assessment via a deterministic workflow, then routes to the standard TDD
  pipeline for the fix.
user-invocable: true
---

# /shaktra:bugfix — Bug Fix Workflow

You orchestrate the bug fix lifecycle: **investigation** (deterministic
diagnosis workflow) followed by **remediation** (the unchanged `/shaktra:dev`
TDD pipeline). Investigation is detective work — bottom-up, evidence-driven.
A story is always created — even a hotfix runs through the pipeline.
Diagnosis methodology lives in `diagnosis-methodology.md` in this skill
directory (loaded by the bug-diagnostician persona).

## Intent

| Intent | Triggers |
|---|---|
| `bugfix` | "bug", "debug", "diagnose", a bug description, error message, stack trace |
| `diagnose_only` | "just diagnose", "investigate only", "root cause analysis" |

Extract from the request: the symptom, any error context (stack traces, logs),
and scope hints (files, functions).

## Pre-flight

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/shaktra_context.py`; stop if
`shaktra_initialized` is false (→ `/shaktra:init`).

## Invoke

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/bugfix-diagnose.js",
  args: {
    plugin_root: "${CLAUDE_PLUGIN_ROOT}", project_dir,
    bug_description, error_context,        // error_context null if none given
    stories_dir: "<project>/.shaktra/stories",
    memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold }
  }
})
```

Wait for the background completion notification — no polling.

## Handle the result

**`blocked` with `reason: "diagnosis_inconclusive"`** — present what was
attempted (`result.diagnosis.evidence`), then ask the user for additional
context, environment details, or reproduction steps. Never proceed to
remediation without a confirmed root cause. Re-invoke with the enriched
`error_context` once provided.

**`complete`** —
1. Present `result.report_markdown` verbatim.
2. Blast-radius observations (`type: "blast-radius"` in `result.observations`):
   present the affected locations and ask via AskUserQuestion which (if any)
   should become separate stories — create them via
   `Skill(skill: "shaktra-tpm", args: "hotfix <description>")`. They never block
   the current fix.
3. `diagnose_only` intent: stop here with the findings.
4. `bugfix` intent: chain to remediation —
   `Skill(skill: "shaktra-dev", args: "develop story <id from result.story_path>")`.
   The entire TDD pipeline runs unchanged; the diagnosis artifact serves as
   planning context, and the reproduction test from the story's test_specs
   becomes part of RED.

Memory note: diagnosis observations are consolidated by the dev pipeline's
memory capture once remediation completes (workflow_type tdd) — high-value for
anti-pattern detection.

If the Workflow tool is unavailable, stop: Shaktra 1.x requires a Claude Code
version with the Workflow tool.

## Testing mode

When the context blob has `test_mode`: never call AskUserQuestion (skip
blast-radius story creation; log `AUTO-ANSWER` lines to `.shaktra-test.log`).
