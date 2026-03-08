# Deep Analysis Workflow — Team-Based Execution

Reference file for `/shaktra:analyze` deep mode. When agent teams are available, the orchestrator delegates to this workflow. Produces the same artifact schemas as standard mode, with richer data from dedicated team member sessions and cross-cutting correlations.

**Used by:** shaktra-analyze SKILL.md (deep mode delegation).
**Prerequisites:** Agent teams available, Stage 1 (static.yml + overview.yml) complete, settings loaded.

---

## File Ownership Map

Each artifact has exactly one writer. Zero conflicts.

| File | Owner | Read By |
|---|---|---|
| `static.yml` | Lead (Stage 1) | All TMs |
| `overview.yml` | Lead (Stage 1) | All TMs |
| `structure.yml` | TM-1 | — |
| `dependencies.yml` | TM-1 | — |
| `git-intelligence.yml` | TM-1 | TM-3 |
| `domain-model.yml` | TM-2 | — |
| `entry-points.yml` | TM-2 | — |
| `tech-debt.yml` | TM-3 | — |
| `critical-paths.yml` | TM-3 | — |
| `practices.yml` | TM-4 | — |
| `data-flows.yml` | TM-4 | — |
| `manifest.yml` | Lead (Stage 3) | — |
| `checksum.yml` | Lead (Stage 3) | — |
| `tm{N}-summary.md` | TM-{N} | Lead |

---

## Stage 2: Spawn Team (4 Members)

Before constructing prompts, replace ALL `{variables}` with actual values:
- `{project_root}` → the absolute path to the project root (e.g., `/Users/user/my-project`)
- `{skill_directory}` → the absolute path to this skill's directory (the directory containing SKILL.md)

Subagents cannot resolve variables — every path must be a concrete absolute path.

### Team Setup Sequence

1. **Create the team** — use TeamCreate (already discovered via ToolSearch in SKILL.md Step 4a):
   ```
   TeamCreate(team_name: "shaktra-analyze", description: "Deep codebase analysis — 4 team members analyzing 9 dimensions")
   ```

2. **Create 4 tasks** — use TaskCreate (the `subject` parameter is the task title):
   - `subject: "TM-1: Analyze D1 Architecture, D5 Dependencies, D9 Git Intelligence"`
   - `subject: "TM-2: Analyze D2 Domain Model, D3 Entry Points + error propagation correlation"`
   - `subject: "TM-3: Analyze D6 Tech Debt, D8 Critical Paths + cross-cutting risk correlation"`
   - `subject: "TM-4: Analyze D4 Practices, D7 Data Flows + test intelligence correlation"`

3. **Spawn 4 teammates** — use the Agent tool with `team_name: "shaktra-analyze"` and a `name` for each (e.g., `name: "tm-1-structure"`). Spawn all 4 in the same message for parallel execution. Use the prompt templates below for each teammate's prompt.

4. **Assign tasks** — use TaskUpdate with `owner` set to the teammate's name.

5. **Wait for completion** — teammates send messages when done. After all 4 complete, proceed to Stage 3.

### TM-1: "structure" — D1, D5, D9

**Dimensions:** D1 Architecture & Structure, D5 Dependencies & Tech Stack, D9 Git Intelligence
**Writes:** `structure.yml`, `dependencies.yml`, `git-intelligence.yml`, `tm1-summary.md`

**Prompt template:**
```
You are Team Member 1: "structure" for Shaktra deep codebase analysis.

CONTEXT:
- Pre-analysis ground truth: {project_root}/.shaktra/analysis/static.yml
- Project context: {project_root}/.shaktra/analysis/overview.yml
- Memory (if exists): {project_root}/.shaktra/memory/principles.yml, anti-patterns.yml, procedures.yml

DIMENSION SPECS (read the relevant sections):
- D1: {skill_directory}/analysis-dimensions-core.md → section "D1: Architecture & Structure"
- D5: {skill_directory}/analysis-dimensions-health.md → section "D5: Dependencies & Tech Stack"
- D9: {skill_directory}/analysis-dimensions-git.md → section "D9: Git Intelligence"

OUTPUT SCHEMAS: {skill_directory}/analysis-output-schemas.md

YOUR OUTPUT FILES (write to {project_root}/.shaktra/analysis/):
- structure.yml (D1)
- dependencies.yml (D5)
- git-intelligence.yml (D9)

INSTRUCTIONS:
1. Read static.yml and overview.yml for ground truth
2. Spawn 3 CBA Analyzer subagents in parallel — one per dimension. Each subagent prompt must include the full paths above for its dimension spec, output schema, and output file.
3. After all complete, validate: every artifact has summary: within budget, all findings cite evidence from actual files
4. Write tm1-summary.md to {project_root}/.shaktra/analysis/ — max 500 words
   Key findings, structural risks, git intelligence highlights

DO NOT: Write to files owned by other TMs. Modify static.yml or overview.yml. Fabricate file paths or evidence.
```

### TM-2: "domain" — D2, D3 + error propagation correlation

**Dimensions:** D2 Domain Model & Business Rules, D3 Entry Points & Interfaces
**Writes:** `domain-model.yml`, `entry-points.yml`, `tm2-summary.md`

**Prompt template:**
```
You are Team Member 2: "domain" for Shaktra deep codebase analysis.

CONTEXT:
- Pre-analysis ground truth: {project_root}/.shaktra/analysis/static.yml
- Project context: {project_root}/.shaktra/analysis/overview.yml
- Memory (if exists): {project_root}/.shaktra/memory/principles.yml, anti-patterns.yml, procedures.yml

DIMENSION SPECS (read the relevant sections):
- D2: {skill_directory}/analysis-dimensions-core.md → section "D2: Domain Model & Business Rules"
- D3: {skill_directory}/analysis-dimensions-core.md → section "D3: Entry Points & Interfaces"

OUTPUT SCHEMAS: {skill_directory}/analysis-output-schemas.md

YOUR OUTPUT FILES (write to {project_root}/.shaktra/analysis/):
- domain-model.yml (D2)
- entry-points.yml (D3)

INSTRUCTIONS:
1. Read static.yml and overview.yml for ground truth
2. Spawn 2 CBA Analyzer subagents in parallel — D2 and D3. Each subagent prompt must include the full paths above.
3. After both complete, run correlation: trace error propagation paths across D2 (domain logic errors) and D3 (entry point error responses). Enrich domain-model.yml error_propagation section with cross-referenced paths.
4. Validate: every artifact has summary: within budget, all findings cite evidence from actual files
5. Write tm2-summary.md to {project_root}/.shaktra/analysis/ — max 500 words
   Key entities, state machines, error propagation highlights

DO NOT: Write to files owned by other TMs. Modify static.yml or overview.yml. Fabricate file paths or evidence.
```

### TM-3: "health" — D6, D8 + cross-cutting risk (sequential Agent C)

**Dimensions:** D6 Technical Debt & Security, D8 Critical Paths & Risk
**Writes:** `tech-debt.yml`, `critical-paths.yml`, `tm3-summary.md`

**Sequencing constraint:** Agent C (cross-cutting risk) runs AFTER Agents A (D6) and B (D8) complete. Agent C reads their outputs plus `git-intelligence.yml` if available from TM-1.

**Prompt template:**
```
You are Team Member 3: "health" for Shaktra deep codebase analysis.

CONTEXT:
- Pre-analysis ground truth: {project_root}/.shaktra/analysis/static.yml
- Project context: {project_root}/.shaktra/analysis/overview.yml
- Memory (if exists): {project_root}/.shaktra/memory/principles.yml, anti-patterns.yml, procedures.yml

DIMENSION SPECS (read the relevant sections):
- D6: {skill_directory}/analysis-dimensions-health.md → section "D6: Technical Debt & Security"
- D8: {skill_directory}/analysis-dimensions-health.md → section "D8: Critical Paths & Risk"

OUTPUT SCHEMAS: {skill_directory}/analysis-output-schemas.md

YOUR OUTPUT FILES (write to {project_root}/.shaktra/analysis/):
- tech-debt.yml (D6)
- critical-paths.yml (D8)

INSTRUCTIONS:
1. Read static.yml and overview.yml for ground truth
2. Spawn 2 CBA Analyzer subagents in parallel — D6 and D8. Each subagent prompt must include the full paths above.
3. AFTER both complete, run cross-cutting risk correlation:
   - Read tech-debt.yml (your D6 output)
   - Read critical-paths.yml (your D8 output)
   - Read git-intelligence.yml IF it exists (TM-1 output — proceed without if not ready)
   - For each file on a critical path: combine debt presence, test coverage, change frequency (from git data if available), and coupling into composite_risk
   - Append cross_cutting_risk section to critical-paths.yml details
4. Validate: every artifact has summary: within budget, all findings cite evidence from actual files
5. Write tm3-summary.md to {project_root}/.shaktra/analysis/ — max 500 words
   Health score, top risk files, cross-cutting risk highlights

DO NOT: Write to files owned by other TMs. Modify static.yml or overview.yml. Fabricate file paths or evidence.
```

### TM-4: "practices" — D4, D7 + test intelligence

**Dimensions:** D4 Coding Practices & Conventions, D7 Data Flows & Integration
**Writes:** `practices.yml`, `data-flows.yml`, `tm4-summary.md`

**Prompt template:**
```
You are Team Member 4: "practices" for Shaktra deep codebase analysis.

CONTEXT:
- Pre-analysis ground truth: {project_root}/.shaktra/analysis/static.yml
- Project context: {project_root}/.shaktra/analysis/overview.yml
- Memory (if exists): {project_root}/.shaktra/memory/principles.yml, anti-patterns.yml, procedures.yml

DIMENSION SPECS (read the relevant sections):
- D4: {skill_directory}/analysis-dimensions-core.md → section "D4: Coding Practices & Conventions"
- D7: {skill_directory}/analysis-dimensions-health.md → section "D7: Data Flows & Integration"

OUTPUT SCHEMAS: {skill_directory}/analysis-output-schemas.md

YOUR OUTPUT FILES (write to {project_root}/.shaktra/analysis/):
- practices.yml (D4)
- data-flows.yml (D7)

INSTRUCTIONS:
1. Read static.yml and overview.yml for ground truth
2. Spawn 2 CBA Analyzer subagents in parallel — D4 and D7. Each subagent prompt must include the full paths above.
3. After both complete, run test intelligence correlation: review D4 test patterns alongside data-flows for deeper test quality analysis. Ensure violation_catalog in practices.yml captures all convention deviations found.
4. Validate: every artifact has summary: within budget, all findings cite evidence from actual files
5. Write tm4-summary.md to {project_root}/.shaktra/analysis/ — max 500 words
   Convention health, violation catalog highlights, data flow risks

DO NOT: Write to files owned by other TMs. Modify static.yml or overview.yml. Fabricate file paths or evidence.
```

---

## Stage 3: Aggregate (Lead)

After all 4 team members complete:

1. **Read summaries:** Load `tm1-summary.md` through `tm4-summary.md` (~2000 words total). This is ALL the lead reads from team member output.

2. **Validate artifacts (for each dimension artifact):**
   - **Parse check** — confirm valid YAML
   - **Summary check** — `summary:` is first key with substantive content (not a placeholder)
   - **Schema check** — all required top-level keys from `analysis-output-schemas.md` present
   - **File reference spot-check** — extract 5 random file paths from `details:`, verify each exists with Glob. If >1 fails, mark dimension as `failed`
   - **Evidence density check** — confirm no major section has zero evidence citations
   - If any artifact fails, report which dimensions need re-execution

3. **Fallback cross-cutting risk:** If `critical-paths.yml` does not contain a `cross_cutting_risk` section (TM-3 Agent C may have failed or git data was unavailable), compute it now: read `tech-debt.yml`, `critical-paths.yml`, and `git-intelligence.yml` (if available). Append `cross_cutting_risk` to `critical-paths.yml` under `details:`.

4. **Generate checksums:** Compute SHA256 of all analyzed source files. Map each file to dimensions. Write to `checksum.yml`.

5. **Generate Mermaid diagrams:** Read `structure.yml`, generate architecture diagram, include under `diagrams:` key.

6. **Update manifest:** Set all dimensions to `complete`, record completion timestamp, set `execution_mode: deep`.

After Stage 3 completes, return to SKILL.md and continue with Step 5.

---

## Common Constraints

All team members and their subagents must follow:

- **Write only own files** — see ownership map above
- **Analyze all source files** — use static.yml file inventory as the complete scope, not a subset
- **Evidence required** — every finding must cite file:line, code pattern, or tool output. Minimum 3 evidence citations per analysis category. If fewer exist, cite all and note the limited sample.
- **Summary budgets respected** — per `analysis-output-schemas.md` budget table. Summaries must be substantive and use a significant portion of their budget — thin summaries miss context that downstream agents need.
- **No hallucinated paths** — every file path in output must exist (verify with Glob/Read)
- **Canonical examples are real** — code snippets copied from actual codebase, not generated. Must be 10-40 lines. Never paraphrase or summarize code.
- **Absence is valid** — if a dimension has no findings (e.g., no tests exist), document the absence rather than fabricating content
- **Detect project-specific patterns** — beyond standard conventions, identify patterns unique to this codebase (e.g., lazy loading, fail-closed validation, shared helpers)
- **Cross-file analysis** — compare how different parts of the codebase handle the same concern. Look for duplicated functions across files. Report inconsistencies across directories.
- **Self-check before writing** — verify you analyzed files from multiple directories, canonical examples are real code >10 lines, summaries are substantive, and violation catalogs cover mixed/low consistency areas

## Team Summary Persistence

Team summaries (`tm1-summary.md` through `tm4-summary.md`) persist in `.shaktra/analysis/` after aggregation. They are useful for debugging the analysis process itself and have negligible cost.
