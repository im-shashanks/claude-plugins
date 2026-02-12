# Handoff Schema

Defines `.shaktra/stories/<story_id>/handoff.yml` — the TDD state machine that tracks a story through plan → tests → code → quality → complete.

## Identity

```yaml
story_id: string          # matches story file id
tier: string              # "trivial" | "small" | "medium" | "large"
current_phase: string     # "pending" | "plan" | "tests" | "code" | "quality" | "complete" | "failed"
completed_phases: [string] # append-only log of completed phases
```

## Plan Summary

```yaml
plan_summary:
  components:
    - name: string
      file: string
      responsibility: string   # single sentence, SRP
  test_plan:
    test_count: integer
    test_types: [string]       # "unit" | "integration" | "contract"
    mocks_needed: [string]
    edge_cases: [string]
  implementation_order: [string] # file paths, minimal-dependency order
  patterns_applied:
    - pattern: string        # design pattern, architectural pattern, or quality principle name
      location: string       # file or component where applied
      guidance: string       # actionable implementation instruction
      source: string         # "decision" | "analysis" | "principle" | "design-doc"
  scope_risks:
    - risk: string           # what could go wrong
      likelihood: string     # "low" | "medium" | "high"
      prevention: string     # how the plan mitigates it
```

## Test Summary

```yaml
test_summary:
  all_tests_red: boolean    # must be true before advancing
  test_count: integer
  test_files: [string]
```

## Code Summary

```yaml
code_summary:
  all_tests_green: boolean  # must be true before advancing
  coverage: integer         # percentage — checked against tier threshold
  files_modified: [string]
  deviations:               # plan deviations — empty list if none
    - change: string        # what diverged from the plan
      justification: string # why the deviation was necessary
```

## Important Decisions

```yaml
important_decisions:
  - category: string      # from decisions-schema categories
    title: string
    summary: string
    guidance: [string]    # 1-5 actionable rules
```

**Pattern decisions must be captured.** During implementation, if any of the following occur, add an `important_decision` with `category: consistency`:
- A **new design pattern** is introduced (e.g., "Repository pattern for all data access in this project")
- A **new architectural convention** is established (e.g., "All services accept dependencies via constructor injection")
- A **deviation from existing patterns** is made with justification
- A **canonical example** worth replicating is created (reference the file path in guidance)

These decisions persist in `decisions.yml` and are loaded by the architect, sw-engineer, and developer agents for all future stories — ensuring pattern coherence across the product lifecycle.

## Quality Findings

**Population:** The orchestrator persists findings to this field after each quality gate (QUICK_CHECK and COMPREHENSIVE). SW Quality returns findings as output; the orchestrator writes the latest findings here. The `check_p0_findings` hook reads this field at workflow completion — it filters out findings with `resolved: true`.

**Note:** SW Quality agent output may include additional fields (`check_id`, `evidence`, `guidance`) beyond the schema below. The orchestrator writes the full agent output; consumers should tolerate extra fields.

```yaml
quality_findings:
  - severity: string      # P0 | P1 | P2 | P3
    dimension: string     # quality dimension (A-M)
    gate: string          # "plan" | "test" | "code" | "quality" — which gate produced this
    issue: string         # specific description of the finding
    file: string
    line: integer
    resolved: boolean     # true if fixed in a subsequent fix loop
```

## Memory Guard

```yaml
memory_captured: boolean  # default: false — must be true before completion
```

## Phase Transitions

| From | To | Guard |
|---|---|---|
| plan | tests | `plan_summary` is populated; `test_plan.test_count > 0` (skip for Trivial) |
| tests | code | `test_summary.all_tests_red == true` (skip for Trivial) |
| code | quality | `code_summary.all_tests_green == true`; coverage ≥ tier threshold from `settings.tdd` |
| quality | complete | No P0 findings; P1 count ≤ `settings.quality.p1_threshold`; `memory_captured == true` |
| _any_ | failed | Unrecoverable error or user abort |

## Validation Rules

1. `current_phase` must be one of the 7 allowed values.
2. `completed_phases` must be a prefix of [plan, tests, code, quality] — phases cannot be skipped.
3. `tier` must match the story file's tier.
4. `test_summary.test_count` must match `plan_summary.test_plan.test_count` (or include a variance note).
5. `coverage` is checked against `settings.tdd.coverage_threshold` or `settings.tdd.hotfix_coverage_threshold` depending on tier.
6. `memory_captured` must be `true` before transitioning to `complete`.
