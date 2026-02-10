# Analysis Output Schemas

This file defines the YAML schemas for all output files produced by `/shaktra:analyze` — 13 primary artifacts from the analysis pipeline (9 dimensions + static, overview, manifest, checksum) plus 2 derivative artifacts from strategy workflows. Used by the orchestrator for validation in Stage 3 and by downstream agents to understand available data.

**Used by:** shaktra-analyze SKILL.md (validation), downstream agents (consumption reference).

---

## Summary Format Requirements

Every analysis artifact (except `static.yml`, `manifest.yml`, `checksum.yml`) MUST begin with a `summary:` key containing a self-contained text block. Summaries are the primary consumption mechanism — agents load summaries for context without reading full details.

**Rules:**
- `summary:` is the first key in the YAML document
- Summary text is a YAML literal block scalar (`|`)
- Summary is self-contained — readable without any other file
- Summary stays within its token budget (see table below)
- Summary includes: what was found, key metrics, notable issues, overall assessment

| Artifact | Summary Budget | Must Include |
|---|---|---|
| `overview.yml` | ~300 tokens | Project identity, tech stack, structure overview |
| `structure.yml` | ~450 tokens | Module count, architecture style, boundary violations, convention violations |
| `domain-model.yml` | ~550 tokens | Entity count, state machines, critical invariants, error propagation |
| `entry-points.yml` | ~400 tokens | Endpoint count by type, auth coverage, gaps |
| `practices.yml` | ~650 tokens | Dominant practices, naming conventions, violation catalog, consistency |
| `dependencies.yml` | ~300 tokens | Total deps, health distribution, CVEs, risks |
| `tech-debt.yml` | ~400 tokens | Health score, debt density, security issues, quantitative metrics |
| `data-flows.yml` | ~500 tokens | Flow count by tier, integration points, critical gotchas |
| `critical-paths.yml` | ~500 tokens | Critical path count, highest-risk areas, cross-cutting risk |
| `git-intelligence.yml` | ~400 tokens | Hotspots, churn, bug-fix density, knowledge risks |

**Total summary budget:** ~4,450 tokens — all primary summaries loadable simultaneously without context pressure.

Derivative artifacts (`debt-strategy.yml`, `dependency-audit.yml`) define their own ~400 token summary budgets in their respective workflow files. These are loaded on-demand, not with the primary summaries.

---

## Schema: `static.yml`

Factual data from tool-based extraction. No LLM analysis. No summary section.

```yaml
extracted_at: ISO-8601 timestamp
language: string
file_inventory:
  total_files: integer
  by_type:
    - extension: string
      count: integer
      files: [string]
dependency_graph:
  - source: string      # file path
    imports: [string]    # imported modules/files
call_graph:
  - file: string
    definitions:
      - name: string
        type: function | method | class
        line: integer
    references:
      - name: string
        called_from: [string]  # file:line
type_hierarchy:
  - name: string
    type: class | interface | trait | protocol
    file: string
    extends: [string]
    implements: [string]
detected_patterns:
  - pattern: string      # singleton, factory, repository, service, middleware, etc.
    locations: [string]   # file paths
config_inventory:
  - file: string
    type: string          # env, yaml, json, toml, ini, etc.
    purpose: string
```

---

## Schema: `overview.yml`

```yaml
summary: |
  {~300 tokens — project identity, tech stack, structure overview}
details:
  project:
    name: string
    language: string
    framework: string
    runtime_version: string
  structure:
    - directory: string
      purpose: string
  build:
    tool: string
    scripts: {key: value}
  tech_stack:
    frameworks: [string]
    databases: [string]
    external_services: [string]
    infrastructure: [string]
  entry_files: [string]
```

---

## Schema: `manifest.yml`

Tracks analysis completion state for resumability.

```yaml
version: string          # plugin version from plugin.json
started_at: ISO-8601
completed_at: ISO-8601 | null
status: pending | in_progress | complete | partial
execution_mode: standard | deep  # which mode produced this analysis

stages:
  pre_analysis:
    static:  {status: pending | complete, completed_at: ISO-8601 | null}
    overview: {status: pending | complete, completed_at: ISO-8601 | null}

  dimensions:
    # D1 through D9 — each dimension has this structure:
    D1:
      name: Architecture & Structure     # D2: Domain Model, D3: Entry Points, D4: Practices
      status: pending | in_progress | complete | failed  # D5: Dependencies, D6: Tech Debt
      output_file: structure.yml         # D7: Data Flows, D8: Critical Paths, D9: Git Intelligence
      started_at: ISO-8601 | null
      completed_at: ISO-8601 | null
      error: string | null
    # D2-D9 follow identical structure with their respective name and output_file

  finalize:
    validation: {status: pending | complete}
    checksums:  {status: pending | complete}
    diagrams:   {status: pending | complete}
    memory:     {status: pending | complete}
```

---

## Schema: `checksum.yml`

Enables incremental refresh by tracking file hashes and their dimension associations.

```yaml
generated_at: ISO-8601
algorithm: SHA256
files:
  - path: string
    hash: string
    size: integer
    dimensions: [string]   # which dimensions analyzed this file (D1, D2, etc.)
dimension_file_counts:
  D1: integer
  D2: integer
  D3: integer
  D4: integer
  D5: integer
  D6: integer
  D7: integer
  D8: integer
  D9: integer
```

---

## Schema: `debt-strategy.yml`

Produced by the `debt-strategy` workflow. Transforms D6 (Tech Debt) findings into a prioritized remediation plan with story drafts.

```yaml
summary: |
  {overview: total items, distribution by category, top 3 urgent items}
categories:
  safety: [{item, source_file, source_line, impact, effort, priority_score}]
  velocity: [{item, source_file, source_line, impact, effort, priority_score}]
  reliability: [{item, source_file, source_line, impact, effort, priority_score}]
  maintenance: [{item, source_file, source_line, impact, effort, priority_score}]
remediation_tiers:
  urgent:
    - item: string
      category: safety|velocity|reliability|maintenance
      story_draft:
        title: string
        scope: string
        acceptance_criteria: [string]
  strategic:
    - item: string
      category: safety|velocity|reliability|maintenance
      story_draft:
        title: string
        scope: string
        acceptance_criteria: [string]
  opportunistic:
    - item: string
      description: string
      trigger: "when touching {files}"
metrics:
  total_items: integer
  health_score_current: integer   # from tech-debt.yml
  projected_score_after_urgent: integer
```

---

## Schema: `dependency-audit.yml`

Produced by the `dependency-audit` workflow. Transforms D5 (Dependencies) findings into a risk-ranked upgrade plan with story drafts.

```yaml
summary: |
  {overview: total deps audited, critical count, outdated count, overlap count}
risks:
  critical:
    - package: string
      version: string
      issue: string
      cve: string | null
      upgrade_to: string
      breaking_changes: [string]
      story_draft:
        title: string
        scope: string
        acceptance_criteria: [string]
  outdated:
    - package: string
      current_version: string
      latest_version: string
      versions_behind: integer
      upgrade_difficulty: easy|moderate|hard
  overlap:
    - purpose: string
      libraries: [string]
      recommendation: string
      story_draft:
        title: string
        scope: string
        acceptance_criteria: [string]
  license:
    - package: string
      license: string
      issue: string
      recommendation: string
upgrade_plan:
  - priority: 1|2|3
    story_draft:
      title: string
      scope: string
      packages: [string]
      acceptance_criteria: [string]
    estimated_effort: small|medium|large
metrics:
  total_dependencies: integer
  healthy_percent: integer
  critical_count: integer
  outdated_count: integer
```

---

## Downstream Agent Loading Guide

Agents do NOT need to read this file. This section documents how agents should consume analysis output.

**Loading pattern:**
1. Read `manifest.yml` — verify analysis is complete
2. Read needed artifact `summary:` sections only (use YAML parsing or read first ~20 lines)
3. If deeper context needed, read the `details:` section of specific artifacts

**Agent-specific loading:**

| Agent | Read Summaries | Read Full Details |
|---|---|---|
| Architect | overview, structure, practices, dependencies | structure.details.modules |
| Scrummaster | structure, domain-model, entry-points | domain-model.details.entities |
| SW Engineer | practices, domain-model, critical-paths | practices.details.practices |
| Developer | practices, domain-model | practices.details (full — needs examples) |
| SW Quality | critical-paths, domain-model, git-intelligence | critical-paths.details.change_risk_index |
| Bug Diagnostician | data-flows, critical-paths, domain-model, git-intelligence, entry-points | critical-paths.details.cross_cutting_risk |
| CR Analyzer | structure, practices, critical-paths | practices.details.violation_catalog |
| Test Agent | practices, critical-paths | practices.details.practices (test patterns) |
