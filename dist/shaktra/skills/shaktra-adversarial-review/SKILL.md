---
name: shaktra-adversarial-review
description: >
  Adversarial Review workflow — treats code changes as behavioral hypotheses and
  systematically falsifies them through mutation testing, adversarial inputs, and
  fault injection. Produces an execution-based risk assessment via a
  deterministic workflow.
user-invocable: true
---

# /shaktra:adversarial-review — Adversarial Review

You orchestrate an adversarial pass over a change set: does the test suite
actually kill bugs, and does the code survive hostile inputs and failing
dependencies? The pipeline runs deterministically in
`${CLAUDE_PLUGIN_ROOT}/workflows/adversarial.js`; the adversary persona and its
strategy files (`mutation-strategy.md`, `probe-strategies.md` in this skill
directory) do the domain work.

## Intent

| Intent | Triggers |
|---|---|
| `story-adversarial` | "adversarial review ST-…", story ID reference |
| `pr-adversarial` | "adversarial review PR", "#<number>", PR URL |

Ambiguous → ask which mode.

## Pre-flight

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/shaktra_context.py [--story <ID>]`.
   Stop if `shaktra_initialized` is false (→ `/shaktra:init`).
2. Read thresholds from `settings.adversarial_review` (defaults if the section is
   missing — tell the user defaults are in use): `mutation_kill_threshold` 80,
   `mutation_timeout` 30, `max_mutations_per_function` 5,
   `max_adversarial_tests` 20, `test_persistence` ask.
3. **Warn the user before invoking:** mutation testing temporarily modifies
   source files (each mutation is applied, tested, and restored). The working
   tree must be clean enough that `git checkout -- <file>` is a safe restore.
   Confirm before proceeding if there are uncommitted changes in files the
   review will mutate.

## Invoke

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/adversarial.js",
  args: {
    plugin_root: "${CLAUDE_PLUGIN_ROOT}", project_dir,
    mode,                                   // story-adversarial | pr-adversarial
    story_id, story_dir, handoff_path, pr_number,
    mutation_kill_threshold, mutation_timeout, max_mutations_per_function,
    max_adversarial_tests, test_persistence,
    p1_threshold,                           // settings.quality.p1_threshold
    memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold }
  }
})
```

Wait for the background completion notification — no polling.

## Handle the result

1. **`status: "blocked"` with `reason: "source_tree_not_restored"`** — a
   mutation may still be applied. Tell the user immediately, show `git status`,
   and help restore before anything else.
2. Story mode: persist findings/observations via
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/shaktra_handoff.py <handoff_path> --merge-json -`
   with `{quality_findings: result.findings, observations: result.observations,
   workflow_run: {script: "adversarial.js", status: "complete"}}`.
3. If `result.test_persistence` is `"ask"`: show the generated adversarial tests
   and ask via AskUserQuestion whether to keep them.
4. Present `result.report_markdown` verbatim. Verdicts:
   `pass` (score ≥ threshold, no P0, P1 within threshold, no blind spots) ·
   `concern` (score below threshold or blind spots — merge with awareness) ·
   `blocked` (P0 findings — fix before merge). A `null` mutation score means no
   existing tests were found; say so explicitly.

If the Workflow tool is unavailable, stop: Shaktra 1.x requires a Claude Code
version with the Workflow tool.

## Testing mode

When the context blob has `test_mode`: never call AskUserQuestion (pick the
first option, log `AUTO-ANSWER` lines to `.shaktra-test.log`), and treat
`test_persistence` as `never`.
