# 6. Workflow Router Decision Tree

The `/shaktra:workflow` router uses a noun-first, two-signal classification model. Shaktra-specific nouns are the primary signal; verbs are secondary. When multiple routes match, a strict priority resolution order determines the target. Ambiguous requests prompt the user for confirmation before dispatching.

```mermaid
flowchart TD
    Start(["/shaktra:workflow\n'user request'"]) --> Empty{Request\nempty?}

    Empty -->|Yes| ShowMenu["Show available\nworkflows table"]
    Empty -->|No| StoryID{Contains\nST-### ?}

    StoryID -->|Yes| HasReview1{"Also has\n'review'?"}
    HasReview1 -->|Yes| Review["/shaktra:review"]
    HasReview1 -->|No| Dev["/shaktra:dev"]

    StoryID -->|No| PRRef{Contains PR\nreference?}
    PRRef -->|Yes| Review

    PRRef -->|No| UtilMatch{Utility\nkeyword?}
    UtilMatch -->|"init, initialize"| Init["/shaktra:init"]
    UtilMatch -->|"doctor, health"| Doctor["/shaktra:doctor"]
    UtilMatch -->|"help, commands"| Help["/shaktra:help"]
    UtilMatch -->|"status, dashboard"| StatusDash["/shaktra:status-dash"]

    UtilMatch -->|No| NounMatch{Shaktra\nnoun?}

    NounMatch -->|"design, stories,\nsprint, hotfix"| TPM["/shaktra:tpm"]
    NounMatch -->|"bug, error,\nstack trace"| Bugfix["/shaktra:bugfix"]
    NounMatch -->|"codebase, brownfield,\ndebt, dependencies"| Analyze["/shaktra:analyze"]

    NounMatch -->|No| VerbOnly{Verb-only\nmatch?}
    VerbOnly -->|Yes| Confirm["Confirm with\nuser before routing"]
    VerbOnly -->|No| General["/shaktra:general"]

    Confirm -->|User confirms| TargetSkill["Route to\ndetected skill"]
    Confirm -->|User redirects| AltSkill["Route to\nuser's choice"]
```

### Priority Resolution Order

1. Story ID + "review" --> Review
2. Story ID (without "review") --> Dev
3. PR reference (#number, URL) --> Review
4. Utility keyword match --> Init / Doctor / Help / Status Dash
5. Noun match --> per route table (noun beats verb)
6. Verb-only match --> confirm with user
7. No match --> General

### Key Overlap Resolutions

| Request | Winner | Reason |
|---------|--------|--------|
| "review the design" | TPM | Noun "design" outranks verb "review" |
| "analyze the PR" | Review | Noun "PR" outranks verb "analyze" |
| "fix this bug" | Bug Fix | Noun "bug" routes to bugfix |
| "diagnose this bug" | Bug Fix | Noun "bug" outranks doctor's "diagnose" |

**Source:** `dist/shaktra/skills/shaktra-workflow/SKILL.md`
