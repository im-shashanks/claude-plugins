# 27. Status Dashboard Data Flow

The status dashboard reads from 6 independent data sources to assemble a read-only project overview. Each section degrades gracefully — missing files produce a short message rather than failing the dashboard. If `.shaktra/` does not exist, only the plugin info section renders.

```mermaid
flowchart LR
    Invoke(["/shaktra:status-dash"]) --> S1

    S1["Section 1:\nPlugin Info +\nVersion Check"] -->|reads| S1src["scripts/check_version.py\nplugin.json\n(remote registry)"]

    S1 --> ShaktraCheck{".shaktra/\nexists?"}

    ShaktraCheck -->|No| ShaktraSkip["Show Section 1 only\n'Run /shaktra:init'"]
    ShaktraCheck -->|Yes| S2

    S2["Section 2:\nSprint Health"] -->|reads| S2src[".shaktra/sprints.yml\n(active sprint, velocity_history)"]

    S2 --> S3
    S3["Section 3:\nStory Pipeline"] -->|reads| S3src[".shaktra/stories/*/handoff.yml\n(story_id, current_phase,\nblocked status)"]

    S3 --> S4
    S4["Section 4:\nQuality Summary"] -->|reads| S4src[".shaktra/stories/*/handoff.yml\n+ .shaktra/settings.yml\n(quality_findings, p1_threshold)"]

    S4 --> S5
    S5["Section 5:\nMemory Health"] -->|reads| S5src[".shaktra/memory/decisions.yml\n.shaktra/memory/lessons.yml"]

    S5 --> S6
    S6["Section 6:\nAnalysis Progress"] -->|reads| S6src[".shaktra/analysis/manifest.yml\n(D1-D9 dimension status)"]

    S6 --> Report["Formatted Dashboard\nAll 6 sections\nwith graceful degradation"]
    ShaktraSkip --> Report
    Report --> Done([Done])
```

### Reading Guide

- **Left to right:** Each section executes in order, reading its specific data sources
- **Section 1** always runs — it reads from the plugin directory, not from `.shaktra/`
- **Sections 2-6** require `.shaktra/` — if missing, the dashboard short-circuits after Section 1
- Each section handles its own missing-file scenario independently (graceful degradation)

**Source:** `dist/shaktra/skills/shaktra-status-dash/SKILL.md`
