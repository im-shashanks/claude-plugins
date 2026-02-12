# Decisions Schema

Defines `.shaktra/memory/decisions.yml` — append-only log of architectural decisions promoted by the sw-quality agent.

## Entry Schema

```yaml
decisions:
  - id: string          # "DC-001" — sequential
    story_id: string    # story that produced the decision
    title: string       # 10-100 characters
    summary: string     # 20-500 characters
    categories: [string] # 1-3 from allowed list
    guidance: [string]   # 1-5 actionable rules for future stories
    status: string      # "active" | "superseded"
    supersedes: string   # optional — ID of decision this replaces
    created: string     # ISO 8601 date
```

## Categories

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

1. **CAPTURE** — discovered during TDD, added to `important_decisions` in handoff
2. **CONSOLIDATE** — sw-quality approves and appends to `.shaktra/memory/decisions.yml`
3. **APPLY** — planner and architect reference in future story planning
4. **SUPERSEDE** — new decision replaces old (set `status: superseded`, never delete)
