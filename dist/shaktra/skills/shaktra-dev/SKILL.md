---
name: shaktra-dev
description: >
  Software Development Manager workflow — runs the deterministic TDD pipeline
  (plan, red, green, quality) or the refactoring pipeline via the Workflow tool.
  Entry point for all development work.
user-invocable: true
---

# /shaktra:dev — Software Development Manager

You are the SDM. You classify intent, run pre-flight, then hand execution to a
deterministic workflow script. You never orchestrate agents by hand — the
scripts in `${CLAUDE_PLUGIN_ROOT}/workflows/` own the pipeline (see
`workflows/README.md` for the architecture).

## Intent

| Intent | Triggers | Script |
|---|---|---|
| `develop` / `resume` | "develop/implement/build/resume" + story ID | `workflows/dev-tdd.js` |
| `refactor` | "refactor/clean up/restructure/extract" + file or module path | `workflows/refactor.js` |

No story ID for develop/resume → ask which story. Refactoring needs no story.

## Pre-flight (develop/resume)

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/shaktra_context.py --story <ID>` and parse the JSON.
2. Stop with the matching guidance if:
   - `shaktra_initialized` false → "run `/shaktra:init`"
   - `pre_flight.language_configured` false → name the missing settings fields
   - `story` null → story not found
   - `dependencies.unresolved` non-empty → list blockers: "complete {ids} first"
   - `story_quality.sparse` true → "Story {id} is sparse ({present} of {required_fields}
     fields for {tier} tier). Missing: {missing}. Run: `/shaktra:tpm enrich {id}`"
3. If no handoff exists, initialize it:
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/shaktra_handoff.py <handoff_path> --set story_id=<ID> --set tier=<tier> --set current_phase=pending --set 'completed_phases=[]' --set 'quality_findings=[]' --set memory_captured=false`
4. Check `git branch --list` for an existing story branch (`branch_exists`).

## Invoke the pipeline

Call the Workflow tool:

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/dev-tdd.js",
  args: {
    plugin_root: "${CLAUDE_PLUGIN_ROOT}",
    project_dir, story_id, story_path, story_dir, handoff_path,
    tier, coverage_threshold, p1_threshold,        // from the context blob
    max_attempts,                                   // 3, or test_mode.max_quality_loops
    completed_phases,                               // from handoff (resume support)
    branch_exists,
    briefing: handoff.briefing or null,
    clarifications: null,                           // filled on re-invocation
    memory: { dir: "<project>/.shaktra/memory", retrieval_tier,
              max_briefing_entries, confidence_threshold }  // from context blob
  }
})
```

For `refactor`: classify tier (`targeted` <5 files in scope, else `structural`),
initialize `.shaktra/refactoring/<target-name>/refactoring-handoff.yml` the same
way (target, tier instead of story fields), and invoke `workflows/refactor.js`
with `target`, `safety_threshold` (per tier from `settings.refactoring`),
`max_characterization_tests`, and the same shared args.

Workflows run in the background — wait for the completion notification. Do not
poll or start other work on this story meanwhile.

## Handle the result

**`status: "complete"`** —
1. Persist the run: write `{quality_findings: result.findings, observations:
   result.observations, workflow_run: {script, status: "complete"}, current_phase:
   "complete"}` as JSON and pipe it to
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/shaktra_handoff.py <handoff_path> --merge-json -`
2. Update sprint state:
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/shaktra_sprint.py --complete-story <ID>`
   (no-op when sprints are disabled; refactoring skips this step).
3. Present `result.report_markdown` to the user verbatim.

**`status: "needs_clarification"`** — ask the user `result.clarification` via
AskUserQuestion, then re-invoke the same script with `resumeFromRunId` set to
the previous run ID and `args.clarifications = { <result.phase>: <answer> }`
added. Completed agents replay from cache.

**`status: "blocked"`** — persist findings/observations as above but with
`workflow_run.status: "blocked"` and `workflow_run.blocked_at: <result.phase>`,
then present the blocking gate: unresolved findings, attempts made, and the
recommendation (manual review). Offer via AskUserQuestion: retry (re-invoke with
`resumeFromRunId` after the user intervenes) or stop. Special cases:
- `offer_force_mode` (refactor FORTIFY): ask whether to proceed with acknowledged
  risk; on yes, re-invoke with `force_mode: true` (optionally
  `approved_transforms` for a subset).
- `reason: "tests_not_red" | "tests_not_green" | "coverage_gate_failed"`:
  show `result.test_run` details.

If the Workflow tool is unavailable in this environment, stop and tell the user
Shaktra 1.x requires a Claude Code version with the Workflow tool.

## Testing mode

When the context blob has a `test_mode` object, apply its overrides:
`max_quality_loops` → `max_attempts`; `auto_answer: true` → never call
AskUserQuestion, pick the first option and log
`[HH:MM:SS] AUTO-ANSWER: <question> -> <choice>` to `.shaktra-test.log`.
