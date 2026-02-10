# Robustify Codebase Analysis — Design Plan

## 1. Problem Statement

The current `/shaktra:analyze` produces 12 YAML artifacts across 8 dimensions. It works, but has three structural problems that prevent "find the needle in a haystack" debugging:

**P1: Under-consumption.** 6 of 8 dimension artifacts are barely or never consumed downstream. `domain-model.yml`, `entry-points.yml`, `data-flows.yml`, `critical-paths.yml`, `dependencies.yml`, and `tech-debt.yml` are produced but almost no agent reads them. The bug diagnostician — the agent that needs these most — loads zero analysis artifacts.

**P2: Shallow depth.** All 8 dimensions run as subagents within a single session. Each CBA analyzer gets limited context. No cross-dimensional correlation happens (e.g., "this file is on a critical path AND has high tech debt AND no tests" — no one computes this).

**P3: Missing intelligence.** No git history analysis (change frequency, bug density, co-change patterns), no convention violation detection, no error propagation tracing, no cross-cutting risk correlation. These are exactly the signals that let principal engineers find bugs fast.

---

## 2. Solution: Two-Pronged Fix

### Prong 1: Fix what we have (all modes)
- Enrich existing artifact schemas with missing fields
- Wire up downstream agents to actually consume the artifacts they should
- Add 1 new artifact (`git-intelligence.yml`) to the standard pipeline

### Prong 2: Add `deep-analysis` mode (team-based)
- New intent in existing `/shaktra:analyze` skill
- Uses Claude Code agent teams for parallel sessions
- 4 team members, each coordinating 2-3 subagents
- Same output artifacts, richer data
- Falls back to single-session if teams unavailable

Both prongs produce the **same artifact schemas**. Deep mode fills them more thoroughly.

---

## 3. What Changes in Existing Artifacts

### 3.1 Enrichments to Existing Schemas

No fields removed. Only additive changes.

**`structure.yml` — add `convention_violations` section:**
```yaml
details:
  # ... existing fields unchanged ...
  convention_violations:
    - module: string
      violation: string        # e.g., "imports from internal of sibling module"
      expected_pattern: string  # what the codebase normally does
      location: string         # file:line
      severity: minor | moderate | significant
```
Why: Architecture violations are currently detected but not contrasted against the codebase's own conventions. This makes violations actionable.

**`domain-model.yml` — add `error_propagation` section:**
```yaml
details:
  # ... existing fields unchanged ...
  error_propagation:
    - error_origin: string     # file:function where error is created/thrown
      propagation_path: [string]  # ordered file:function chain
      terminal_handler: string    # where it's finally caught/handled
      transforms: [string]       # how error shape changes along the path
      swallowed: boolean          # true if error is caught but not re-raised or logged
      user_visible: boolean       # true if error reaches user-facing response
```
Why: Error propagation paths are the #1 thing you trace when debugging. "Where does this error come from, and where does it get swallowed?" is currently unanswerable from analysis artifacts.

**`practices.yml` — add `violation_catalog` section:**
```yaml
details:
  # ... existing fields unchanged ...
  violation_catalog:
    - area: string             # one of the 14 practice areas
      canonical_pattern: string # what the codebase normally does
      violation: string         # what this file does differently
      location: string          # file:line
      impact: low | medium | high  # how likely this causes confusion/bugs
```
Why: Convention violations are where bugs hide. Currently practices.yml documents conventions but doesn't flag where they're broken. This turns it from a style guide into a bug-finding tool.

**`critical-paths.yml` — add `cross_cutting_risk` section:**
```yaml
details:
  # ... existing fields unchanged ...
  cross_cutting_risk:
    - file: string
      risk_factors:
        on_critical_path: boolean
        categories: [string]     # revenue | security | performance | data_integrity
        tech_debt_present: boolean
        debt_items: [string]     # from tech-debt.yml
        test_coverage: none | partial | adequate
        change_frequency: high | medium | low  # from git-intelligence.yml
        coupling_score: high | medium | low
      composite_risk: critical | high | medium | low
      recommendation: string
```
Why: This is the cross-dimensional correlation that no single dimension can produce alone. "This file is on the payment path, has 3 TODOs, no tests, and changes weekly" — that's your #1 incident risk. Currently requires manually cross-referencing 4 artifacts.

**`tech-debt.yml` — add `quantitative_metrics` section:**
```yaml
details:
  # ... existing fields unchanged ...
  quantitative_metrics:
    total_source_files: integer
    total_source_lines: integer
    avg_function_length: integer    # lines
    max_function_length: {file: string, function: string, lines: integer}
    avg_file_length: integer
    max_file_length: {file: string, lines: integer}
    deeply_nested_functions: integer  # functions with nesting depth > 4
    long_functions: integer           # functions > 50 lines
    test_to_source_ratio: float       # e.g., 0.8 means 80 test lines per 100 source lines
    files_without_tests: integer
    percent_files_tested: float
```
Why: The current analysis says "complexity hotspots" but doesn't quantify them. Numbers let you track improvement over time and prioritize debt.

### 3.2 New Artifact: `git-intelligence.yml`

Added to standard pipeline as **D9**. Not a separate workflow — runs alongside D1-D8.

```yaml
summary: |
  {~400 tokens: hotspot count, highest-churn files, co-change clusters,
   bug-fix density distribution, knowledge concentration risks}

details:
  hotspots:
    - file: string
      commits_last_90_days: integer
      commits_last_365_days: integer
      distinct_authors: integer
      churn_category: hot | warm | cold  # hot = top 10%, cold = bottom 50%

  bug_fix_density:
    - file: string
      total_commits: integer
      fix_commits: integer             # commits matching fix/bug/patch/hotfix patterns
      fix_ratio: float                 # fix_commits / total_commits
      recent_fixes: integer            # fix commits in last 90 days

  co_change_patterns:
    - cluster_name: string             # descriptive label
      files: [string]
      co_change_frequency: integer     # times these files changed together
      linked_in_code: boolean          # true if they import each other
      hidden_coupling: boolean         # co-change but no import = hidden coupling

  knowledge_distribution:
    - file: string
      primary_author: string           # most commits
      author_count: integer
      bus_factor: integer              # authors with >20% of commits
      knowledge_risk: high | medium | low  # high = bus_factor 1, on critical path

  code_age:
    - file: string
      last_modified: ISO-8601
      age_category: fresh | recent | aging | stale
      # fresh = <30 days, recent = 30-180, aging = 180-365, stale = >365
```

**Evidence requirements:** All data from `git log` commands — no LLM inference. Pure tool-based extraction (same philosophy as `static.yml`).

**Dimension spec file:** New file `analysis-dimensions-git.md` in shaktra-analyze skill folder.

### 3.3 Updated Summary Budget

| Artifact | Current Budget | New Budget | Delta |
|---|---|---|---|
| `overview.yml` | ~300 | ~300 | unchanged |
| `structure.yml` | ~400 | ~450 | +50 (convention violations) |
| `domain-model.yml` | ~500 | ~550 | +50 (error propagation) |
| `entry-points.yml` | ~400 | ~400 | unchanged |
| `practices.yml` | ~600 | ~650 | +50 (violation catalog) |
| `dependencies.yml` | ~300 | ~300 | unchanged |
| `tech-debt.yml` | ~350 | ~400 | +50 (quantitative metrics) |
| `data-flows.yml` | ~500 | ~500 | unchanged |
| `critical-paths.yml` | ~400 | ~500 | +100 (cross-cutting risk) |
| `git-intelligence.yml` | NEW | ~400 | NEW |
| **Total** | **~3,750** | **~4,450** | **+700** |

+700 tokens is within acceptable bounds. All summaries still loadable simultaneously.

---

## 4. Downstream Consumption Fixes

### 4.1 Current Consumption Map (Problem)

| Agent | Currently Loads | Should Also Load |
|---|---|---|
| architect | structure, practices | domain-model, entry-points |
| sw-engineer | structure, practices | critical-paths, domain-model |
| developer | structure, practices | domain-model (entities for naming) |
| sw-quality | structure (Large only) | critical-paths, git-intelligence |
| scrummaster | "analysis/*" (vague) | domain-model, entry-points, structure (explicit) |
| **bug-diagnostician** | **NOTHING** | **data-flows, critical-paths, domain-model, git-intelligence** |
| **cr-analyzer** | **NOTHING** | **structure, practices, critical-paths** |
| **test-agent** | **NOTHING** | **practices (test patterns), critical-paths** |

### 4.2 Bug Diagnostician — The Critical Fix

The bug diagnostician is the agent that benefits MOST from codebase analysis and currently uses NONE of it. This is the highest-impact fix.

**Add to bug-diagnostician input contract:**
```
IF .shaktra/analysis/ exists:
  Load summaries of:
    - data-flows.yml     → trace where buggy data flows
    - critical-paths.yml → understand blast radius of the bug
    - domain-model.yml   → check state machine violations
    - git-intelligence.yml → check if bug is in a historical hotspot
    - entry-points.yml   → identify which entry points trigger the bug path

  Use for:
    - HYPOTHESIZE step: git hotspots + critical paths narrow candidate root causes
    - GATHER EVIDENCE step: data flows trace the exact path
    - BLAST RADIUS step: cross_cutting_risk pre-computed for affected files
    - STATE BUGS: domain-model state machines reveal invalid transitions
```

### 4.3 CR Analyzer — Architecture-Aware Review

**Add to cr-analyzer input contract:**
```
IF .shaktra/analysis/ exists:
  Load summaries of:
    - structure.yml      → verify changes respect architecture boundaries
    - practices.yml      → verify changes follow codebase conventions
    - critical-paths.yml → flag if changes touch high-risk areas

  Use for:
    - Dimension H (Maintainability): cross-ref against structure.yml patterns
    - Dimension E (Security): flag if changes touch security-critical paths
    - Dimension G (Performance): flag if changes touch performance-critical paths
    - All dimensions: note if file appears in violation_catalog (practices.yml)
```

### 4.4 Test Agent — Risk-Aware Test Writing

**Add to test-agent input contract:**
```
IF .shaktra/analysis/ exists:
  Load summaries of:
    - practices.yml      → follow existing test patterns (naming, fixtures, assertions)
    - critical-paths.yml → prioritize edge case tests for high-risk code

  Use for:
    - Match test naming and structure to canonical test examples
    - Add extra edge case tests for files with high composite_risk
```

### 4.5 Explicit Scrummaster Loading

**Replace vague "Read .shaktra/analysis/ artifacts" with explicit list:**
```
Load summaries of:
  - structure.yml      → module context for story scoping
  - domain-model.yml   → entity/state context for acceptance criteria
  - entry-points.yml   → API context for interface stories
```

---

## 5. Deep Analysis Mode — Team-Based Execution

### 5.1 Intent Classification Update

Add to SKILL.md intent classification:

| Intent | Signals | Target |
|---|---|---|
| `deep-analysis` | "deep", "thorough", "comprehensive", "team", "full deep" | Team-based 3-stage analysis |

### 5.2 Preconditions

- Agent teams feature available (check `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` or feature detection)
- If teams unavailable: warn user, offer to run enhanced single-session instead
- `.shaktra/` directory exists
- Project type is `brownfield`

### 5.3 Execution Flow

```
LEAD SESSION (context-lean orchestrator)
│
├─ Stage 1: Pre-Analysis [LEAD runs directly]
│   ├─ static.yml  (tool-based, no LLM)
│   └─ overview.yml (tool-based, minimal LLM)
│
├─ Stage 2: Spawn Team [LEAD spawns 4 members]
│   │
│   ├─ TM-1: "structure" ─────────────────────────────
│   │   ├─ Agent A: D1 Architecture & Structure
│   │   │   (enriched with convention_violations)
│   │   ├─ Agent B: D5 Dependencies & Tech Stack
│   │   └─ Agent C: D9 Git Intelligence (NEW)
│   │   Writes: structure.yml, dependencies.yml, git-intelligence.yml
│   │   Writes: tm1-summary.md (what lead reads)
│   │
│   ├─ TM-2: "domain" ────────────────────────────────
│   │   ├─ Agent A: D2 Domain Model & Business Rules
│   │   │   (enriched with error_propagation)
│   │   ├─ Agent B: D3 Entry Points & Interfaces
│   │   └─ Agent C: Correlation — error propagation
│   │   │   traces paths across D2+D3 findings
│   │   Writes: domain-model.yml, entry-points.yml
│   │   Writes: tm2-summary.md
│   │
│   ├─ TM-3: "health" ────────────────────────────────
│   │   ├─ Agent A: D6 Technical Debt & Security
│   │   │   (enriched with quantitative_metrics)
│   │   ├─ Agent B: D8 Critical Paths & Risk
│   │   └─ Agent C: Cross-cutting risk correlation
│   │   │   reads D6+D8+git-intelligence outputs
│   │   │   produces cross_cutting_risk in critical-paths.yml
│   │   Writes: tech-debt.yml, critical-paths.yml
│   │   Writes: tm3-summary.md
│   │
│   └─ TM-4: "practices" ─────────────────────────────
│       ├─ Agent A: D4 Coding Practices & Conventions
│       │   (enriched with violation_catalog)
│       ├─ Agent B: D7 Data Flows & Integration
│       └─ Agent C: Test Intelligence
│       │   deeper test quality analysis folded into
│       │   tech-debt.yml test_health + practices.yml test patterns
│       Writes: practices.yml, data-flows.yml
│       Writes: tm4-summary.md
│
├─ Stage 3: Aggregate [LEAD reads only summaries]
│   ├─ Read tm1-summary.md through tm4-summary.md (~2000 words total)
│   ├─ Validate all 10 dimension artifacts exist with summary: sections
│   ├─ Generate checksums → checksum.yml
│   ├─ Update manifest → manifest.yml (now tracks D1-D9)
│   ├─ Generate Mermaid diagrams → structure.yml diagrams section
│   └─ Back-fill settings.project.architecture if applicable
│
└─ Stage 4: Memory Capture [LEAD spawns memory curator]
    └─ Extract lessons from analysis into lessons.yml
```

### 5.4 Team Member Prompt Template

Each team member receives a structured prompt from the lead:

```
You are Team Member {N}: "{domain_name}" for Shaktra deep codebase analysis.

CONTEXT:
- Project: {project_name} ({language}, {framework})
- Pre-analysis artifacts at: .shaktra/analysis/static.yml, overview.yml
- Memory (if exists): .shaktra/memory/decisions.yml, lessons.yml
- Dimension specs: dist/skills/shaktra-analyze/{relevant spec files}
- Output schemas: dist/skills/shaktra-analyze/analysis-output-schemas.md

YOUR DIMENSIONS: {D_list}
YOUR OUTPUT FILES: {artifact_list}

INSTRUCTIONS:
1. Read static.yml and overview.yml for ground truth
2. Spawn up to 3 subagents (Task tool) for your dimensions
   - Each subagent receives: dimension spec, static.yml path, output schema
   - Subagents write directly to .shaktra/analysis/{artifact}.yml
3. After all subagents complete, validate:
   - Every artifact has summary: section within token budget
   - Every finding cites file:line evidence
   - No hallucinated dependencies (verify against static.yml)
4. {Cross-cutting instructions specific to this TM}
5. Write tm{N}-summary.md to .shaktra/analysis/ — max 500 words
   - Key findings, risk highlights, notable patterns
   - This is ALL the lead will read from you

DO NOT:
- Write to artifacts owned by other team members
- Modify static.yml or overview.yml
- Create files outside .shaktra/analysis/
```

### 5.5 Sequencing Constraint: TM-3 Agent C

TM-3's cross-cutting risk correlation agent needs data from TM-1 (git-intelligence.yml) and TM-3's own D6 and D8 outputs. Two options:

**Option A (preferred): TM-3 runs Agent C after A and B complete.**
TM-3 spawns Agents A and B in parallel, waits, then spawns Agent C which reads their outputs plus git-intelligence.yml. If git-intelligence.yml isn't ready yet (TM-1 still running), Agent C uses whatever git data it can extract directly.

**Option B: Lead runs cross-cutting correlation in Stage 3.**
After all team members finish, lead spawns one more agent to compute cross_cutting_risk. Adds latency but guarantees all data is available. Increases lead's context usage.

### 5.6 File Ownership Map (Conflict Prevention)

| File | Owner | Other TMs: Read-Only |
|---|---|---|
| `static.yml` | Lead (Stage 1) | All TMs read |
| `overview.yml` | Lead (Stage 1) | All TMs read |
| `structure.yml` | TM-1 | — |
| `dependencies.yml` | TM-1 | — |
| `git-intelligence.yml` | TM-1 | TM-3 reads |
| `domain-model.yml` | TM-2 | — |
| `entry-points.yml` | TM-2 | — |
| `practices.yml` | TM-4 | — |
| `data-flows.yml` | TM-4 | — |
| `tech-debt.yml` | TM-3 | — |
| `critical-paths.yml` | TM-3 | — |
| `manifest.yml` | Lead (Stage 3) | — |
| `checksum.yml` | Lead (Stage 3) | — |
| `tm{N}-summary.md` | TM-{N} | Lead reads |

Zero file conflicts. Each artifact has exactly one writer.

---

## 6. Single-Session Fallback (Enhanced Mode)

When teams are unavailable, the enhanced single-session mode still benefits from Prong 1:

- Same enriched schemas (convention violations, error propagation, etc.)
- D9 (git intelligence) added as 9th parallel CBA analyzer
- Cross-cutting risk computed in finalize stage (lead reads D6, D8, D9 outputs)
- Downstream consumption fixes apply regardless

The difference: single-session can't go as deep per dimension (context budget shared across 9 subagents vs. dedicated team member sessions).

---

## 7. Manifest Schema Update

```yaml
# Add D9 to dimensions:
dimensions:
  # D1-D8 unchanged ...
  D9:
    name: Git Intelligence
    status: pending | in_progress | complete | failed
    output_file: git-intelligence.yml
    started_at: ISO-8601 | null
    completed_at: ISO-8601 | null
    error: string | null

# Add execution_mode:
execution_mode: standard | deep  # tracks which mode produced this analysis
```

---

## 8. What Does NOT Change

- **Artifact file format:** Still YAML with `summary:` + `details:` structure
- **Artifact file locations:** Still `.shaktra/analysis/`
- **Summary-first loading pattern:** Agents still read summaries by default
- **Static extraction (Stage 1):** Still tool-based, still runs first
- **Resumability:** Manifest still tracks per-dimension completion
- **Incremental refresh:** Checksums still enable selective re-analysis
- **Existing dimension specs (D1-D8):** Content preserved, only additive fields
- **Other skills:** `/shaktra:tpm`, `/shaktra:dev`, `/shaktra:review`, `/shaktra:bugfix` — skill prompts unchanged except for the downstream consumption wiring (agent files updated)
- **Debt strategy / dependency audit workflows:** Unchanged, still consume D6/D5 outputs

---

## 9. Implementation Phases

### Phase A: Schema Enrichment + D9 (~1-2 sessions)
Files to modify:
- `analysis-output-schemas.md` — add new fields to 5 existing schemas + D9 schema
- `analysis-dimensions-core.md` — add convention_violations to D1, error_propagation to D2, violation_catalog to D4
- `analysis-dimensions-health.md` — add quantitative_metrics to D6, cross_cutting_risk to D8
- NEW: `analysis-dimensions-git.md` — D9 Git Intelligence spec
- `SKILL.md` — add D9 to Stage 2 dispatch, add cross-cutting correlation to Stage 3

### Phase B: Downstream Consumption Wiring (~1 session)
Files to modify:
- `dist/agents/shaktra-bug-diagnostician.md` — add analysis artifact loading
- `dist/agents/shaktra-cr-analyzer.md` — add analysis artifact loading
- `dist/agents/shaktra-test-agent.md` — add analysis artifact loading
- `dist/agents/shaktra-scrummaster.md` — make consumption explicit
- `dist/skills/shaktra-analyze/analysis-output-schemas.md` — update downstream loading guide

### Phase C: Deep Analysis Mode (~1-2 sessions)
Files to modify:
- `SKILL.md` — add `deep-analysis` intent, team spawn logic, Stage 3 aggregation
- NEW or update: team member prompt templates (could be inline in SKILL.md or separate reference file)

### Phase D: Validation
- Run enhanced single-session analysis on a real codebase
- Run deep analysis (team-based) on same codebase
- Verify all 10 artifacts produce valid YAML with summaries
- Verify downstream agents load and use new fields
- Verify no file exceeds 300 lines after changes
- Verify no content duplication across layers

---

## 10. Key Design Decisions to Confirm

1. **D9 as tool-based extraction (like static.yml) vs. LLM-analyzed?**
   Recommendation: tool-based. Git data is factual. No LLM needed for `git log` output parsing. A Python script in `dist/scripts/` could handle extraction, or CBA analyzer runs git commands directly.

2. **Cross-cutting risk: computed by TM-3 or by lead in Stage 3?**
   Recommendation: TM-3 Agent C (Option A above). Keeps lead context lean. TM-3 can read git-intelligence.yml if TM-1 finishes first; if not, computes without git data and lead can re-run correlation in Stage 3.

3. **Team member summaries (tm*-summary.md): persist or delete after aggregation?**
   Recommendation: persist. They're useful for debugging the analysis itself and cost nothing.

4. **Should deep-analysis be the default, or always require explicit "deep" signal?**
   Recommendation: explicit signal. Teams cost significantly more tokens. Standard analysis remains the default for cost-conscious usage.

---

## 11. Success Criteria

After implementation, these should be true:

- [ ] Bug diagnostician can answer "where does this data flow?" by reading data-flows.yml
- [ ] Bug diagnostician can answer "is this a historically buggy area?" by reading git-intelligence.yml
- [ ] Bug diagnostician can answer "what else breaks if this fails?" by reading critical-paths.yml cross_cutting_risk
- [ ] CR analyzer flags when a PR touches code that violates its own conventions (practices.yml violation_catalog)
- [ ] CR analyzer flags when a PR touches a critical path without adding tests
- [ ] Any agent can identify the top 10 riskiest files by reading critical-paths.yml cross_cutting_risk
- [ ] Deep analysis produces the same artifact format as standard analysis (consumers don't care which mode ran)
- [ ] Deep analysis completes faster wall-clock than standard (parallel team sessions)
- [ ] No single file exceeds 300 lines
- [ ] Total summary budget stays under 5,000 tokens
