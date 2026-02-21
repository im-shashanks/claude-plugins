# Procedures Schema

Defines `.shaktra/memory/procedures.yml` — workflow-level learnings that inform orchestration and process adaptation.

## Schema

```yaml
procedures:
  - id: string           # "PC-001" — sequential
    text: string         # workflow-level learning (1-3 sentences)
    confidence: float    # 0.2-1.0
    source_count: integer # number of supporting observations
    tags: [string]
    roles: [string]      # typically "sdm" for orchestrator-level
    applies_to: [string] # workflow types: "tdd" | "review" | "analysis" | "bugfix" | "tpm" | "pm" | "general"
    scope: string        # "project" | "universal"
    status: string       # "active" | "archived"
    source: string       # story_id where first observed
    created: string      # ISO 8601 date
    last_reinforced: string # ISO 8601 date (optional)
```

## Detection Rule

A procedure is created when:
- 3+ workflow-level observations (`type: observation` or `type: deviation`) across **different stories**
- Observations describe the same workflow adaptation or risk pattern

## Distinction from Principles

- **Principles** = code-level patterns (how to write code, what patterns to use)
- **Procedures** = workflow-level patterns (how to run the process, what steps to adapt)

Example principle: "Always use constructor injection for external service dependencies"
Example procedure: "Stories touching the auth module need extra security review in the PLAN phase"

## Lifecycle

1. **DETECT** — memory-curator identifies repeated workflow observation
2. **CREATE** — procedure entry created
3. **APPLY** — included in briefings for matching workflow types
4. **ARCHIVE** — confidence drops below threshold
