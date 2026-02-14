# 12. Dev Agent Dispatch

The Software Development Manager orchestrates the TDD pipeline through 4 phases: PLAN, RED, GREEN, and QUALITY. Each phase has a dedicated creator agent and a quality gate enforced by SW Quality. The pipeline includes branch creation between PLAN and RED, tier-aware gate skipping (Trivial skips RED; Trivial/Small skip QUALITY), and mandatory memory capture at the end.

```mermaid
sequenceDiagram
    participant U as User
    participant O as /shaktra:dev<br/>Orchestrator
    participant SWE as SW Engineer<br/>(Opus)
    participant DEV as Developer<br/>(Opus)
    participant TA as Test Agent<br/>(Opus)
    participant SWQ as SW Quality<br/>(Sonnet)
    participant MC as Memory Curator<br/>(Haiku)

    U->>O: /shaktra:dev {story_id}
    O->>O: Read settings, decisions, lessons
    O->>O: Pre-flight: language config,<br/>story deps, story quality guard

    rect rgb(255, 245, 235)
        Note over O,SWQ: PLAN PHASE
        O->>SWE: Story + settings + decisions
        SWE-->>O: implementation_plan.md + handoff

        alt Tier >= Medium
            loop Quality Loop (max 3)
                O->>SWQ: PLAN_REVIEW
                alt CHECK_PASSED
                    SWQ-->>O: CHECK_PASSED
                else CHECK_BLOCKED
                    SWQ-->>O: Findings
                    O->>SWE: Fix plan findings
                    SWE-->>O: Updated plan
                end
            end
        end
    end

    Note over O,DEV: BRANCH CREATION
    O->>DEV: mode: branch
    DEV-->>O: feat/ or fix/ branch created

    rect rgb(255, 235, 235)
        Note over O,SWQ: RED PHASE (skip if Trivial)
        O->>TA: Story + plan + handoff
        TA->>TA: Write tests
        TA->>TA: Run tests - verify RED
        Note right of TA: Valid: ImportError,<br/>AttributeError<br/>Invalid: SyntaxError,<br/>TypeError (fix and re-run)
        TA-->>O: handoff.test_summary

        loop Quality Loop (max 3)
            O->>SWQ: QUICK_CHECK (test gate)
            alt CHECK_PASSED
                SWQ-->>O: CHECK_PASSED
            else CHECK_BLOCKED
                SWQ-->>O: Findings
                O->>TA: Fix test findings
                TA-->>O: Updated tests
            end
        end
    end

    rect rgb(235, 255, 235)
        Note over O,SWQ: GREEN PHASE
        O->>DEV: mode: implement
        DEV->>DEV: Implement in plan order
        DEV->>DEV: Run tests incrementally
        DEV->>DEV: Check coverage vs tier threshold

        alt TESTS_NOT_GREEN
            DEV->>DEV: Debug and fix implementation
        end
        alt COVERAGE_GATE_FAILED
            DEV->>DEV: Add coverage
        end

        DEV-->>O: handoff.code_summary

        loop Quality Loop (max 3)
            O->>SWQ: QUICK_CHECK (code gate)
            alt CHECK_PASSED
                SWQ-->>O: CHECK_PASSED
            else CHECK_BLOCKED
                SWQ-->>O: Findings
                O->>DEV: Fix code findings
                DEV-->>O: Updated code
            end
        end
    end

    rect rgb(235, 235, 255)
        Note over O,SWQ: QUALITY PHASE (skip if Trivial/Small)
        O->>SWQ: COMPREHENSIVE review
        SWQ->>SWQ: Run tests + coverage
        SWQ->>SWQ: Dimensions A-M + N
        SWQ->>SWQ: Identify decisions to promote

        loop Quality Loop (max 3)
            alt QUALITY_PASS
                SWQ-->>O: QUALITY_PASS + decisions
            else QUALITY_BLOCKED
                SWQ-->>O: Findings
                O->>DEV: Fix quality findings
                DEV-->>O: Updated code
            end
        end

        O->>O: Write promoted decisions<br/>to decisions.yml
    end

    rect rgb(245, 235, 255)
        Note over O,MC: MEMORY CAPTURE (always)
        O->>MC: workflow_type: tdd
        MC-->>O: memory_captured: true
    end

    O->>O: Update sprint state (if enabled)
    O->>U: Present completion report
```

### Reading Guide

- **Pre-flight checks** block the pipeline if language config, story dependencies, or story quality are insufficient.
- **Quality loops** use a reusable pattern: SW Quality reviews, if blocked the creator agent fixes, up to 3 attempts. After 3 failures, MAX_LOOPS_REACHED escalates to the user.
- **Tier-aware gating:** Trivial stories skip RED and QUALITY. Small stories skip QUALITY. Medium gets standard COMPREHENSIVE. Large gets COMPREHENSIVE + expanded review.
- **Coverage thresholds** are read from settings per tier: hotfix (Trivial), small, standard (Medium), large.
- **Decision promotion** happens during QUALITY phase -- SW Quality identifies patterns worth codifying, and the orchestrator writes them to decisions.yml.

**Source:** `dist/shaktra/skills/shaktra-dev/SKILL.md`, `dist/shaktra/skills/shaktra-dev/tdd-pipeline.md`, `dist/shaktra/agents/shaktra-sw-engineer.md`, `dist/shaktra/agents/shaktra-test-agent.md`, `dist/shaktra/agents/shaktra-developer.md`, `dist/shaktra/agents/shaktra-sw-quality.md`
