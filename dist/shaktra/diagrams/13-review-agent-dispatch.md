# 13. Review Agent Dispatch

The Code Reviewer orchestrator dispatches 4 CR Analyzer agents in parallel, each covering a group of quality dimensions (A-M). After aggregation, independent verification tests probe for blind spots the developer's tests may share with the code. The merge gate applies severity-based logic to produce one of four verdicts.

```mermaid
sequenceDiagram
    participant U as User
    participant O as /shaktra:review<br/>Orchestrator
    participant CR1 as CR Analyzer 1<br/>(Opus)
    participant CR2 as CR Analyzer 2<br/>(Opus)
    participant CR3 as CR Analyzer 3<br/>(Opus)
    participant CR4 as CR Analyzer 4<br/>(Opus)
    participant MC as Memory Curator<br/>(Haiku)

    U->>O: /shaktra:review {story or PR}
    O->>O: Read settings, decisions, lessons
    O->>O: Classify intent (story vs PR)
    O->>O: Load modified files, test files,<br/>application context

    rect rgb(255, 245, 235)
        Note over O,CR4: PARALLEL DIMENSION REVIEW
        par Group 1: Correctness & Safety
            O->>CR1: Dims A, B, C, D
            Note right of CR1: Contract, Failure Modes,<br/>Data Integrity, Concurrency
            CR1-->>O: Findings + deliverables
        and Group 2: Security & Ops
            O->>CR2: Dims E, F, K
            Note right of CR2: Security, Observability,<br/>Configuration
            CR2-->>O: Findings + deliverables
        and Group 3: Reliability & Scale
            O->>CR3: Dims G, I, L
            Note right of CR3: Performance, Testing,<br/>Dependencies
            CR3-->>O: Findings + deliverables
        and Group 4: Evolution
            O->>CR4: Dims H, J, M
            Note right of CR4: Maintainability,<br/>Deployment, Compatibility
            CR4-->>O: Findings + deliverables
        end
    end

    O->>O: Aggregate findings,<br/>deduplicate (keep higher severity)

    rect rgb(235, 245, 255)
        Note over O,O: INDEPENDENT VERIFICATION TESTING
        O->>O: Generate min 5 verification tests
        Note right of O: 1. Core behavior (external view)<br/>2. Error handling at boundaries<br/>3. Edge cases from matrix<br/>4. Security boundary probing<br/>5. Integration point stress
        O->>O: Run verification tests
        O->>O: Failed tests -> P1 findings
    end

    rect rgb(245, 255, 235)
        Note over O,O: MERGE GATE
        O->>O: Apply severity gate logic
        Note right of O: P0 > 0 -> BLOCKED<br/>P1 > threshold -> CHANGES_REQUESTED<br/>P1/P2 exist -> APPROVED_WITH_NOTES<br/>Clean -> APPROVED
    end

    O->>MC: workflow_type: review
    MC-->>O: Lessons captured
    O->>U: Present review report with verdict
```

### Reading Guide

- **Parallel dispatch** is the key efficiency pattern. Four CR Analyzer agents run simultaneously, each handling 3-4 dimensions. This is the only Shaktra workflow that spawns multiple agents of the same type concurrently.
- **Deduplication** handles cases where two groups flag the same issue (e.g., a missing timeout could appear in both Failure Modes and Performance). The higher severity wins.
- **Verification tests** are fundamentally different from the developer's tests. They test from an external perspective, probe security boundaries, and stress integration points -- catching blind spots where tests and code share the same assumptions.
- **Four verdicts** provide graduated feedback: APPROVED (ship it), APPROVED_WITH_NOTES (merge with awareness), CHANGES_REQUESTED (fix P1s), BLOCKED (critical issues).

**Source:** `dist/shaktra/skills/shaktra-review/SKILL.md`, `dist/shaktra/agents/shaktra-cr-analyzer.md`
