# Comprehensive Review

Full quality assessment for the QUALITY phase of the TDD pipeline. Uses 14 dimensions (A-M from `quality-dimensions.md` + Dimension N: Plan Adherence) plus coverage verification and decision consolidation.

**When:** QUALITY phase of TDD pipeline (Medium+ tiers). Thorough tier adds expanded analysis.

---

## Review Process

### 1. Load Context

Read before reviewing:
- Story YAML at `.shaktra/stories/<story_id>.yml`
- Handoff at `.shaktra/stories/<story_id>/handoff.yml`
- Implementation plan at `.shaktra/stories/<story_id>/implementation_plan.md`
- All files in `handoff.code_summary.files_modified`
- All files in `handoff.test_summary.test_files`
- `.shaktra/settings.yml` — for threshold values
- `.shaktra/memory/decisions.yml` — for cross-story consistency

### 2. Run Tests and Verify Coverage

Execute the project's test suite using the configured `test_framework` and `coverage_tool` from settings.

**Verify:**
- All tests pass (`all_tests_green` confirmed by actual execution, not self-reported)
- Coverage meets or exceeds the tier threshold from `settings.tdd`
- Coverage comes from behavioral tests (not empty assertion tests that just execute code)

If tests fail or coverage is below threshold, emit `COVERAGE_GATE_FAILED` and stop the review — return to the developer for fixes.

### 3. Apply Dimensions A-M

Review using each of the 13 dimensions from `quality-dimensions.md`. For each dimension:

1. Apply the 3 key checks defined in the dimension
2. Check the P0 trigger condition
3. Record findings with: severity, dimension letter, file, line, issue description, guidance

**Dimension priority by scope:**
- Integration scope: Emphasize B (Failure Modes), F (Observability), G (Performance)
- Security scope: Emphasize A (Contract & API), E (Security), K (Configuration)
- Data scope: Emphasize C (Data Integrity), D (Concurrency), J (Deployment)

Skip dimensions that are clearly not applicable (e.g., Dimension D: Concurrency for a purely synchronous, single-threaded change). Document the skip reason.

### 4. Apply Dimension N — Plan Adherence

Verify the implementation matches the agreed plan:

**N.1 — Components Match Plan**
Compare `handoff.plan_summary.components` against actual files created. Every planned component must exist; every created file must trace to a planned component.
- Missing planned component → P0 (missing risk prevention)
- Extra unplanned component → P2 (document justification in code_summary)

**N.2 — Patterns Applied**
Verify each entry in `handoff.plan_summary.patterns_applied` was actually implemented.
- Pattern planned but not applied → P1
- Pattern applied differently → P2 (acceptable if justified in code_summary)

**N.3 — Scope Risks Mitigated**
For each risk in `handoff.plan_summary.scope_risks`, verify the prevention strategy was implemented.
- Risk identified but prevention missing → P0
- Prevention implemented differently → P2 (acceptable if justified)

**N.4 — Deviations Documented**
Any deviation from the plan must be documented in `handoff.code_summary` with justification.
- Undocumented deviation → P1

### 5. Quick-Check Cross-Reference

Read `handoff.quality_findings` — this contains findings from earlier quick-check gates (Plan, Test, Code), persisted by the orchestrator after each gate.

For each prior P0 or P1 finding where `resolved: false`:
- Verify the issue is resolved in the current code
- If still present: escalate to P0 (recurring finding after fix attempt)
- If resolved: confirm as addressed

If `quality_findings` is empty, skip this step (first-time review with no prior gates).

### 6. Decision Consolidation

Extract decisions made during development that should persist:

1. Read `handoff.important_decisions`
2. For each decision:
   - Does it match an existing entry in `.shaktra/memory/decisions.yml`? → Skip (no duplicate)
   - Is it specific enough to be actionable? → Promote
   - Is it too story-specific to generalize? → Skip
3. Return qualifying decisions in `decisions_promoted` output — the orchestrator writes them to `.shaktra/memory/decisions.yml`

### 7. Cross-Story Consistency

Compare this story's decisions and patterns against existing `decisions.yml`:
- Does this implementation contradict a prior decision? → Flag as P1
- Does it establish a new pattern not yet recorded? → Recommend recording
- Does it deviate from an established pattern? → Flag as P2 if unjustified

---

## Thorough Tier — Expanded Review

For Large tier stories, add these additional review dimensions after the standard 14:

**Architecture Governance:**
- Apply ARC-01 through ARC-06 from `architecture-checks.md`
- For Large tier: additionally verify new modules don't fragment existing bounded contexts
- Cross-reference with `.shaktra/analysis/structure.yml` if analysis exists

**Performance Profiling Review:**
- Are there O(n^2) or worse algorithms on user-controlled input?
- Are database queries optimized (no N+1, appropriate indexing)?
- Are caching opportunities utilized where data is read-heavy?

**Dependency Audit:**
- Are all new dependencies actively maintained and appropriate for the use case?
- Do new dependencies introduce license incompatibilities?
- Could any new dependency be replaced with stdlib functionality?

---

## Output Format

```yaml
comprehensive_findings:
  - severity: P0|P1|P2|P3
    dimension: A|B|C|...|M|N
    check: "dimension check identifier"
    file: "path/to/file.py"
    line: 42
    issue: "Specific description of the problem"
    evidence: "Test result, log line, or code reference proving the issue"
    guidance: "Specific action to resolve"

coverage_result:
  tests_pass: true|false
  coverage_percent: integer
  tier_threshold: integer
  meets_threshold: true|false

decisions_promoted:
  - category: "category from decisions-schema"
    title: "decision title"
    summary: "what was decided and why"

cross_story_issues:
  - type: contradiction|new_pattern|deviation
    description: "what was found"
    existing_decision: "reference to decisions.yml entry"
```

## Evidence Rule

Every finding must include evidence — a test result, log line, command output, or code reference. "This looks wrong" is never sufficient. "Line 42 calls `requests.get(url)` without a `timeout` parameter — see CQ-03" is.

## Gate Logic

After completing the review, apply the merge gate from `severity-taxonomy.md`:
- P0 > 0 → emit `QUALITY_BLOCKED`
- P1 > `settings.quality.p1_threshold` → emit `QUALITY_BLOCKED`
- Otherwise → emit `QUALITY_PASS`
