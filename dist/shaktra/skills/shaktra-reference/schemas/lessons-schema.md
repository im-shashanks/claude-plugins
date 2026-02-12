# Lessons Schema

Defines `.shaktra/memory/lessons.yml` — append-only log of workflow insights written by the memory-curator agent.

## Schema

```yaml
lessons:
  - id: string       # "LS-001" — sequential
    date: string     # ISO 8601 date (YYYY-MM-DD)
    source: string   # story_id or workflow that produced the insight
    insight: string  # what was learned (1-3 sentences)
    action: string   # concrete change to future behavior (1-2 sentences)
```

## Capture Bar

A lesson is worth capturing only if it would **materially change future workflow execution**. Routine observations ("tests passed", "code compiled") are not lessons.

Good: "Mocking the payment gateway at the HTTP layer instead of the SDK layer cut test setup from 40 lines to 8 and eliminated flaky timeouts."

Bad: "We wrote unit tests for the login module." (routine — no actionable insight)

## Archival

Maximum 100 active entries. When the limit is reached, the memory-curator moves the oldest entries to `.shaktra/memory/lessons-archive.yml` before appending new ones.
