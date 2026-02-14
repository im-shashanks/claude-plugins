# 11. TPM Agent Dispatch

The TPM orchestrator runs the Full workflow by default -- the most complex agent sequence in Shaktra. It dispatches 5 distinct agents across 4 phases, with quality loops that can retry up to 3 times at each gate. The Architect and Scrummaster are the primary creators; TPM Quality and PM serve supporting roles; Memory Curator closes every workflow.

```mermaid
sequenceDiagram
    participant U as User
    participant O as /shaktra:tpm<br/>Orchestrator
    participant ARCH as Architect<br/>(Opus)
    participant PM as Product Manager<br/>(Sonnet)
    participant TQ as TPM Quality<br/>(Sonnet)
    participant SM as Scrummaster<br/>(Sonnet)
    participant MC as Memory Curator<br/>(Haiku)

    U->>O: /shaktra:tpm {request}
    O->>O: Read settings, decisions, lessons
    O->>O: Classify intent -> "full"

    rect rgb(255, 245, 235)
        Note over O,TQ: PHASE 1: DESIGN
        O->>ARCH: Create design doc
        ARCH-->>O: Design doc OR GAPS_FOUND

        alt GAPS_FOUND
            O->>PM: mode: gaps (answer questions)
            PM-->>O: Answers OR PM_ESCALATE
            alt PM_ESCALATE
                O->>U: Questions PM cannot answer
                U-->>O: Answers
            end
            O->>ARCH: Re-run with gap answers
            ARCH-->>O: Design doc
        end

        loop Quality Loop (max 3 attempts)
            O->>TQ: Review design (type: design)
            alt QUALITY_PASS
                TQ-->>O: QUALITY_PASS
            else QUALITY_BLOCKED
                TQ-->>O: Findings
                O->>ARCH: Fix findings
                ARCH-->>O: Updated design
            end
        end
        Note over O: MAX_LOOPS_REACHED if 3 failures
    end

    rect rgb(235, 245, 255)
        Note over O,TQ: PHASE 2: STORIES
        O->>SM: mode: create (from design doc)
        SM-->>O: Stories written

        loop Per story - Quality Loop (max 3)
            O->>TQ: Review story (type: story)
            alt QUALITY_PASS
                TQ-->>O: QUALITY_PASS
            else QUALITY_BLOCKED
                TQ-->>O: Findings
                O->>SM: Fix story findings
                SM-->>O: Updated story
            end
        end
    end

    rect rgb(245, 255, 235)
        Note over O,SM: PHASE 3: PM ANALYSIS
        O->>PM: mode: coverage (PRD mapping)
        PM-->>O: Coverage report + gaps

        O->>PM: mode: rice (prioritization)
        PM-->>O: Ranked stories + sprint goal

        O->>SM: Sprint allocation
        SM-->>O: sprints.yml written
    end

    rect rgb(245, 235, 255)
        Note over O,MC: PHASE 4: MEMORY
        O->>MC: workflow_type: tpm
        MC-->>O: Lessons captured
    end

    O->>U: Present completion report
```

### Reading Guide

- **Phase 1 (Design)** has the most complex flow: Architect may discover gaps, routing to PM for answers, which may escalate to the user. After the design is created, a quality loop validates it up to 3 times.
- **Phase 2 (Stories)** runs a quality loop per story, not once for the batch. Each story is independently validated.
- **Phase 3 (PM Analysis)** is linear -- PM scores stories, then Scrummaster allocates to sprints. No quality loops here.
- **Guard tokens** drive control flow: GAPS_FOUND routes to PM, PM_ESCALATE routes to user, QUALITY_BLOCKED triggers a fix cycle, MAX_LOOPS_REACHED halts and escalates.

**Source:** `dist/shaktra/skills/shaktra-tpm/SKILL.md`, `dist/shaktra/skills/shaktra-tpm/workflow-template.md`
