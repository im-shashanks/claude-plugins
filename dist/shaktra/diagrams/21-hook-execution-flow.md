# 21. Hook Execution Flow

Shaktra enforces four blocking hooks at different points in the development lifecycle. Hooks are all-or-nothing: they block or they do not exist. There is no warn-only mode. Each hook is a Python script triggered by Claude Code's hook system.

```mermaid
flowchart TD
    subgraph PreToolUse["PreToolUse Hooks"]
        direction TB
        BASH["Bash tool invoked"] --> BMB{"block_main_branch.py<br/>Is target branch<br/>main/master/prod?"}
        BMB -->|Yes| BMB_BLOCK["BLOCK<br/>Direct commits to<br/>protected branches<br/>not allowed"]
        BMB -->|No| BMB_PASS["PASS<br/>Proceed with<br/>git operation"]

        WRITE["Write/Edit tool invoked"] --> VSS{"validate_story_scope.py<br/>Is file in current<br/>story's scope?"}
        VSS -->|No| VSS_BLOCK["BLOCK<br/>Out-of-scope<br/>file change<br/>rejected"]
        VSS -->|Yes| VSS_PASS["PASS<br/>Proceed with<br/>file edit"]
    end

    subgraph PostToolUse["PostToolUse Hook"]
        direction TB
        WROTE["Write/Edit completed"] --> VSCH{"validate_schema.py<br/>Does YAML match<br/>Shaktra schema?"}
        VSCH -->|No| VSCH_BLOCK["BLOCK<br/>Schema validation<br/>failed"]
        VSCH -->|Yes| VSCH_PASS["PASS<br/>File written<br/>successfully"]
    end

    subgraph StopHook["Stop Hook"]
        direction TB
        STOP["Agent stop triggered"] --> CP0{"check_p0_findings.py<br/>Any unresolved<br/>P0 findings?"}
        CP0 -->|Yes| CP0_BLOCK["BLOCK<br/>Unresolved P0s<br/>must be fixed"]
        CP0 -->|No| CP0_PASS["PASS<br/>Safe to<br/>complete"]
    end

    style BMB_BLOCK fill:#d9534f,stroke:#a94442,color:#fff
    style VSS_BLOCK fill:#d9534f,stroke:#a94442,color:#fff
    style VSCH_BLOCK fill:#d9534f,stroke:#a94442,color:#fff
    style CP0_BLOCK fill:#d9534f,stroke:#a94442,color:#fff
    style BMB_PASS fill:#5ba85b,stroke:#3a7a3a,color:#fff
    style VSS_PASS fill:#5ba85b,stroke:#3a7a3a,color:#fff
    style VSCH_PASS fill:#5ba85b,stroke:#3a7a3a,color:#fff
    style CP0_PASS fill:#5ba85b,stroke:#3a7a3a,color:#fff
    style PreToolUse fill:#f5f5f5,stroke:#337ab7,color:#333
    style PostToolUse fill:#f5f5f5,stroke:#f0ad4e,color:#333
    style StopHook fill:#f5f5f5,stroke:#d9534f,color:#333
```

**Reading guide:**
- **PreToolUse** hooks run before a tool executes. `block_main_branch` intercepts git operations targeting protected branches. `validate_story_scope` intercepts file edits outside the current story's file list.
- **PostToolUse** hook runs after a Write/Edit completes. `validate_schema` checks that any `.shaktra/` YAML file conforms to its schema.
- **Stop** hook runs when the agent finishes. `check_p0_findings` prevents completion if unresolved P0 findings remain in any story handoff.
- Every hook is implemented as a Python script for cross-platform compatibility (no shell-specific commands like `grep -oP`).

**Source:** `dist/shaktra/hooks/hooks.json`, `dist/shaktra/README.md` (Hooks: Enforcement Rules section)
