# Observations Schema

Defines `.shaktra/stories/<story_id>/.observations.yml` — per-story observations written by agents during workflow execution. Consumed by the memory-curator during post-workflow consolidation.

## Schema

```yaml
observations:
  - id: string          # "OB-001" — sequential within story
    agent: string       # agent name: "developer" | "sw-quality" | "sw-engineer" | "architect" | "bug-diagnostician" | "test-agent" | "product-manager"
    phase: string       # TDD phase: "plan" | "plan-review" | "tests" | "code" | "code-gate" | "quality" | "review" | "diagnosis"
    type: string        # "discovery" | "quality-loop-finding" | "fix-rationale" | "deviation" | "observation" | "consistency-check"
    text: string        # what was observed (1-3 sentences)
    tags: [string]      # freeform keywords, used for matching during consolidation
    importance: integer  # 1-10 (7+ = strong promotion candidate)
    # Optional fields (type-dependent):
    severity: string     # P0-P3, only for quality-loop-finding type
    resolved: boolean    # only for quality-loop-finding type
    iterations: integer  # fix attempt count, only for quality-loop-finding type
    principle_id: string # only for consistency-check type — references PR-NNN
    relationship: string # "reinforce" | "weaken" | "contradict", only for consistency-check type
```

## Lifecycle

1. **CREATE** — orchestrator creates empty `.observations.yml` at workflow start
2. **APPEND** — agents append observations during their phase
3. **CONSOLIDATE** — memory-curator reads and synthesizes into long-term stores
4. **ARCHIVE** — observations stay with the story directory for audit trail
