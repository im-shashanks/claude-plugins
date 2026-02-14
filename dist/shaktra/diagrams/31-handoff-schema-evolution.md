# 31. Handoff Schema Evolution

The `handoff.yml` file is a state machine that tracks a story through the TDD pipeline. Fields are populated incrementally — each phase adds its section while preserving all prior state. This diagram shows how the handoff schema evolves as a story progresses from pending through completion.

```mermaid
stateDiagram-v2
    [*] --> pending: handoff.yml created

    pending --> plan: PLAN phase
    note right of pending
        identity fields only:
        story_id, tier,
        current_phase: pending,
        completed_phases: [],
        quality_findings: [],
        important_decisions: [],
        memory_captured: false
    end note

    plan --> tests: RED phase
    note right of plan
        + plan_summary:
        components, test_plan,
        implementation_order,
        patterns_applied,
        scope_risks
    end note

    tests --> code: GREEN phase
    note right of tests
        + test_summary:
        all_tests_red: true,
        test_count,
        test_files
    end note

    code --> quality: QUALITY phase
    note right of code
        + code_summary:
        all_tests_green: true,
        coverage, files_modified,
        deviations
    end note

    quality --> complete: MEMORY phase
    note right of quality
        + quality_findings updated,
        + important_decisions populated,
        decisions promoted to
        decisions.yml
    end note

    note right of complete
        + memory_captured: true,
        current_phase: complete,
        completed_phases: [plan,
        tests, code, quality]
    end note

    pending --> failed: error/abort
    plan --> failed: error/abort
    tests --> failed: error/abort
    code --> failed: error/abort
    quality --> failed: error/abort
```

**Source:** `dist/shaktra/skills/shaktra-reference/schemas/handoff-schema.md`, `dist/shaktra/skills/shaktra-dev/tdd-pipeline.md`
