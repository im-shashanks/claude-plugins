# Analyze Workflow

Deep-dive guide to Shaktra's 9-dimension brownfield codebase assessment.

## When to Use

- On-boarding to an unfamiliar codebase
- Planning a major refactoring effort
- Assessing technical debt before sprint planning
- Evaluating acquisition targets or inherited projects
- Establishing a quality baseline before new feature work

Run `/shaktra:analyze` in any brownfield project with a `.shaktra/` directory initialized.

## How It Works

The analysis runs in two stages, then produces structured output that every downstream agent can consume.

**Stage 1 -- Pre-Analysis (tool-based, sequential)**
Extracts ground truth using Glob, Grep, and Bash. No LLM interpretation. Produces `static.yml` (file inventory, dependency graph, call graph, type hierarchy, detected patterns) and `overview.yml` (project identity, tech stack, build system). This factual foundation prevents hallucinated findings in Stage 2.

**Stage 2 -- Deep Analysis (LLM-driven, parallel)**
Nine specialized CBA Analyzer agents each consume the Stage 1 facts and analyze one dimension. When team mode is available, agents run in parallel across four team members. In single-session mode, all nine run as parallel sub-agents within one session.

**Stage 3 -- Validation and Output**
Cross-references all dimension outputs, generates checksums for incremental refresh, updates the manifest, and presents the summary report.

## The 9 Dimensions

### D1: Architecture and Structure

Answers: *How is this codebase organized?*

Analyzes module inventory, module relationships, architectural patterns (MVC, hexagonal, clean architecture), boundary violations, and convention violations. Produces a Mermaid dependency diagram. Detects whether patterns are consistent or mixed across the codebase. Every boundary violation cites a specific import path; every convention violation cites the dominant pattern first, then the deviating instance with file and line.

Output: `structure.yml`

### D2: Domain Model and Business Rules

Answers: *What business logic does this code encode?*

Maps entities and value objects, state machines with transitions and guards, business invariants (and where they are enforced), conditional business rules, and edge cases discovered from code comments, tests, and error handling. Traces error propagation paths from origin through handler chains to final catch points, flagging swallowed errors.

Output: `domain-model.yml`

### D3: Entry Points and Interfaces

Answers: *How do external actors interact with this system?*

Catalogs HTTP/REST endpoints, event handlers, CLI commands, scheduled jobs, webhooks, WebSocket endpoints, and internal interfaces (shared libraries, SDK surfaces). For each: the handler function, its dependencies, authentication requirements, and data contracts.

Output: `entry-points.yml`

### D4: Coding Practices and Conventions

Answers: *How is code written in this project?*

Analyzes 14 practice areas: type annotations, docstrings, import organization, dependency injection, API patterns, testing patterns, database patterns, error handling, logging, configuration, authentication, async patterns, file organization, and code structure. Detects naming conventions across files, functions, classes, variables, and tests. Extracts canonical code examples (10-40 lines from the actual codebase) for each detected pattern, teaching downstream agents "how we do things here." Produces a violation catalog mapping deviations from established conventions.

Output: `practices.yml`

### D5: Dependencies and Tech Stack

Answers: *Are our dependencies healthy?*

Audits direct and notable transitive dependencies: version currency, maintenance status (active, maintenance-only, abandoned, archived), known CVEs via package manager audit commands, license compatibility, and library overlap (multiple libraries serving the same purpose).

Output: `dependencies.yml`

### D6: Technical Debt and Security

Answers: *How healthy is this codebase overall?*

Counts debt indicators (TODO, FIXME, HACK, dead code, disabled tests). Identifies complexity hotspots with quantitative metrics: average and maximum function length, nesting depth, file length, test-to-source ratio. Assesses security posture: hardcoded secrets, injection risks, XSS vectors, missing auth, overly permissive CORS. Produces an aggregate 1-10 health score broken down by code quality, test coverage, security, and consistency.

Output: `tech-debt.yml`

### D7: Data Flows and Integration

Answers: *How does data move through the system?*

Traces data from entry point through processing to storage, classifying flows by criticality (critical: revenue-impacting; important: feature-impacting; reference: supporting). Maps all integration points: APIs, databases, queues, caches, third-party services. Flags integration gotchas that cause production incidents -- race conditions, TOCTOU bugs, webhook ordering issues, cache consistency problems, non-atomic operations, timeout cascades, and retry storms.

Output: `data-flows.yml`

### D8: Critical Paths and Risk

Answers: *Where do we need to be most careful?*

Identifies code areas by risk category: revenue-critical, security-sensitive, performance-critical, and data-integrity. For each critical path, assesses blast radius (contained, service-level, cross-service, or user-facing). Mines lessons learned from git history (frequent bug-fix commits), code comments (warnings, workarounds), and regression tests. Produces a change risk index per file and a cross-cutting risk score combining critical path membership, tech debt, test coverage, git change frequency, and coupling.

Output: `critical-paths.yml`

### D9: Git Intelligence

Answers: *How has this codebase evolved?*

All data extracted via git commands, not LLM inference. Identifies hotspots (files with most commits), bug-fix density (ratio of fix commits to total), co-change patterns (files that frequently change together, flagging hidden coupling when co-changing files have no import relationship), knowledge distribution (bus factor per file), and code age (fresh, recent, aging, stale).

Output: `git-intelligence.yml`

## Understanding Health Scores

The aggregate health score in `tech-debt.yml` is rated 1-10 and broken into four sub-scores:

| Sub-score | What it measures |
|---|---|
| Code quality | Complexity hotspots, function/file length, nesting depth, dead code |
| Test coverage | Test-to-source ratio, untested modules, coverage gaps |
| Security | Hardcoded secrets, injection risks, missing auth, insecure dependencies |
| Consistency | Adherence to detected conventions, pattern uniformity |

Scores are evidence-based: every finding cites specific files and line numbers. A score of 7+ indicates a well-maintained area; 4-6 suggests targeted improvements needed; below 4 signals systemic issues requiring dedicated remediation sprints.

## What Gets Stored

All output lives in `.shaktra/analysis/` as YAML files:

| File | Source | Purpose |
|---|---|---|
| `static.yml` | Stage 1 | Ground truth: file inventory, dependency graph, call graph, type hierarchy |
| `overview.yml` | Stage 1 | Project identity, tech stack, build system, entry files |
| `structure.yml` | D1 | Module inventory, relationships, boundary violations, Mermaid diagram |
| `domain-model.yml` | D2 | Entities, state machines, invariants, edge cases, error propagation |
| `entry-points.yml` | D3 | All external interfaces with handlers and data contracts |
| `practices.yml` | D4 | Coding conventions, canonical examples, violation catalog |
| `dependencies.yml` | D5 | Dependency health, CVEs, version currency, overlaps |
| `tech-debt.yml` | D6 | Health score, debt indicators, security findings, quantitative metrics |
| `data-flows.yml` | D7 | Data flow traces, integration points, integration gotchas |
| `critical-paths.yml` | D8 | Risk categories, blast radius, change risk index, cross-cutting risk |
| `git-intelligence.yml` | D9 | Hotspots, bug-fix density, co-change patterns, knowledge distribution |
| `manifest.yml` | Orchestrator | Completion state for resumability (which stages/dimensions are done) |
| `checksum.yml` | Orchestrator | File hashes for incremental refresh |

Derivative artifacts (produced by follow-up workflows):
- `debt-strategy.yml` -- prioritized remediation plan with story drafts
- `dependency-audit.yml` -- risk-ranked upgrade plan with story drafts

Every artifact (except static, manifest, checksum) starts with a `summary:` section of 300-650 tokens. Agents load summaries for quick context and only read full `details:` when deeper information is needed. Total summary budget across all dimensions is approximately 4,450 tokens.

## How Improvement Roadmaps Are Generated

After the base analysis, two derivative workflows transform findings into actionable plans:

**Debt Strategy** (`/shaktra:analyze` with "debt strategy" intent)
Takes D6 (Technical Debt) findings and categorizes them into safety, velocity, reliability, and maintenance buckets. Each item gets an impact and effort score, producing a priority ranking. Items are grouped into three remediation tiers:
- **Urgent** -- fix now, with generated story drafts ready for sprint planning
- **Strategic** -- plan for upcoming sprints, with story drafts
- **Opportunistic** -- fix when touching nearby files

Includes a projected health score improvement if urgent items are resolved.

**Dependency Audit** (`/shaktra:analyze` with "dependency audit" intent)
Takes D5 (Dependencies) findings and produces risk-ranked categories: critical (CVEs, abandoned packages), outdated (version gaps), overlap (redundant libraries), and license issues. Generates an upgrade plan with prioritized story drafts and breaking change warnings.

Both workflows output story drafts that feed directly into `/shaktra:tpm` for sprint planning.

## Using Findings for Planning

After analysis completes, findings flow into the rest of the Shaktra workflow:

1. **Run `/shaktra:tpm`** -- the Architect agent automatically consumes analysis artifacts (overview, structure, practices, dependencies summaries) to inform technical design decisions
2. **Sprint planning** -- the Scrummaster uses domain model, entry points, and structure summaries to scope stories accurately
3. **Development** -- the Developer agent reads practices and domain model to generate code matching existing conventions
4. **Quality checks** -- SW Quality uses critical paths and git intelligence to focus review effort on highest-risk areas
5. **Bug diagnosis** -- the Bug Diagnostician cross-references data flows, critical paths, domain model, git intelligence, and entry points to trace root causes

**Incremental refresh:** After code changes, run `/shaktra:analyze refresh` to recompute checksums, identify stale dimensions, and selectively re-analyze only what changed.

**Targeted analysis:** Analyze a single dimension with `/shaktra:analyze architecture` or `/shaktra:analyze practices` when you only need to update one area.

## Example Output

After a full analysis run, the summary report looks like:

```
## Codebase Analysis Complete

Project: acme-api (TypeScript)
Artifacts: .shaktra/analysis/ (13 files)

### Dimension Summary
| Dimension                      | Status   | Key Finding                                      |
|--------------------------------|----------|--------------------------------------------------|
| D1: Architecture & Structure   | complete | Clean layering, 3 boundary violations in data layer |
| D2: Domain Model               | complete | 12 entities, 2 state machines, 4 undocumented invariants |
| D3: Entry Points               | complete | 47 HTTP endpoints, 8 missing auth middleware     |
| D4: Coding Practices           | complete | High consistency, 6 convention violations        |
| D5: Dependencies               | complete | 2 abandoned packages, 1 critical CVE             |
| D6: Tech Debt & Security       | complete | Health: 7/10, 23 TODOs, no critical security gaps |
| D7: Data Flows                 | complete | 3 critical flows, timeout cascade risk in payment |
| D8: Critical Paths             | complete | Payment + auth paths high-risk, bus factor 1     |
| D9: Git Intelligence           | complete | 5 hotspot files, hidden coupling in utils/helpers |

### Next Steps
- Run /shaktra:tpm to start planning -- architect will consume analysis automatically
- Run /shaktra:analyze refresh after code changes to update stale dimensions
```
