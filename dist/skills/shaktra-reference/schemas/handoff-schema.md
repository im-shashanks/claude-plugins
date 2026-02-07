# Handoff Schema

Defines `.shaktra/stories/<story_id>/handoff.yml` — the TDD state machine that tracks a story through plan → tests → code → quality → complete.

## Identity

```yaml
story_id: string          # matches story file id
tier: string              # "trivial" | "small" | "medium" | "large"
current_phase: string     # "plan" | "tests" | "code" | "quality" | "complete" | "failed"
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
    - pattern: string        # principle or pattern name
      location: string       # file or component where applied
      guidance: string       # actionable implementation instruction
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
```

## Important Decisions

```yaml
important_decisions:
  - category: string      # from decisions-schema categories
    title: string
    summary: string
    guidance: [string]    # 1-5 actionable rules
```

## Quality Findings

```yaml
quality_findings:
  - severity: string      # P0 | P1 | P2 | P3
    dimension: string     # quality dimension (A-M)
    description: string
    file: string
    line: integer
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

1. `current_phase` must be one of the 6 allowed values.
2. `completed_phases` must be a prefix of [plan, tests, code, quality] — phases cannot be skipped.
3. `tier` must match the story file's tier.
4. `test_summary.test_count` must match `plan_summary.test_plan.test_count` (or include a variance note).
5. `coverage` is checked against `settings.tdd.coverage_threshold` or `settings.tdd.hotfix_coverage_threshold` depending on tier.
6. `memory_captured` must be `true` before transitioning to `complete`.
