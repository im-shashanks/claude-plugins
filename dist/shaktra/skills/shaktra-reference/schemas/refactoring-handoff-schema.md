# Refactoring Handoff Schema

Defines `.shaktra/refactoring/<target>/refactoring-handoff.yml` — the state machine that tracks a refactoring session through ASSESS → FORTIFY → TRANSFORM → VERIFY → MEMORY.

## Identity

```yaml
target: string              # file or module path being refactored
tier: string                # "targeted" | "structural"
current_phase: string       # "pending" | "assess" | "fortify" | "transform" | "verify" | "complete" | "failed"
completed_phases: [string]  # append-only log
```

## Assessment Summary

```yaml
assessment:
  smells_detected:
    - id: string            # smell ID (BL-01, CP-02, etc.)
      location: "file:line"
      severity: string      # from smell catalog
      description: string
  proposed_transforms:
    - id: string            # transform ID (EX-01, MV-02, etc.)
      target_smell: string  # smell ID being addressed
      description: string
      risk: low | medium | high
      order: integer        # execution order
  baseline_metrics:
    test_count: integer
    coverage: integer       # percentage
    files_in_scope: integer
```

## Fortify Summary

```yaml
fortify:
  coverage_before: integer  # percentage
  coverage_after: integer   # after characterization tests
  characterization_tests_added: integer
  safety_threshold_met: boolean
  force_mode: boolean       # user acknowledged risk — no sufficient tests
```

## Transform Log

```yaml
transforms:
  - id: string              # transform ID
    status: applied | reverted | skipped
    files_changed: [string]
    tests_after: pass | fail
    notes: string           # reason for revert/skip if applicable
```

## Verify Summary

```yaml
verify:
  all_tests_green: boolean
  coverage_change: integer  # delta from baseline (should be >= 0)
  smells_resolved: integer
  smells_remaining: integer
  metrics_improved: boolean
```

## Memory Guard

```yaml
memory_captured: boolean    # default: false — must be true before completion
```

## Phase Transitions

| From | To | Guard |
|---|---|---|
| assess | fortify | `assessment.smells_detected` is non-empty; transforms proposed |
| fortify | transform | `fortify.safety_threshold_met == true` OR `fortify.force_mode == true` |
| transform | verify | All transforms applied, reverted, or skipped |
| verify | complete | `verify.all_tests_green == true`; `verify.coverage_change >= 0`; `memory_captured == true` |
| _any_ | failed | Unrecoverable error or user abort |
