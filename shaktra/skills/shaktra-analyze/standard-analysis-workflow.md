# Standard Analysis Workflow — Single-Session Execution

Reference file for `/shaktra:analyze` standard mode. When agent teams are NOT
available, the orchestrator delegates Stages 2-4 to this workflow. Produces the
same artifact schemas as deep mode, using parallel CBA Analyzer agents within a
single session.

**Used by:** shaktra-analyze SKILL.md (standard mode delegation).
**Prerequisites:** Stage 1 (static.yml + overview.yml) complete, settings loaded.

---

## Stage 2: Parallel Deep Dimensions

Spawn **9 CBA Analyzer agents** in parallel. Each receives its dimension specification from the analysis dimensions files, plus:

- Path to `static.yml` (ground truth input)
- Path to `overview.yml` (project context)
- Path to `.shaktra/memory/decisions.yml` (if exists)

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

**CBA Analyzer prompt template:**

```
You are the shaktra-cba-analyzer agent. Execute analysis dimension {dimension_id}.

Dimension: {dimension_name}
Static data: .shaktra/analysis/static.yml
Overview: .shaktra/analysis/overview.yml
Decisions: .shaktra/memory/decisions.yml
Output path: .shaktra/analysis/{output_file}

Read your dimension specification from analysis-dimensions-core.md (D1-D4), analysis-dimensions-health.md (D5-D8), or analysis-dimensions-git.md (D9).
Follow the output schema from analysis-output-schemas.md for your artifact format.
Follow the checks, evidence requirements, and output schema for dimension {dimension_id}. Ground all findings in static.yml data where possible.

Your output file MUST begin with a summary: section (300-600 tokens, self-contained).
```

After each agent completes, update `manifest.yml` with that dimension's completion state.

---

## Stage 3: Finalize

**3a. Validate artifacts:**
- Read each output file in `.shaktra/analysis/`
- Verify every artifact (except static, manifest, checksum) has a `summary:` key at the top level
- If any artifact is missing or malformed, report which dimensions need re-execution

**3b. Cross-cutting risk correlation:**
- Read `tech-debt.yml`, `critical-paths.yml`, and `git-intelligence.yml`
- If `critical-paths.yml` does not already contain a `cross_cutting_risk` section (D8 may have produced it), compute it: for each file on a critical path, combine debt presence (D6), test coverage (D6), change frequency (D9), and coupling to produce a composite risk score
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
- Set all stages/dimensions to `complete`
- Record completion timestamp
- Record analysis version (from plugin.json)

---

## Stage 4: Memory Capture

Spawn **shaktra-memory-curator**:
```
You are the shaktra-memory-curator agent. Capture lessons from the completed analysis workflow.

Workflow type: analysis
Artifacts path: .shaktra/analysis/

Extract lessons that meet the capture bar. Append to .shaktra/memory/lessons.yml.
```
