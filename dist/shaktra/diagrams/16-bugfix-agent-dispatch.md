# 16. Bugfix Agent Dispatch

The bugfix workflow has two phases: investigation (unique to bugfix) and remediation (reuses the full TDD pipeline from /shaktra:dev). The Bug Diagnostician never modifies code -- it produces a diagnosis artifact and story draft, then hands off to the standard dev pipeline for the fix.

```mermaid
sequenceDiagram
    participant U as User
    participant O as /shaktra:bugfix<br/>Orchestrator
    participant BD as Bug Diagnostician<br/>(Opus)
    participant DEV as /shaktra:dev<br/>TDD Pipeline
    participant MC as Memory Curator<br/>(Haiku)

    U->>O: /shaktra:bugfix {bug description}
    O->>O: Read settings, decisions, lessons
    O->>O: Classify intent (bugfix vs diagnose_only)

    rect rgb(255, 245, 235)
        Note over O,BD: INVESTIGATION PHASE
        O->>BD: bug_description, error_context
        BD->>BD: Step 1: Triage (severity, type)
        BD->>BD: Step 2: Reproduce (find failing test)
        BD->>BD: Step 3: Hypothesize (min 2 candidates)
        BD->>BD: Step 4: Gather evidence
        BD->>BD: Step 5: Blast radius search

        alt DIAGNOSIS_COMPLETE
            BD-->>O: Diagnosis artifact + story draft
            O->>U: Present diagnosis summary
        else DIAGNOSIS_BLOCKED
            BD-->>O: Cannot reproduce
            O->>U: Request more context
        end
    end

    alt BLAST_RADIUS_FOUND
        O->>U: Present similar patterns,<br/>recommend additional stories
    end

    alt bugfix intent (not diagnose_only)
        rect rgb(235, 245, 255)
            Note over O,DEV: REMEDIATION PHASE (reuses /shaktra:dev)
            O->>DEV: Invoke with bug_fix story
            Note right of DEV: PLAN -> RED -> GREEN -> QUALITY<br/>(unchanged TDD pipeline)
            DEV-->>O: Story complete
        end
    end

    O->>MC: workflow_type: bugfix
    Note right of MC: Enhanced metadata:<br/>tags: bug-pattern, {RC category}
    MC-->>O: Lessons captured
    O->>U: Present completion report
```

**Source:** `dist/shaktra/skills/shaktra-bugfix/SKILL.md`, `dist/shaktra/agents/shaktra-bug-diagnostician.md`
