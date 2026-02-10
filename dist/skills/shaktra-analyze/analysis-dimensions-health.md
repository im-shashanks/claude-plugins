# Analysis Dimensions — Health (D5-D8)

Dimensions that answer "How HEALTHY is this codebase?" — its dependencies, debt, data flows, and risk areas.

**Used by:** shaktra-cba-analyzer agent during `/shaktra:analyze` workflow.
**Input dependency:** All dimensions consume `static.yml` (ground truth) and `overview.yml` (project context).
**Companion:** `analysis-dimensions-core.md` defines D1-D4, `analysis-dimensions-git.md` defines D9.

---

## D5: Dependencies & Tech Stack → `dependencies.yml`

**Scope:** All project dependencies, their health, version currency, and potential risks.

**What to analyze:**
1. **Direct dependencies** — name, version, purpose, last updated, license
2. **Transitive dependencies** — significant transitive deps that affect the project
3. **Dependency health** — maintenance status (active, maintenance-only, abandoned, archived)
4. **Version currency** — current vs latest, major version gaps
5. **Known vulnerabilities** — check for known CVEs via package manager audit commands
6. **Dependency overlap** — multiple libraries serving the same purpose

**Evidence requirements:**
- Versions from actual lockfile/manifest, not guessed
- Health status based on recent commit activity, issue responsiveness
- CVE data from `npm audit`, `pip audit`, `cargo audit`, or equivalent

**Output structure:**
```yaml
summary: |
  {Self-contained 300-token overview: total deps, health distribution,
   critical CVEs, notable risks}
details:
  direct:
    - name: string
      version: string
      purpose: string
      health: active | maintenance | abandoned | archived
      latest_version: string
      license: string
  transitive_notable:
    - name: string
      pulled_by: string
      risk: string
  vulnerabilities:
    - package: string
      severity: critical | high | medium | low
      cve: string
      description: string
  overlaps:
    - purpose: string
      libraries: [string]
      recommendation: string
```

---

## D6: Technical Debt & Security → `tech-debt.yml`

**Scope:** Code quality issues, technical debt indicators, security posture, and an overall health score.

**What to analyze:**
1. **Debt indicators** — TODO/FIXME/HACK counts with context, dead code, unused imports, disabled tests, commented-out code blocks
2. **Complexity hotspots** — files/functions with high cyclomatic complexity, deeply nested logic, long functions/methods. Produce quantitative metrics: total files/lines, avg/max function length, avg/max file length, nesting depth counts, test-to-source ratio.
3. **Test health** — test-to-source ratio, test coverage gaps (modules with no tests), flaky test indicators
4. **Security posture** — hardcoded secrets, SQL injection risks, XSS vectors, insecure dependencies, missing auth on endpoints, overly permissive CORS
5. **Health score** — aggregate 1-10 score based on debt density, test coverage, security issues, code consistency

**Evidence requirements:**
- Debt indicators cite specific files and line numbers
- Complexity metrics based on actual code analysis (nesting depth, function length)
- Security findings cite specific code patterns, not theoretical risks

**Output structure:**
```yaml
summary: |
  {Self-contained 350-token overview: health score, debt density,
   critical security issues, test coverage status}
details:
  health_score: integer  # 1-10
  health_breakdown:
    code_quality: integer
    test_coverage: integer
    security: integer
    consistency: integer
  debt:
    todo_count: integer
    fixme_count: integer
    hack_count: integer
    dead_code_files: [string]
    disabled_tests: [string]
    hotspots:
      - file: string
        issue: string  # high complexity, deep nesting, long function
        metric: string
  security:
    - category: string
      severity: critical | high | medium | low
      location: string
      description: string
      remediation: string
  test_health:
    test_to_source_ratio: string
    untested_modules: [string]
    coverage_estimate: string
  quantitative_metrics:
    total_source_files: integer
    total_source_lines: integer
    avg_function_length: integer
    max_function_length: {file: string, function: string, lines: integer}
    avg_file_length: integer
    max_file_length: {file: string, lines: integer}
    deeply_nested_functions: integer
    long_functions: integer
    test_to_source_ratio: float
    files_without_tests: integer
    percent_files_tested: float
```

---

## D7: Data Flows & Integration → `data-flows.yml`

**Scope:** How data moves through the system, integration points with external services, and critically: integration gotchas that cause production incidents.

**What to analyze:**
1. **Data flows** — trace data from entry point through processing to storage/response. Classify each flow by criticality:
   - **Critical:** Revenue-impacting, data-loss-risking (payment, order, user creation)
   - **Important:** Feature-impacting (search, notification, reporting)
   - **Reference:** Supporting flows (logging, metrics, health checks)
2. **Integration points** — all external service connections: APIs, databases, queues, caches, file systems, third-party services
3. **Integration gotchas** — the non-obvious failure modes that cause production incidents:
   - Race conditions (concurrent writes to same resource)
   - TOCTOU bugs (check-then-act with stale data)
   - Webhook ordering issues (events arriving out of order)
   - Cache consistency problems (stale reads after writes)
   - Non-atomic multi-step operations (partial failure mid-sequence)
   - Timeout cascades (one slow service blocking the chain)
   - Retry storms (retries amplifying load during outages)

**Evidence requirements:**
- Data flows traced through actual code paths, not architecture diagrams
- Integration points verified via connection config, client instantiation
- Gotchas cite specific code patterns where the risk exists

**Output structure:**
```yaml
summary: |
  {Self-contained 500-token overview: flow count by tier,
   integration points, critical gotchas}
details:
  flows:
    - name: string
      tier: critical | important | reference
      entry_point: string
      path: [string]  # ordered list of file:function through the flow
      data_transforms: [string]
      storage: string
      risks: [string]
  integrations:
    - service: string
      type: api | database | queue | cache | filesystem | third_party
      connection: string  # config/env reference
      timeout: string | none
      retry: string | none
      circuit_breaker: string | none
  gotchas:
    - type: race_condition | toctou | webhook_ordering | cache_consistency | non_atomic | timeout_cascade | retry_storm
      location: string
      description: string
      impact: string
      current_mitigation: string | none
```

---

## D8: Critical Paths & Risk → `critical-paths.yml`

**Scope:** Code paths that require extra caution — revenue-critical, security-sensitive, performance-critical, and data-integrity code. Includes blast radius assessment and lessons learned from the codebase's history.

**What to analyze:**
1. **Critical path identification** — classify code areas by risk category:
   - **Revenue-critical:** Payment processing, billing, subscription management, order fulfillment
   - **Security-sensitive:** Authentication, authorization, encryption, PII handling, secret management
   - **Performance-critical:** Hot paths under load, real-time processing, bulk operations
   - **Data-integrity:** Migration paths, schema changes, data transformations, backup/restore
2. **Blast radius assessment** — for each critical path, what breaks if it fails? How many users affected? Is the failure contained or cascading?
3. **Lessons learned from history** — evidence of past issues discovered from:
   - Git history: files with frequent bug-fix commits (many `fix:` prefixed commits)
   - Code comments: warnings, workarounds, known limitations
   - Error handling: defensive code suggesting past incidents
   - Test edge cases: regression tests suggesting past bugs
4. **Change risk index** — which files/modules require the most caution when modifying? Based on: criticality, complexity, coupling, historical bug density.
5. **Cross-cutting risk** — combine critical path membership, tech debt, test coverage, git change frequency, and coupling into a composite risk score per file. Requires reading `tech-debt.yml` (D6 output) and `git-intelligence.yml` (D9 output, if available). Reference the source dimension for each risk factor.

**Evidence requirements:**
- Critical paths traced to actual code locations, not theoretical
- Blast radius derived from dependency graph (who calls this code?)
- Lessons learned cite specific commits, comments, or test names
- Change risk index based on measurable factors
- Cross-cutting risk: reference source dimension for each risk factor

**Output structure:**
```yaml
summary: |
  {Self-contained 400-token overview: critical path count by category,
   highest-risk areas, key lessons learned}
details:
  critical_paths:
    - name: string
      category: revenue | security | performance | data_integrity
      files: [string]
      blast_radius:
        scope: contained | service | cross_service | user_facing
        affected: string
      current_protections: [string]
  lessons_learned:
    - source: git_history | code_comment | error_handling | regression_test
      location: string
      lesson: string
      implication: string  # what this means for future changes
  change_risk_index:
    - file: string
      risk: high | medium | low
      factors: [string]  # criticality, complexity, coupling, bug_density
      recommendation: string
  cross_cutting_risk:
    - file: string
      risk_factors:
        on_critical_path: boolean
        categories: [string]
        tech_debt_present: boolean
        debt_items: [string]
        test_coverage: none | partial | adequate
        change_frequency: high | medium | low
        coupling_score: high | medium | low
      composite_risk: critical | high | medium | low
      recommendation: string
```
