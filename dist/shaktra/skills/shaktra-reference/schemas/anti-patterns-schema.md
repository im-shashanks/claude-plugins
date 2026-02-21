# Anti-Patterns Schema

Defines `.shaktra/memory/anti-patterns.yml` — failure patterns with recommended alternatives. Created when repeated failures are detected on the same pattern.

## Schema

```yaml
anti_patterns:
  - id: string              # "AP-001" — sequential
    failed_approach: string  # what went wrong (1-3 sentences)
    failure_mode: string     # why it fails
    severity: string         # P0-P3 — highest severity from source observations
    recommended_approach: string # what to do instead
    trigger_patterns: [string]  # keywords for proactive surfacing
    confidence: float        # 0.2-1.0
    tags: [string]
    roles: [string]          # agents this anti-pattern is relevant to
    scope: string            # "project" | "universal"
    status: string           # "active" | "archived"
    source: string           # story_id where the pattern was first detected
    created: string          # ISO 8601 date
```

## Detection Rule

An anti-pattern is created when:
- 2+ failure observations (`type: quality-loop-finding`, `resolved: false`) on the **same pattern** within 3 stories
- Pattern match: overlapping tags and similar issue descriptions

## Proactive Surfacing

During briefing generation, anti-patterns are surfaced when their `trigger_patterns` match the story's keywords or scope. This enables proactive warnings before agents repeat known mistakes.

## Lifecycle

1. **DETECT** — memory-curator identifies repeated failure pattern
2. **CREATE** — anti-pattern entry created with trigger patterns
3. **SURFACE** — included in story briefings when trigger patterns match
4. **ARCHIVE** — confidence drops below threshold
