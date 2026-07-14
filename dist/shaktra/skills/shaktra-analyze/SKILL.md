---
name: shaktra-analyze
description: >
  Codebase Analyzer workflow — evidence-based analysis across 9 dimensions
  (architecture, domain, interfaces, practices, dependencies, debt, data flows,
  critical paths, git intelligence) run as a deterministic workflow with
  incremental refresh.
user-invocable: true
---

# /shaktra:analyze — Codebase Analyzer

You orchestrate codebase analysis. Everything an agent claims must be grounded
in the Stage-1 ground truth (`static.yml`) — evidence over impressions. The
pipeline runs deterministically in `${CLAUDE_PLUGIN_ROOT}/workflows/analyze.js`;
dimension specifications live in this skill directory
(`analysis-dimensions-core.md`, `analysis-dimensions-health.md`,
`analysis-dimensions-git.md`, `analysis-output-schemas.md`, `debt-strategy.md`,
`dependency-audit.md`).

## Intent

| Intent | Triggers | Workflow args |
|---|---|---|
| `full` | "analyze the codebase", "full analysis" | mode full, all 9 dimensions |
| `targeted` | a dimension by name (see mapping) | mode targeted, that dimension |
| `refresh` | "refresh", "update analysis" | mode targeted, stale dimensions |
| `debt-strategy` | "debt strategy", "prioritize debt" | mode debt-strategy |
| `dependency-audit` | "dependency audit", "upgrade plan" | mode dependency-audit |
| `status` | "analysis status" | no workflow — read manifest.yml and report |

Dimension mapping: architecture/structure→D1 · domain/entities→D2 ·
endpoints/APIs→D3 · practices/conventions→D4 · dependencies/stack→D5 ·
debt/security/health→D6 · data flows/integrations→D7 · critical paths/risk→D8 ·
git history/churn/hotspots→D9. Ambiguous → ask.

## Pre-flight

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/shaktra_context.py`; stop if
   `shaktra_initialized` is false (→ `/shaktra:init`).
2. Read `.shaktra/analysis/manifest.yml`:
   - Incomplete prior run → ask: resume (pass only incomplete dimensions) or
     start fresh (clear artifacts first)?
   - `stage1_complete`: true only when static.yml + overview.yml exist AND
     `checksum.yml` hashes still match the source files (spot-check with Bash);
     stale → false so Stage 1 re-runs.
3. Refresh intent: compare `checksum.yml` hashes against current files, map
   changed files to dimensions (plus D9, always stale), present the stale table,
   and confirm which dimensions to re-run.
4. debt-strategy needs `tech-debt.yml` (else run D6 first); dependency-audit
   needs `dependencies.yml` (else run D5 first).

## Invoke

```
Workflow({
  scriptPath: "${CLAUDE_PLUGIN_ROOT}/workflows/analyze.js",
  args: {
    plugin_root: "${CLAUDE_PLUGIN_ROOT}", project_dir,
    analysis_dir: "<project>/.shaktra/analysis",
    skill_dir: "${CLAUDE_PLUGIN_ROOT}/skills/shaktra-analyze",
    mode, dimensions, stage1_complete,
    summary_token_budget,                 // settings.analysis.summary_token_budget
    memory: { dir, retrieval_tier, max_briefing_entries, confidence_threshold }
  }
})
```

Wait for the background completion notification — no polling.

## Handle the result

1. Present `result.report_markdown` verbatim; list `result.failed_dimensions`
   prominently if any (offer a re-run of just those).
2. **Architecture back-fill** from `result.architecture_note`: if
   `settings.project.architecture` is empty and a single dominant style was
   detected with high consistency, update `.shaktra/settings.yml` and say so;
   if consistency is mixed/low, ask the user which target style to set; if
   already set but conflicting, report the mismatch as a finding.
3. Offer an annotatable HTML review of the analysis report via AskUserQuestion;
   on yes, invoke the `shaktra-html-review` skill with the report content.
4. For debt-strategy / dependency-audit: remind the user the generated stories
   feed `/shaktra:tpm` for sprint planning.

If the Workflow tool is unavailable, stop: Shaktra 1.x requires a Claude Code
version with the Workflow tool.

## Testing mode

When the context blob has `test_mode`: never call AskUserQuestion (auto-select:
resume→fresh, stale→re-run all; log `AUTO-ANSWER` lines to `.shaktra-test.log`);
skip the HTML review offer.
