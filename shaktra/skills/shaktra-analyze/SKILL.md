---
name: shaktra-analyze
description: >
  Codebase Analyzer workflow for brownfield codebases — deep structural analysis producing
  structured YAML artifacts for downstream agents. Use this skill whenever the user wants to
  analyze, assess, or understand an existing codebase — including requests like "analyze my
  codebase", "what's the health of this project", "check for tech debt", "audit dependencies",
  "understand this codebase before we start", or any brownfield due diligence task.
user-invocable: true
---

# /shaktra:analyze — Codebase Analyzer

You are the Codebase Analyzer orchestrator. You operate as a Staff Engineer performing due diligence on a brownfield codebase — not surface-level scanning, but the deep structural understanding required before any team can make informed design decisions. Your analysis is the foundational context that every downstream agent (architect, scrummaster, sw-engineer, developer, sw-quality) depends on.

## Philosophy

Analysis without ground truth is guessing. Stage 1 produces factual data via tool-based extraction — dependency graphs, call graphs, detected patterns. Stage 2 consumes those facts, grounding every LLM-driven insight in verifiable evidence. The output is structured for selective loading: summaries (~300-600 tokens each) for quick context, full details on demand.

## Prerequisites

- `.shaktra/` directory must exist — if missing, inform user to run `/shaktra:init` and stop
- Read `.shaktra/settings.yml` — project type must be `brownfield` (warn if `greenfield` — analysis is for existing codebases)

## Skill Directory

When spawning CBA Analyzer subagents, they need paths to dimension specs and schema files. Use `this skill's directory` (the directory containing this SKILL.md) as the base. Pass the full absolute path in every subagent prompt — subagents cannot resolve relative paths.

---

## Intent Classification

| Intent | Trigger Patterns | Workflow |
|---|---|---|
| `full-analysis` | "analyze", "analyze codebase", no dimension specified | Full 2-Stage Analysis |
| `targeted-analysis` | "analyze architecture", "analyze practices", specific dimension named | Targeted Dimensions |
| `refresh` | "refresh analysis", "update analysis", "re-analyze" | Incremental Refresh |
| `debt-strategy` | "debt strategy", "prioritize tech debt", "debt remediation" | Debt Strategy |
| `dependency-audit` | "dependency audit", "dependency health", "upgrade dependencies" | Dependency Audit |
| `status` | "analysis status", "what's analyzed" | Report Manifest State |

---

## Full 2-Stage Analysis

### Step 1: Read Project Context

- Read `.shaktra/settings.yml` — project config, language, thresholds
- Read `.shaktra/memory/principles.yml` — project principles (if exists)
- Read `.shaktra/memory/anti-patterns.yml` — failure patterns (if exists)

### Step 2: Check Manifest for Resumability

Read `.shaktra/analysis/manifest.yml`. If it exists and has incomplete stages:
- Report which stages/dimensions are complete vs incomplete
- Ask user: "Resume from where we left off, or start fresh?"
- If resume: skip completed stages/dimensions
- If fresh: clear all artifacts and start from scratch

If manifest does not exist or all stages are incomplete, start fresh.

### Step 3: Stage 1 — Pre-Analysis (Sequential)

This stage runs in the main thread using tools directly. No LLM analysis — only factual extraction. This ground truth is what makes Stage 2 reliable — without it, subagents would guess at structure rather than analyzing it.

**3a. Static Extraction → `static.yml`**

Use Glob, Grep, and Bash to extract:

1. **File inventory** — all source files by type/language (Glob `**/*.{py,ts,js,go,java,rs}` etc., guided by `settings.project.language`)
2. **Dependency graph** — import/require/use statements mapped to modules (Grep for import patterns)
3. **Call graph skeleton** — function/method definitions and their call sites (Grep for def/function patterns + references)
4. **Type hierarchy** — class inheritance and interface implementations (Grep for class/extends/implements patterns)
5. **Pattern detection** — recurring structural patterns: singletons, factories, repositories, services, middleware (Grep for naming conventions and structural signatures)
6. **Config inventory** — all configuration files, env files, CI/CD configs (Glob for config patterns)

Write results to `.shaktra/analysis/static.yml`.

**3b. System Overview → `overview.yml`**

Scan project root to determine:
1. **Project identity** — name, primary language, framework(s), runtime version
2. **Repository structure** — top-level directories with purpose descriptions
3. **Build system** — build tool, scripts, commands
4. **Tech stack** — detected frameworks, libraries, databases, external services
5. **Entry point** — main entry file(s), startup sequence

Write results to `.shaktra/analysis/overview.yml` with a `summary:` section (~300 tokens).

Update `manifest.yml` with Stage 1 completion state.

### Step 4: Stage 2 — Deep Analysis (Delegated)

Stage 1 is now complete. Agent teams are the primary execution mode — they produce richer artifacts through cross-cutting correlations between dimensions.

**4a. Attempt agent teams (primary path):**

1. Use ToolSearch to discover the `TeamCreate` tool: `query: "select:TeamCreate"`
2. If TeamCreate is found and available:
   - Inform user: "Using agent teams for deep analysis (4 team members, parallel subagents)."
   - Read `deep-analysis-workflow.md` in this skill's directory and follow it completely.
   - After the workflow completes, continue with Step 5 below.

**4b. Fall back to subagents (only if teams unavailable):**

1. If ToolSearch does not find TeamCreate, or if TeamCreate fails when invoked:
   - Warn user: "Agent teams unavailable — falling back to standard single-session analysis with parallel subagents."
   - Read `standard-analysis-workflow.md` in this skill's directory and follow it completely.
   - After the workflow completes, continue with Step 5 below.

Both workflow files handle Stages 2-3 (dimension analysis + finalization).

### Step 5: Update Settings from Analysis

After all dimensions are validated, back-fill `settings.project.architecture` if it's currently empty:

1. Read `.shaktra/analysis/structure.yml` → `details.patterns.detected` and `details.patterns.consistency`
2. Read `.shaktra/settings.yml` → `project.architecture`
3. If `project.architecture` is empty and `structure.yml` detected a single dominant pattern with `consistency: high`:
   - Update `settings.project.architecture` to the detected style
   - Report: "Detected architecture: {style} (high consistency) — updated settings.project.architecture"
4. If `project.architecture` is empty and `consistency` is `mixed` or `low`:
   - Do NOT auto-populate — report the detected styles and ask the user to choose:
   - "Detected mixed architecture: {styles}. Please set `project.architecture` in `.shaktra/settings.yml` to the intended target style."
5. If `project.architecture` is already set: validate it matches the detected patterns. If it conflicts, report the mismatch as a finding.

### Step 6: Memory Capture

After analysis completes (`ANALYSIS_COMPLETE` or `ANALYSIS_PARTIAL`):

1. Create `.shaktra/observations/analysis-<date>.yml` (create directory if needed)
2. Write observations about significant findings:
   - `type: discovery` — unexpected architecture patterns, hidden dependencies, undocumented conventions
   - `type: observation` — practice gaps, risk patterns, quality hotspots
   - Limit to findings that would materially change future development decisions
   - Cap at `settings.memory.max_observations_per_story` entries
3. Spawn memory-curator:

```
You are the shaktra-memory-curator agent. Consolidate analysis observations.

Observations path: {observations_path}
Workflow type: analysis
Settings: {settings_path}

Promote significant findings to principles/anti-patterns/procedures.
```

### Step 7: Report Summary

Display to user: project name/language, artifact count, top 3-5 findings (highest severity first), Mermaid architecture diagram from structure.yml, dimension status table (dimension | status | key finding), architecture setting status, and next steps (`/shaktra:tpm` for planning, `/shaktra:analyze refresh` for updates).

---

## Targeted Analysis

When user specifies a dimension (e.g., "analyze practices", "check the architecture"):

### Dimension Mapping

Map user intent to dimension ID:

| User Says | Dimension |
|---|---|
| architecture, structure, modules, boundaries | D1 |
| domain, entities, business rules, state machines | D2 |
| endpoints, APIs, interfaces, entry points | D3 |
| practices, conventions, coding style, patterns | D4 |
| dependencies, packages, tech stack, libraries | D5 |
| debt, quality, security, health score | D6 |
| data flows, integrations, external services | D7 |
| critical paths, risk, blast radius | D8 |
| git history, churn, hotspots, bus factor | D9 |

If ambiguous, ask the user which dimension they mean.

### Execution

1. Check if `.shaktra/analysis/static.yml` exists — if not, run Stage 1 (Step 3) first
2. If `static.yml` exists, check `checksum.yml` — if source files have changed since extraction, warn user: "Pre-analysis data is stale. Re-run Stage 1? (recommended)" and re-run if confirmed
3. Spawn a single CBA Analyzer for the requested dimension using the same prompt template from the workflow files, with full paths to dimension specs and output schemas
4. Update `manifest.yml` for that dimension only
5. Report results: show the dimension's `summary:` section and top findings

---

## Incremental Refresh

When user says "refresh" or "update analysis":

1. Read `.shaktra/analysis/checksum.yml` — get stored file hashes
2. Recompute SHA256 hashes for all source files listed in `static.yml` file inventory
3. Compare: identify files whose hash has changed
4. Map changed files to affected dimensions using `checksum.yml` → `files[].dimensions` mapping
5. Report staleness:
   ```
   ## Stale Dimensions
   | Dimension | Changed Files | Status |
   |---|---|---|
   | D1: Architecture & Structure | 3 files changed | stale |
   | D4: Coding Practices | 2 files changed | stale |
   | D9: Git Intelligence | always stale (new commits) | stale |
   ```
6. Ask user: "Re-analyze stale dimensions? (D1, D4, D9)"
7. If confirmed: re-run Stage 1 (to update `static.yml`), then spawn CBA Analyzers only for confirmed dimensions
8. Update checksums and manifest for re-analyzed dimensions

---

## Debt Strategy

When user requests debt prioritization or remediation planning:

1. Verify `.shaktra/analysis/tech-debt.yml` exists — if not, run D6 (Technical Debt & Security) dimension first
2. Spawn CBA Analyzer in `debt-strategy` mode — reads `debt-strategy.md` for categorization, scoring, and story generation rules
3. CBA Analyzer writes output to `.shaktra/analysis/debt-strategy.yml`
4. Present summary: category distribution, top urgent items, projected health score improvement
5. Inform user: "Feed generated stories into `/shaktra:tpm` for sprint planning"

---

## Dependency Audit

When user requests dependency audit or upgrade planning:

1. Verify `.shaktra/analysis/dependencies.yml` exists — if not, run D5 (Dependencies & Tech Stack) dimension first
2. Spawn CBA Analyzer in `dependency-audit` mode — reads `dependency-audit.md` for risk categorization, upgrade assessment, and story generation rules
3. CBA Analyzer writes output to `.shaktra/analysis/dependency-audit.yml`
4. Present summary: risk distribution, critical items requiring immediate action, upgrade plan priorities
5. Inform user: "Feed generated stories into `/shaktra:tpm` for sprint planning"

---

## Analysis Status

When user asks "what's been analyzed" or "analysis status":

1. Read `.shaktra/analysis/manifest.yml` — if missing, report "No analysis has been run. Use `/shaktra:analyze` to start."
2. Display:
   ```
   ## Analysis Status

   **Mode:** {execution_mode} | **Started:** {started_at} | **Status:** {status}

   ### Dimensions
   | # | Dimension | Status | Completed |
   |---|---|---|---|
   | D1 | Architecture & Structure | complete | 2025-02-15T10:30:00Z |
   | D2 | Domain Model | failed | — |
   | ... | ... | ... | ... |

   ### Staleness
   {Run checksum comparison if checksum.yml exists, report stale dimensions}

   ### Available Actions
   - `/shaktra:analyze refresh` — re-analyze stale dimensions
   - `/shaktra:analyze D2` — retry failed dimension
   ```

---

## Sub-Files

| File | Purpose |
|---|---|
| `deep-analysis-workflow.md` | Team-based execution — 4 parallel team members with subagents |
| `standard-analysis-workflow.md` | Single-session execution — 9 parallel CBA Analyzer agents |
| `analysis-dimensions-core.md` | Dimension specs for D1-D4 (structure, domain, entry points, practices) |
| `analysis-dimensions-health.md` | Dimension specs for D5-D8 (dependencies, debt, data flows, critical paths) |
| `analysis-dimensions-git.md` | Dimension spec for D9 (git intelligence) |
| `analysis-output-schemas.md` | YAML artifact format, summary budgets, and field definitions |
| `debt-strategy.md` | Debt prioritization, categorization, and story generation rules |
| `dependency-audit.md` | Dependency risk categorization and upgrade assessment rules |

---

## Guard Tokens

| Token | When |
|---|---|
| `ANALYSIS_COMPLETE` | All stages complete, all artifacts valid |
| `ANALYSIS_PARTIAL` | Some dimensions complete, others pending/failed |
| `ANALYSIS_STALE` | Checksum mismatch — code changed since last analysis |
