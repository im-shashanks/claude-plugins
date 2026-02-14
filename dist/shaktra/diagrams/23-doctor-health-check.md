# 23. Doctor Health Check

The `/shaktra:doctor` skill runs 10 read-only checks across 3 categories: plugin structure (5 checks validating agents, skills, hooks, sub-file references, and Python dependencies), project health (2 checks on settings and directory structure), and design constraints (3 checks enforcing file limits, severity taxonomy uniqueness, and orphan detection). Each category degrades gracefully — a missing `.shaktra/` directory skips Category 2 without failing the whole report.

```mermaid
flowchart TD
    Start(["/shaktra:doctor"]) --> Cat1

    subgraph Cat1 ["Category 1: Plugin Structure"]
        direction TB
        C1["Check 1: Agent Files\n12 agents with valid\nYAML frontmatter"]
        C2["Check 2: Skill Directories\n15 skills with valid\nSKILL.md frontmatter"]
        C3["Check 3: Hook Scripts\n4 scripts exist\nand are executable"]
        C4["Check 4: Sub-File References\nAll referenced .md files\nactually exist"]
        C10["Check 10: Python Dependencies\npython3 -c 'import yaml'\nreturn code check"]
        C1 --> C2 --> C3 --> C4 --> C10
    end

    Cat1 --> ShaktraExists{".shaktra/\nexists?"}

    ShaktraExists -->|No| SkipCat2["Skip Category 2:\nReport 'run /shaktra:init'"]
    ShaktraExists -->|Yes| Cat2

    subgraph Cat2 ["Category 2: Project Health"]
        direction TB
        C5["Check 5: Settings File\nsettings.yml has required sections:\nproject, tdd, quality, review,\nanalysis, refactoring, sprints"]
        C6["Check 6: Directory Structure\nmemory/, stories/,\ndesigns/, analysis/"]
        C5 --> C6
    end

    SkipCat2 --> Cat3
    Cat2 --> Cat3

    subgraph Cat3 ["Category 3: Design Constraints"]
        direction TB
        C7["Check 7: File Line Limits\nwc -l on all .md and .py\nFlag any file > 300 lines"]
        C8["Check 8: Severity Taxonomy\nGrep for '## P0' headings\nMust appear in exactly 1 file"]
        C9["Check 9: No Orphaned Files\nEvery sub-file .md referenced\nby parent SKILL.md"]
        C7 --> C8 --> C9
    end

    Cat3 --> Report["Structured Report\nPASS/FAIL per check\nwith actionable detail"]
    Report --> Done([Done])
```

### Reading Guide

- **Category 1** runs against the installed plugin at `${CLAUDE_PLUGIN_ROOT}` — validates the plugin is structurally complete
- **Category 2** runs against the project's `.shaktra/` directory — skipped entirely if the project is not initialized
- **Category 3** runs against `${CLAUDE_PLUGIN_ROOT}` — enforces Shaktra design rules (300-line limit, single severity definition, no orphans)
- Each check produces PASS or FAIL independently; failures include actionable remediation steps

**Source:** `dist/shaktra/skills/shaktra-doctor/SKILL.md`
