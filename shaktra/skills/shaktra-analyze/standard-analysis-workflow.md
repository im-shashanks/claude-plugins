# Standard Analysis Workflow — Single-Session Execution

Reference file for `/shaktra:analyze` standard mode. When agent teams are NOT
available, the orchestrator delegates to this workflow. Produces the same artifact
schemas as deep mode, using parallel CBA Analyzer agents within a single session.

**Used by:** shaktra-analyze SKILL.md (standard mode delegation).
**Prerequisites:** Stage 1 (static.yml + overview.yml) complete, settings loaded.

---

## Stage 2: Parallel Deep Dimensions

Spawn **9 CBA Analyzer agents** in parallel — one per dimension. Each receives its dimension specification, ground truth inputs, and output target.

**Dispatch all 9 dimensions simultaneously:**

```
D1: Architecture & Structure        → .shaktra/analysis/structure.yml
D2: Domain Model & Business Rules   → .shaktra/analysis/domain-model.yml
D3: Entry Points & Interfaces       → .shaktra/analysis/entry-points.yml
D4: Coding Practices & Conventions  → .shaktra/analysis/practices.yml
D5: Dependencies & Tech Stack       → .shaktra/analysis/dependencies.yml
D6: Technical Debt & Security       → .shaktra/analysis/tech-debt.yml
D7: Data Flows & Integration        → .shaktra/analysis/data-flows.yml
D8: Critical Paths & Risk           → .shaktra/analysis/critical-paths.yml
D9: Git Intelligence                → .shaktra/analysis/git-intelligence.yml
```

### CBA Analyzer Prompt Template

For each dimension, construct the prompt below. Replace all `{variables}` with actual values — subagents cannot resolve them.

```
You are the shaktra-cba-analyzer agent. Execute analysis dimension {dimension_id}: {dimension_name}.

INPUTS (read these first):
- Pre-analysis ground truth: {project_root}/.shaktra/analysis/static.yml
- Project context: {project_root}/.shaktra/analysis/overview.yml
- Project principles (if exists): {project_root}/.shaktra/memory/principles.yml

YOUR DIMENSION SPECIFICATION:
- Read: {skill_directory}/{dimension_spec_file}
  (D1-D4: analysis-dimensions-core.md, D5-D8: analysis-dimensions-health.md, D9: analysis-dimensions-git.md)
- Find the section for {dimension_id} and follow its analysis steps, evidence requirements, and output structure exactly.

OUTPUT FORMAT:
- Read: {skill_directory}/analysis-output-schemas.md — your artifact must match the schema for {output_file}.
- Your output file MUST begin with a summary: section (see budget table in schemas file).
- The summary must be self-contained — readable without any other file.

OUTPUT PATH: {project_root}/.shaktra/analysis/{output_file}

CRITICAL RULES:
- Analyze ALL source files listed in static.yml — do not limit to a single directory.
- Every finding must cite evidence: file path, line number, code pattern, or tool output.
- If you cannot find evidence for a finding, omit it. Never fabricate file paths or line numbers.
- Code snippets in output must be copied from the actual codebase, not generated.
- Verify every file path you reference exists (use Glob or Read to confirm).
- If the codebase lacks sufficient content for a dimension (e.g., no tests for D4 test patterns), report what's absent rather than guessing.
- Look for project-specific patterns beyond standard language conventions — these are often the most valuable findings.

EVIDENCE THRESHOLDS:
- Each practice area (D4) or analysis category must have at least 3 evidence citations. If fewer exist in the codebase, cite all available and note the limited sample.
- Canonical examples (D4) must be 10-40 lines of real code. Never summarize or paraphrase — copy the actual code.
- Violation catalog entries must reference both the canonical pattern and the deviating file:line.

CROSS-FILE ANALYSIS:
- Actively look for duplicated functions or utilities across files (e.g., same helper function copy-pasted into multiple modules). Report these as code duplication findings.
- Compare how different parts of the codebase handle the same concern (error handling, logging, config loading). Inconsistencies across directories are findings, not noise.
- Check whether project-specific patterns (e.g., shared utilities, custom base classes) are used consistently everywhere or only in some areas.

SELF-CHECK BEFORE WRITING:
- Verify you analyzed files from multiple directories (not just one top-level folder).
- Confirm every canonical example snippet is >10 lines of real code copied from the codebase.
- Check that your summary uses a substantial portion of its token budget — thin summaries miss important context that downstream agents need.
- For D4: verify violation_catalog has entries for any area with mixed or low consistency.
```

### Dimension Spec File Mapping

| Dimensions | Spec File |
|---|---|
| D1, D2, D3, D4 | `analysis-dimensions-core.md` |
| D5, D6, D7, D8 | `analysis-dimensions-health.md` |
| D9 | `analysis-dimensions-git.md` |

After each agent completes, update `manifest.yml` with that dimension's completion state. If an agent fails, record `status: failed` and `error:` in the manifest — do not retry automatically.

---

## Stage 3: Finalize

**3a. Validate artifacts (for each dimension artifact):**

1. **Parse check** — Read the file and confirm it is valid YAML. If it fails to parse, mark the dimension as `failed` in the manifest.
2. **Summary check** — Confirm `summary:` is the first top-level key and contains substantive content (not a placeholder or single sentence). A good summary is self-contained — someone reading only the summary should understand the key findings without opening `details:`.
3. **Schema check** — Verify all required top-level keys from `analysis-output-schemas.md` are present. Missing sections indicate incomplete analysis.
4. **File reference spot-check** — Extract 5 random file paths from the artifact's `details:` section. Use Glob to verify each path exists in the project. If more than 1 of 5 fails, the artifact likely contains hallucinated paths — mark as `failed`.
5. **Evidence density check** — Scan `details:` for `file:`, `location:`, `evidence:` fields. If any major section has zero evidence citations, flag for re-execution.
6. If any artifact fails validation, set its manifest status to `failed` with `error:` describing what failed. Do not proceed with cross-cutting correlation until all required inputs pass.

**3b. Cross-cutting risk correlation:**
- Read `tech-debt.yml`, `critical-paths.yml`, and `git-intelligence.yml`
- If `critical-paths.yml` does not already contain a `cross_cutting_risk` section, compute it: for each file on a critical path, combine debt presence (D6), test coverage (D6), change frequency (D9), and coupling to produce a composite risk score
- Append `cross_cutting_risk` to `critical-paths.yml` under `details:`

**3c. Generate checksums:**
- Compute SHA256 of all analyzed source files (from static.yml file inventory)
- Map each file to the dimensions it was analyzed by
- Write to `.shaktra/analysis/checksum.yml`

**3d. Generate Mermaid diagrams:**
- Read `structure.yml` for module relationships
- Generate architecture diagram showing module dependencies and boundaries
- Include in `structure.yml` under a `diagrams:` key

**3e. Update manifest:**
- Set all successfully completed stages/dimensions to `complete`
- Record completion timestamp
- Record analysis version (from plugin.json)
- Set `execution_mode: standard`

After Stage 3 completes, return to SKILL.md and continue with Step 5.
