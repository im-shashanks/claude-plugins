# Principles Schema

Defines `.shaktra/memory/principles.yml` — synthesized principles from cross-story observations. The primary long-term knowledge store for project patterns, techniques, and constraints.

## Schema

```yaml
principles:
  - id: string           # "PR-001" — sequential
    text: string         # the principle statement (20-500 chars)
    categories: [string] # 1-3 from the 14 categories (see Categories below)
    guidance: [string]   # 1-5 actionable rules
    confidence: float    # 0.2-1.0
    source_count: integer # number of supporting observations
    tags: [string]       # for retrieval matching
    roles: [string]      # "developer" | "sw-engineer" | "architect" | "sw-quality" | "test-agent" | etc.
    scope: string        # "project" | "universal"
    status: string       # "active" | "archived" | "superseded"
    supersedes: string   # optional — PR-ID of superseded principle
    source: string       # story_id or "migrated:DC-NNN"
    created: string      # ISO 8601 date
    last_reinforced: string # ISO 8601 date (optional)
```

## Categories

Reused from the decisions-schema 14-category taxonomy:

| # | Category | Covers |
|---|---|---|
| 1 | correctness | Logic, invariants, contracts |
| 2 | reliability | Fault tolerance, retry, recovery |
| 3 | performance | Latency, throughput, resource use |
| 4 | security | Auth, injection, secrets, access |
| 5 | maintainability | Readability, modularity, coupling |
| 6 | testability | Mockability, isolation, determinism |
| 7 | observability | Logging, metrics, tracing |
| 8 | scalability | Load, concurrency, partitioning |
| 9 | compatibility | APIs, versions, migrations |
| 10 | accessibility | A11y standards, assistive tech |
| 11 | usability | UX patterns, error messages |
| 12 | cost | Infrastructure, API calls, storage |
| 13 | compliance | Regulatory, licensing, data governance |
| 14 | consistency | Naming, patterns, conventions |

## Lifecycle

1. **SEED** — migrated from `decisions.yml` or created from high-importance observations
2. **REINFORCE** — confidence increases when observations match (+0.08)
3. **WEAKEN** — confidence decreases when observations partially contradict (-0.08)
4. **SUPERSEDE** — new principle replaces old (set `status: superseded`, `supersedes` references old ID)
5. **ARCHIVE** — confidence drops below threshold (set `status: archived`)
