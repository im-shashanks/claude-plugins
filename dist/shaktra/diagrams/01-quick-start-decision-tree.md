# 1. Quick Start Decision Tree

Shaktra offers different entry paths depending on your project type and immediate need. This decision tree shows which commands to run first based on whether you have an existing codebase or are starting fresh, and whether you need to fix a bug or build a feature.

```mermaid
flowchart TD
    Start([Start]) --> HasShaktra{.shaktra/\nexists?}

    HasShaktra -->|No| Init["/shaktra:init"]
    HasShaktra -->|Yes| Intent{What do you\nneed?}

    Init --> ProjectType{Project\ntype?}

    ProjectType -->|Greenfield| Intent
    ProjectType -->|Brownfield| Analyze["/shaktra:analyze"]
    Analyze --> Intent

    Intent -->|Build a feature| TPM["/shaktra:tpm"]
    Intent -->|Fix a bug| Bugfix["/shaktra:bugfix"]
    Intent -->|Hotfix| Hotfix["'/shaktra:tpm hotfix: ...'"]
    Intent -->|Not sure| Workflow["/shaktra:workflow"]

    TPM --> Dev["/shaktra:dev ST-xxx"]
    Hotfix --> Dev
    Bugfix --> BugDev["Creates story\nthen /shaktra:dev"]

    Dev --> Review["/shaktra:review ST-xxx"]
    BugDev --> Review

    Review --> Done([Done])
```

**Source:** `dist/shaktra/README.md` (Quick Start section)
