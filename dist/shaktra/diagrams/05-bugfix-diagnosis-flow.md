# 5. Bugfix Diagnosis Flow

The Bug Fix workflow splits into two phases: a 5-step investigation that transforms vague bug reports into confirmed root causes, followed by remediation through the standard TDD pipeline (see diagram 02). The diagnosis classifies bugs by symptom type and root cause category, then assesses blast radius to find similar patterns elsewhere in the codebase.

```mermaid
flowchart TD
    Start(["/shaktra:bugfix"]) --> Classify{Intent?}

    Classify -->|Full bugfix| Investigation
    Classify -->|"diagnose only"| Investigation

    subgraph Investigation ["Investigation: Bug Diagnostician"]
        direction TB
        Triage["Step 1: Triage\nSymptom type: crash / wrong_result /\nperformance / data_corruption / security\nReproducibility: always / intermittent /\nenvironment / data_specific"]

        Reproduce["Step 2: Reproduce\nCreate minimal failing test\nDocument exact steps + inputs"]

        Hypothesize["Step 3: Hypothesize\nGenerate candidates across 6 categories:\nRC-LOGIC, RC-DATA, RC-INTEG,\nRC-CONFIG, RC-CONCUR, RC-RESOURCE\n(min 2 hypotheses)"]

        Evidence["Step 4: Gather Evidence\nTrace execution, inspect state,\ngit history, dependency check\nConfirm or eliminate each hypothesis"]

        Isolate["Step 5: Isolate Root Cause\nWHY: causal chain explained\nWHEN: trigger conditions identified\nPROOF: test demonstrates bug"]

        Triage --> Reproduce
        Reproduce -->|Cannot reproduce| Blocked["DIAGNOSIS_BLOCKED\nAsk user for more context"]
        Reproduce -->|Reproduced| Hypothesize
        Hypothesize --> Evidence
        Evidence --> Isolate
    end

    Isolate --> BlastRadius["Blast Radius Assessment\nSearch for similar patterns\nIdentify affected consumers\nFind masking tests"]

    BlastRadius --> CreateStory["Create Bug Fix Story\nscope: bug_fix\nIncludes reproduction test"]

    BlastRadius -->|Similar patterns found| BlastStories["BLAST_RADIUS_FOUND\nRecommend additional stories\n(user decides)"]

    Classify -->|"diagnose only"| DiagnoseStop
    Isolate --> DiagnoseStop["Present diagnosis\nand stop"]

    CreateStory --> Remediation["Remediation: /shaktra:dev\nPLAN --> RED --> GREEN --> QUALITY\n(standard TDD pipeline)"]

    Remediation --> Memory["Memory Capture\nBug pattern tagged:\nsource: bugfix-{id}\ntags: bug-pattern, {category}"]

    Memory --> Done([Done])
```

### Severity to Story Tier Mapping

| Bug Severity | Story Tier | Coverage Threshold |
|-------------|-----------|-------------------|
| P0 (production down) | Large | 95% |
| P1 (major broken) | Medium | 90% |
| P2 (minor, workaround) | Small | 80% |
| P3 (cosmetic) | Trivial | 70% |

**Source:** `dist/shaktra/skills/shaktra-bugfix/SKILL.md`, `diagnosis-methodology.md`
