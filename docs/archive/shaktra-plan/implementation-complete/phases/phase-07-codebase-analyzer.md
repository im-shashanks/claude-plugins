# Phase 7 — Codebase Analyzer [COMPLETE]

> **Context Required:** Read [architecture-overview.md](../architecture-overview.md) before starting.
> **Depends on:** Phase 1 (Foundation). Standalone workflow — most independent phase.
> **Blocks:** Phase 11 (Workflow Router)

---

## Objective

Build the codebase analysis workflow for brownfield projects. Produces structured, token-efficient analysis consumed by architect, scrummaster, sw-engineer, developer, and sw-quality agents for informed design, story enrichment, and implementation decisions. Analysis is the foundational context that every downstream agent uses — gaps here cascade into every workflow.

## Architecture — 2-Stage Model

```
Stage 1: Pre-Analysis (sequential — ground truth before LLM)
  1a. Static extraction via Glob/Grep/Bash → static.yml
  1b. System overview scan → overview.yml

Stage 2: Parallel Deep Dimensions (8 CBA Analyzer agents)
  D1: Architecture & Structure        → structure.yml
  D2: Domain Model & Business Rules   → domain-model.yml
  D3: Entry Points & Interfaces       → entry-points.yml
  D4: Coding Practices & Conventions  → practices.yml
  D5: Dependencies & Tech Stack       → dependencies.yml
  D6: Technical Debt & Security       → tech-debt.yml
  D7: Data Flows & Integration        → data-flows.yml
  D8: Critical Paths & Risk           → critical-paths.yml

Stage 3: Finalize (sequential — after all dimensions)
  - Validate all artifacts + summary sections
  - Generate checksum.yml
  - Update manifest.yml
  - Memory capture via memory-curator
  - Report summary to user
```

**Why 2-stage:** Stage 1 produces factual ground truth (dependency graphs, call graphs, patterns) using tool-based extraction — no LLM hallucination. Stage 2 dimensions consume static.yml as input, grounding LLM analysis in facts. This prevents false positives in dependency relationships and pattern detection.

**Why tool-based static analysis:** Language-agnostic via Glob/Grep/Bash (not a Python script). Works for any language. No script maintenance.

## Deliverables

| File | Lines | Purpose |
|------|-------|---------|
| `skills/shaktra-analyze/SKILL.md` | ~220 | 2-stage orchestrator: pre-analysis, parallel dispatch, finalize, memory, report |
| `skills/shaktra-analyze/analysis-dimensions-core.md` | ~240 | Dimensions D1-D4: architecture, domain model, entry points, practices |
| `skills/shaktra-analyze/analysis-dimensions-health.md` | ~210 | Dimensions D5-D8: dependencies, tech debt, data flows, critical paths |
| `skills/shaktra-analyze/analysis-output-schemas.md` | ~240 | YAML schemas for all 12 output files + summary format requirements |
| `agents/shaktra-cba-analyzer.md` | ~90 | Executor agent: persona, tool usage protocol, evidence standards, dimension execution |
| `templates/analysis-manifest.yml` | ~85 | Manifest template for `/shaktra:init` |

**Split rationale:** Dimensions split into core (D1-D4: "what is this codebase") and health (D5-D8: "how healthy is it") to stay under 300-line constraint. Output schemas in a separate file because CBA Analyzer loads dimensions, SKILL.md loads output schemas for validation.

## Dimension-to-Forge Mapping

| Shaktra Dimension | Forge Phases Covered | Key Additions vs Original Plan |
|---|---|---|
| Pre: Static | Phase 0 | NEW — dependency graph, call graph, type hierarchy, patterns |
| Pre: Overview | Phase 1 | NEW — project identity, tech stack, config inventory |
| D1: Architecture & Structure | Phase 2 | Expanded — module summaries (why_exists, responsibilities), boundary violations |
| D2: Domain Model & Business Rules | Phase 3 | NEW — entities, state machines, invariants, edge cases, lessons learned |
| D3: Entry Points & Interfaces | Phase 4 | Expanded — was "API surface area," now includes events, CLI, jobs, webhooks |
| D4: Coding Practices & Conventions | Phase 6+7+12 | NEW — 14 practice areas, naming conventions, canonical examples |
| D5: Dependencies & Tech Stack | Phase 5 | Enriched with health/CVE data |
| D6: Technical Debt & Security | Phase 8 | Merged — was "Code quality metrics" + "Security posture," adds health score |
| D7: Data Flows & Integration | Phase 9 | NEW — tiered flows, integration gotchas (race conditions, TOCTOU) |
| D8: Critical Paths & Risk | Phase 10 | NEW — replaces "Test coverage & gaps," adds blast radius, lessons learned |

## Output Schema — 12 YAML Files

All output to `.shaktra/analysis/`:

| File | Source | Summary Budget |
|---|---|---|
| `static.yml` | Pre-analysis | N/A (factual) |
| `overview.yml` | Pre-analysis | ~300 tokens |
| `structure.yml` | D1 | ~400 tokens |
| `domain-model.yml` | D2 | ~500 tokens |
| `entry-points.yml` | D3 | ~400 tokens |
| `practices.yml` | D4 | ~600 tokens |
| `dependencies.yml` | D5 | ~300 tokens |
| `tech-debt.yml` | D6 | ~350 tokens |
| `data-flows.yml` | D7 | ~500 tokens |
| `critical-paths.yml` | D8 | ~400 tokens |
| `manifest.yml` | Finalize | N/A (metadata) |
| `checksum.yml` | Finalize | N/A (hashes) |

Every artifact (except static/manifest/checksum) follows: `summary:` section at top (300-600 tokens, self-contained) + `details:` section below (full depth, on-demand). Total summary budget: ~3,750 tokens — any agent can load all summaries without context pressure.

## Downstream Consumer Loading Map

| Agent | Loads These Summaries | For This Purpose |
|---|---|---|
| Architect | overview, structure, practices, dependencies | Brownfield design respecting existing patterns |
| Scrummaster | structure, entry-points, domain-model | Story enrichment with codebase context |
| SW Engineer | practices, domain-model, critical-paths | Implementation planning matching codebase |
| Developer | practices (full + examples), domain-model | Code generation matching existing style |
| SW Quality | critical-paths, domain-model | Risk-aware story-level review |

## Workflow

```
User: /shaktra:analyze "Analyze codebase for development readiness"

Analyze Skill (main thread):
  1. Read project context (.shaktra/settings.yml, .shaktra/memory/decisions.yml, .shaktra/memory/lessons.yml)
  2. Check manifest for resumability — resume incomplete dimensions only
  3. STAGE 1 — Pre-Analysis (sequential):
     a. Static extraction via Glob/Grep/Bash → static.yml
     b. System overview scan → overview.yml
     c. Update manifest.yml with Stage 1 completion
  4. STAGE 2 — Parallel Deep Dimensions:
     Spawn 8 CBA Analyzer agents, each receiving:
       - Its assigned dimension from analysis-dimensions-core.md (D1-D4) or analysis-dimensions-health.md (D5-D8)
       - static.yml as ground truth input
       - overview.yml for project context
     Dimensions: D1–D8 (see Architecture above)
     Update manifest.yml per dimension completion
  5. STAGE 3 — Finalize (sequential):
     a. Validate all artifacts have summary: sections
     b. Generate checksum.yml (SHA256 of analyzed source files)
     c. Update manifest.yml with completion state
     d. Generate mermaid diagrams for key architectural connections
  6. MEMORY CAPTURE (mandatory final step):
     Spawn shaktra-memory-curator
       - Reviews analysis findings (patterns, risks, architecture insights)
       - Evaluates: "Would this materially change future workflow execution?"
       - Writes actionable insights to .shaktra/memory/lessons.yml (if any)
  7. Report analysis summary to user
```

## Resumability & Incremental Refresh

**Resumability:** `manifest.yml` tracks completion state per stage/dimension. If analysis is interrupted, re-running `/shaktra:analyze` checks the manifest and resumes from the first incomplete stage or dimension. Completed dimensions are not re-executed.

**Incremental refresh:** `checksum.yml` stores SHA256 hashes of all analyzed source files, mapped to the dimensions they affect. When re-analyzing after code changes, dimensions where no input files changed can be skipped. The manifest records whether each dimension result is `current` or `stale`.

## What's Simplified from Forge (Intentionally Consolidated)

- **No separate conventions.yml** — merged into `practices.yml` as a section
- **No separate examples.yml** — canonical examples embedded in `practices.yml` per pattern
- **No separate flows/ directory** — reference flows indexed in `data-flows.yml` with enough context
- **Static via agent tools, not Python script** — language-agnostic, no script maintenance
- **No learning-analyzer** — Forge's ML pattern discovery is out of scope; Shaktra uses memory-curator
- **No 13-phase sequential pipeline** — 2-stage (sequential pre + parallel deep) is faster and equally thorough

## Validation

- [ ] Pre-analysis produces factual `static.yml` (dependency graph, call graph, patterns)
- [ ] All 12 output files generated with valid YAML
- [ ] Every artifact has self-contained `summary:` section within token budget
- [ ] Domain model includes edge cases and lessons learned
- [ ] Practices include canonical examples per detected pattern
- [ ] Data flows include integration gotchas (race conditions, TOCTOU)
- [ ] Critical paths include blast radius and lessons learned
- [ ] Manifest tracks dimension completion state (resumability)
- [ ] Checksum enables incremental refresh
- [ ] Architect agent can load summaries and produce brownfield design
- [ ] Scrummaster can enrich stories using analysis context
- [ ] Parallel dimension execution works for independent dimensions
- [ ] Memory capture invoked as final step
- [ ] Mermaid diagrams generated for architecture connections
- [ ] No file exceeds 300 lines
- [ ] No content duplication across skill files

## Forge Reference

| Forge Source | What to Port | What to Change |
|-------------|-------------|----------------|
| forge-analyzer agent (Phase 0) | Static pre-analysis concept | **Use Glob/Grep/Bash tools instead of Python AST script** |
| forge-analyzer agent (Phases 1-10) | Multi-phase deep analysis | **Consolidate 13 phases into 2-stage model (pre + 8 parallel)** |
| forge-analyze skill | Analysis framework, output structure | **Add summary architecture, manifest, checksums** |
| forge-analyzer output schemas | YAML output format | **Standardize summary: + details: pattern across all files** |
