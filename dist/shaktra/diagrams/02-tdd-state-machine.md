# 2. TDD State Machine

Every story implementation follows a strict 6-phase state machine with quality gates at each transition. The pipeline enforces test-driven development: tests are written before code, and no phase can be skipped. Tier determines which gates activate -- Trivial stories skip RED and QUALITY, while Large stories get expanded review.

```mermaid
stateDiagram-v2
    [*] --> PreFlight

    PreFlight --> PLAN: Checks pass
    PreFlight --> [*]: Blocked

    PLAN --> RED: Approved + branch created
    PLAN --> PLAN: Blocked, retry

    RED --> GREEN: Tests fail correctly
    RED --> RED: Invalid failures, retry

    GREEN --> QUALITY: Tests pass + coverage OK
    GREEN --> GREEN: Tests or coverage failed

    QUALITY --> MEMORY: Review passed
    QUALITY --> GREEN: Findings need fixes

    MEMORY --> Complete: Lessons captured

    Complete --> [*]

    note right of PreFlight
        Checks:
        1. Language config
        2. Story dependencies
        3. Story quality
    end note

    note right of PLAN
        M/L tiers: quality gate
        Creates feature branch
    end note

    note right of RED
        Trivial tier: skip RED
        Tests must fail for
        valid reasons
    end note

    note right of QUALITY
        Trivial/Small: skip
        Medium: standard
        Large: comprehensive
    end note

    note right of MEMORY
        Always required
        Updates sprint state
    end note
```

### Tier-Aware Gate Matrix

| Phase | Trivial | Small | Medium | Large |
|-------|---------|-------|--------|-------|
| PLAN | Minimal | Minimal | Full + review | Full + review |
| RED | Skip | Required | Required | Required |
| GREEN | Required | Required | Required | Required |
| QUALITY | Skip | Skip | Comprehensive | Comprehensive + expanded |
| MEMORY | Required | Required | Required | Required |

**Source:** `dist/shaktra/skills/shaktra-dev/tdd-pipeline.md`
