# Deep Analysis Workflow — Team-Based Execution

Reference file for `/shaktra:analyze` deep mode. When agent teams are available, the orchestrator delegates Stages 2-4 to this workflow. Produces the same artifact schemas as standard mode, with richer data from dedicated team member sessions.

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

Use TeamCreate to spawn a team of 4 agents simultaneously. Each team member spawns up to 3 subagents for its dimensions.

### TM-1: "structure" — D1, D5, D9

**Dimensions:** D1 Architecture & Structure, D5 Dependencies & Tech Stack, D9 Git Intelligence
**Writes:** `structure.yml`, `dependencies.yml`, `git-intelligence.yml`, `tm1-summary.md`

**Prompt template:**
```
You are Team Member 1: "structure" for Shaktra deep codebase analysis.

CONTEXT:
- Pre-analysis: .shaktra/analysis/static.yml, overview.yml
- Memory (if exists): .shaktra/memory/decisions.yml, lessons.yml
- Dimension specs: analysis-dimensions-core.md (D1), analysis-dimensions-health.md (D5), analysis-dimensions-git.md (D9)
- Output schemas: analysis-output-schemas.md

YOUR DIMENSIONS: D1, D5, D9
YOUR OUTPUT FILES: structure.yml, dependencies.yml, git-intelligence.yml

INSTRUCTIONS:
1. Read static.yml and overview.yml for ground truth
2. Spawn 3 CBA Analyzer subagents in parallel — one per dimension
3. After all complete, validate: every artifact has summary: within budget, all findings cite evidence
4. Write tm1-summary.md to .shaktra/analysis/ — max 500 words
   Key findings, structural risks, git intelligence highlights

DO NOT: Write to files owned by other TMs. Modify static.yml or overview.yml.
```

### TM-2: "domain" — D2, D3 + error propagation correlation

**Dimensions:** D2 Domain Model & Business Rules, D3 Entry Points & Interfaces
**Writes:** `domain-model.yml`, `entry-points.yml`, `tm2-summary.md`

**Prompt template:**
```
You are Team Member 2: "domain" for Shaktra deep codebase analysis.

CONTEXT:
- Pre-analysis: .shaktra/analysis/static.yml, overview.yml
- Memory (if exists): .shaktra/memory/decisions.yml, lessons.yml
- Dimension specs: analysis-dimensions-core.md (D2, D3)
- Output schemas: analysis-output-schemas.md

YOUR DIMENSIONS: D2, D3
YOUR OUTPUT FILES: domain-model.yml, entry-points.yml

INSTRUCTIONS:
1. Read static.yml and overview.yml for ground truth
2. Spawn 2 CBA Analyzer subagents in parallel — D2 and D3
3. After both complete, run correlation: trace error propagation paths across D2 (domain logic errors) and D3 (entry point error responses). Enrich domain-model.yml error_propagation section with cross-referenced paths.
4. Validate: every artifact has summary: within budget, all findings cite evidence
5. Write tm2-summary.md to .shaktra/analysis/ — max 500 words
   Key entities, state machines, error propagation highlights

DO NOT: Write to files owned by other TMs. Modify static.yml or overview.yml.
```

### TM-3: "health" — D6, D8 + cross-cutting risk (sequential Agent C)

**Dimensions:** D6 Technical Debt & Security, D8 Critical Paths & Risk
**Writes:** `tech-debt.yml`, `critical-paths.yml`, `tm3-summary.md`

**Sequencing constraint:** Agent C (cross-cutting risk) runs AFTER Agents A (D6) and B (D8) complete. Agent C reads their outputs plus `git-intelligence.yml` if available from TM-1.

**Prompt template:**
```
You are Team Member 3: "health" for Shaktra deep codebase analysis.

CONTEXT:
- Pre-analysis: .shaktra/analysis/static.yml, overview.yml
- Memory (if exists): .shaktra/memory/decisions.yml, lessons.yml
- Dimension specs: analysis-dimensions-health.md (D6, D8)
- Output schemas: analysis-output-schemas.md

YOUR DIMENSIONS: D6, D8
YOUR OUTPUT FILES: tech-debt.yml, critical-paths.yml

INSTRUCTIONS:
1. Read static.yml and overview.yml for ground truth
2. Spawn 2 CBA Analyzer subagents in parallel — D6 and D8
3. AFTER both complete, run cross-cutting risk correlation:
   - Read tech-debt.yml (your D6 output)
   - Read critical-paths.yml (your D8 output)
   - Read git-intelligence.yml IF it exists (TM-1 output — proceed without if not ready)
   - For each file on a critical path: combine debt presence, test coverage, change frequency (from git data if available), and coupling into composite_risk
   - Append cross_cutting_risk section to critical-paths.yml details
4. Validate: every artifact has summary: within budget, all findings cite evidence
5. Write tm3-summary.md to .shaktra/analysis/ — max 500 words
   Health score, top risk files, cross-cutting risk highlights

DO NOT: Write to files owned by other TMs. Modify static.yml or overview.yml.
```

### TM-4: "practices" — D4, D7 + test intelligence

**Dimensions:** D4 Coding Practices & Conventions, D7 Data Flows & Integration
**Writes:** `practices.yml`, `data-flows.yml`, `tm4-summary.md`

**Prompt template:**
```
You are Team Member 4: "practices" for Shaktra deep codebase analysis.

CONTEXT:
- Pre-analysis: .shaktra/analysis/static.yml, overview.yml
- Memory (if exists): .shaktra/memory/decisions.yml, lessons.yml
- Dimension specs: analysis-dimensions-core.md (D4), analysis-dimensions-health.md (D7)
- Output schemas: analysis-output-schemas.md

YOUR DIMENSIONS: D4, D7
YOUR OUTPUT FILES: practices.yml, data-flows.yml

INSTRUCTIONS:
1. Read static.yml and overview.yml for ground truth
2. Spawn 2 CBA Analyzer subagents in parallel — D4 and D7
3. After both complete, run test intelligence correlation: review D4 test patterns alongside data-flows for deeper test quality analysis. Ensure violation_catalog in practices.yml captures all convention deviations found.
4. Validate: every artifact has summary: within budget, all findings cite evidence
5. Write tm4-summary.md to .shaktra/analysis/ — max 500 words
   Convention health, violation catalog highlights, data flow risks

DO NOT: Write to files owned by other TMs. Modify static.yml or overview.yml.
```

---

## Stage 3: Aggregate (Lead)

After all 4 team members complete:

1. **Read summaries:** Load `tm1-summary.md` through `tm4-summary.md` (~2000 words total). This is ALL the lead reads from team member output.

2. **Validate artifacts:** Verify all 9 dimension artifacts exist in `.shaktra/analysis/` and each has a `summary:` section as the first key. If any artifact is missing or malformed, report which dimensions need re-execution.

3. **Fallback cross-cutting risk:** If `critical-paths.yml` does not contain a `cross_cutting_risk` section (TM-3 Agent C may have failed or git data was unavailable), compute it now: read `tech-debt.yml`, `critical-paths.yml`, and `git-intelligence.yml` (if available). Append `cross_cutting_risk` to `critical-paths.yml` under `details:`.

4. **Generate checksums:** Compute SHA256 of all analyzed source files. Map each file to dimensions. Write to `checksum.yml`.

5. **Generate Mermaid diagrams:** Read `structure.yml`, generate architecture diagram, include under `diagrams:` key.

6. **Update manifest:** Set all dimensions to `complete`, record completion timestamp, set `execution_mode: deep`.

---

## Stage 4: Memory Capture

Spawn **shaktra-memory-curator** (same as standard flow):
```
You are the shaktra-memory-curator agent. Capture lessons from the completed analysis workflow.

Workflow type: analysis
Artifacts path: .shaktra/analysis/

Extract lessons that meet the capture bar. Append to .shaktra/memory/lessons.yml.
```

---

## Common Constraints

All team members and their subagents must follow:

- **Write only own files** — see ownership map above
- **Evidence required** — every finding must cite file:line, code pattern, or tool output
- **Summary budgets respected** — per `analysis-output-schemas.md` budget table
- **No hallucinated paths** — every file path in output must exist (verify with Glob/Read)
- **Canonical examples are real** — code snippets copied from actual codebase, not generated

## Team Summary Persistence

Team summaries (`tm1-summary.md` through `tm4-summary.md`) persist in `.shaktra/analysis/` after aggregation. They are useful for debugging the analysis process itself and have negligible cost.
