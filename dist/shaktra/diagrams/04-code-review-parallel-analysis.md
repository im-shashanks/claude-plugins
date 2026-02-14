# 4. Code Review Parallel Analysis

The Code Reviewer dispatches CR Analyzer agents across 4 parallel dimension groups, covering all 13 quality dimensions simultaneously. After aggregation, independent verification tests validate behavior from an outsider's perspective. The merge gate applies strict severity rules -- any P0 blocks, P1 count is threshold-gated.

```mermaid
flowchart TD
    Start(["/shaktra:review"]) --> Mode{Mode?}

    Mode -->|Story ID| LoadStory["Load Story Context\nHandoff + modified files\n+ surrounding code"]
    Mode -->|PR number| LoadPR["Load PR Context\ngh pr view + diff\n+ linked story"]

    LoadStory --> Dispatch
    LoadPR --> Dispatch

    subgraph Dispatch ["Parallel CR Analyzer Dispatch"]
        direction LR
        G1["Group 1\nCorrectness & Safety\nA: Contract & API\nB: Failure Modes\nC: Data Integrity\nD: Concurrency"]
        G2["Group 2\nSecurity & Ops\nE: Security\nF: Observability\nK: Configuration"]
        G3["Group 3\nReliability & Scale\nG: Performance\nI: Testing\nL: Dependencies"]
        G4["Group 4\nEvolution\nH: Maintainability\nJ: Deployment\nM: Compatibility"]
    end

    Dispatch --> Aggregate["Aggregate Findings\nDeduplicate\nHigher severity wins"]

    Aggregate --> Verify["Independent Verification\nTests (min 5)"]

    subgraph Verify5 ["5 Test Categories"]
        direction TB
        V1["1. Core Behavior\n(external perspective)"]
        V2["2. Error Handling\n(system boundaries)"]
        V3["3. Edge Cases\n(edge-case matrix)"]
        V4["4. Security Probing\n(boundary violations)"]
        V5["5. Integration Stress\n(upstream/downstream)"]
    end

    Verify --> Verify5
    Verify5 --> Gate{Merge Gate}

    Gate -->|"P0 > 0"| Blocked["BLOCKED\nCritical issues"]
    Gate -->|"P1 > threshold"| ChangesReq["CHANGES_REQUESTED\nFix P1s"]
    Gate -->|"P1 <= threshold\nP2+ exist"| ApprovedNotes["APPROVED_WITH_NOTES\nMerge with awareness"]
    Gate -->|"No findings"| Approved["APPROVED\nShip it"]

    Blocked --> Memory["Memory Capture"]
    ChangesReq --> Memory
    ApprovedNotes --> Memory
    Approved --> Memory

    Memory --> Done([Done])
```

### Reading Guide

- **Top section:** Intent classification routes to story or PR context loading
- **Middle section:** 4 analyzer groups run in parallel, each covering 3-4 dimensions
- **Verification section:** 5 mandatory test categories validate independently of developer tests
- **Bottom section:** Merge gate applies P0/P1 severity rules, then memory capture

### Dimension Reference

| Group | Dimensions | Focus |
|-------|-----------|-------|
| Correctness & Safety | A, B, C, D | Does it work correctly? |
| Security & Ops | E, F, K | Is it secure and observable? |
| Reliability & Scale | G, I, L | Will it hold up? |
| Evolution | H, J, M | Can it evolve safely? |

**Source:** `dist/shaktra/skills/shaktra-review/SKILL.md`
