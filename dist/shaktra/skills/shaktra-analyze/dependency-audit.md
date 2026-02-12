# Dependency Audit — Dependency Health & Upgrade Planning

Transforms D5 (Dependencies) analysis findings into a risk-ranked upgrade plan with auto-generated story drafts. Executed by CBA Analyzer in `dependency-audit` mode.

---

## Prerequisites

- `.shaktra/analysis/dependencies.yml` must exist (D5 dimension output)
- If missing, the orchestrator runs D5 first before invoking this workflow

---

## Risk Categorization Framework

Categorize each dependency risk from `dependencies.yml` into exactly one category:

### Critical
Known CVEs, abandoned libraries (no commits in 12+ months with open security issues), deprecated packages with no migration path.

**Indicators:** CVE entries in vulnerability scan, npm/pip audit findings, "deprecated" flag in registry, last publish date > 2 years with unresolved issues.

**Action:** One story per Critical item — each gets dedicated remediation.

### Outdated
Major version behind current stable release. Minor version gaps are informational only unless they include security fixes.

**Indicators:** Major version difference >= 1, changelog shows breaking changes between current and latest, deprecation warnings in current version.

**Action:** Grouped upgrade stories — batch related packages (e.g., "Upgrade all testing libraries", "Upgrade all Express-related packages").

### Overlap
Multiple libraries serving the same purpose (e.g., two HTTP clients, two date libraries, two validation libraries).

**Indicators:** `dependencies.yml` overlap analysis, multiple packages with identical or highly overlapping functionality.

**Action:** Pick a winner based on maintenance health, community size, and API fit. Create a migration story to consolidate.

### License
Incompatible or restrictive licenses that conflict with the project's license or intended distribution model.

**Indicators:** GPL in a proprietary project, AGPL in a SaaS without source disclosure, license field missing or "UNLICENSED".

**Action:** Assess risk and recommend alternative packages or legal review.

---

## Upgrade Difficulty Assessment

For each Critical and Outdated item, assess upgrade difficulty:

| Difficulty | Criteria |
|---|---|
| `easy` | No breaking changes, drop-in replacement, < 1 hour |
| `moderate` | Minor breaking changes, API surface changes, 1-3 days with testing |
| `hard` | Major breaking changes, API redesign, data migration needed, > 3 days |

**Assessment inputs:**
1. Read changelog/migration guide between current and target version
2. Count breaking changes listed
3. Check if the package provides codemods or automated migration tools
4. Assess how widely the package is used in the codebase (from `dependencies.yml` usage data)

---

## Story Generation Rules

### Critical Items — One Story Each

**Title:** `[Security] Remediate {package}@{version} — {CVE or issue}`

**Scope:** All files importing or depending on the affected package.

**Acceptance criteria:**
1. Package upgraded to {target_version} or replaced with {alternative}
2. All existing tests pass after upgrade
3. No new vulnerability findings for this package
4. Breaking changes addressed (list specific API changes if applicable)

### Outdated Items — Grouped Stories

Group by ecosystem affinity (testing tools together, framework packages together, utility packages together).

**Title:** `[Upgrade] Update {group_name} packages to latest`

**Scope:** All packages in the group with their importing files.

**Acceptance criteria:**
1. All packages in group upgraded to specified versions
2. All existing tests pass after upgrade
3. Deprecated API usage replaced with current equivalents
4. No new type errors or linting failures introduced

### Overlap Items — Consolidation Stories

**Title:** `[Consolidate] Standardize on {winner} for {purpose}`

**Scope:** All files using the deprecated library, plus the package manifest.

**Acceptance criteria:**
1. All usage of {loser} replaced with {winner}
2. {loser} removed from dependencies
3. All existing tests pass
4. No functionality regression

---

## Upgrade Plan Prioritization

Assemble an ordered upgrade plan from all generated stories:

| Priority | Criteria |
|---|---|
| 1 | Critical items (CVEs, abandoned with security issues) |
| 2 | Outdated items with `hard` difficulty (schedule early — they take longer) |
| 3 | Outdated items with `easy`/`moderate` difficulty + Overlap consolidations |

**Effort estimation:**
- `small`: 1-2 story points — drop-in upgrade, no breaking changes
- `medium`: 3-5 story points — some API changes, moderate testing
- `large`: 8+ story points — major migration, extensive testing, possible data changes

---

## Metrics

Calculate and include in the output:

- `total_dependencies`: count of all dependencies audited
- `healthy_percent`: percentage of dependencies that are current (within 1 minor version) and have no known issues
- `critical_count`: number of Critical risk items
- `outdated_count`: number of Outdated risk items (major version behind)

---

## Output Schema

Write to `.shaktra/analysis/dependency-audit.yml` following the schema in `analysis-output-schemas.md`.

The `summary:` section (~400 tokens) must include:
- Total dependencies audited and health distribution
- Critical items requiring immediate attention (with CVE IDs if applicable)
- Number of outdated packages and upgrade difficulty distribution
- Overlap findings and consolidation recommendations
- Recommended upgrade sequence (what to tackle first)

---

## CBA Analyzer Prompt Template

```
You are the shaktra-cba-analyzer agent in dependency-audit mode.

Input: .shaktra/analysis/dependencies.yml
Output: .shaktra/analysis/dependency-audit.yml

1. Read dependencies.yml — load all findings
2. Read dependency-audit.md — this file, for risk categorization and story generation rules
3. Read analysis-output-schemas.md — for output schema
4. Categorize each dependency risk into Critical/Outdated/Overlap/License
5. Assess upgrade difficulty for Critical and Outdated items
6. Generate story drafts: one per Critical, grouped for Outdated, consolidation for Overlap
7. Build prioritized upgrade plan
8. Calculate metrics
9. Write output to .shaktra/analysis/dependency-audit.yml
```
