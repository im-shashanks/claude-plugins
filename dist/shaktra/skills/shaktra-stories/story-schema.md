# Story Schema

Defines the YAML structure for story files in `.shaktra/stories/`. Fields accumulate by tier — each tier inherits all fields from lower tiers. Tier definitions and gate behavior are in `story-tiers.md`.

## Trivial — 3 fields + metadata

```yaml
id: string           # "ST-001" — sequential
title: string        # imperative, ≤100 characters
description: string  # what and why, 1-3 sentences
tier: string         # "trivial" | "small" | "medium" | "large" — auto-detected from scope and complexity

metadata:
  story_points: integer    # from [1, 2, 3, 5, 8, 10] — assigned based on tier and complexity
  priority: string         # "critical" | "high" | "medium" | "low" — PM adjusts via RICE
  blocked_by: [string]     # story IDs that must complete before this starts
  status: string           # "planned" | "in_progress" | "done"
```

## Small — adds 2 fields (total 5 + metadata)

```yaml
files: [string]             # source files to create or modify (max 3). Excludes test files — tests are defined in test_specs.
acceptance_criteria:        # Gherkin-style
  - id: string              # "AC-1"
    given: string
    when: string
    then: string
    priority: string        # "must" | "should"
```

## Medium — adds 7 fields (total 12 + metadata)

```yaml
scope: string               # exactly 1 from allowed values (see below)
interfaces:
  implements:               # new code this story creates
    - name: string
      signature: string
      returns: string
      raises: [string]
  uses: [string]            # existing dependencies to inject/import
io_examples:
  - name: string
    input: any              # concrete test data
    output: any             # expected result
    notes: string           # optional — edge case explanation
  # at least 1 must be an error case
error_handling:
  - code: string            # error identifier
    condition: string       # when this error fires
    recoverable: boolean
    fallback: string        # what happens on this error
test_specs:
  unit:
    - id: string            # "T-01"
      description: string
      covers: string        # AC-id this test validates
      arrange: string
      act: string
      assert: [string]
invariants:
  - rule: string            # e.g. "balance >= 0 after any transaction"
    test: string            # test id that enforces this
logging_rules:
  - event: string           # e.g. "payment_processed"
    level: string           # "debug" | "info" | "warn" | "error"
    fields: [string]        # structured fields to include
    condition: string       # when to emit (optional — omit if always)
observability_rules:
  metrics: [string]         # metric names with type (counter, gauge, histogram)
  traces: [string]          # span names for distributed tracing
```

## Large — adds 6 fields (total 18+ plus metadata)

```yaml
failure_modes:
  - trigger: string         # what external failure occurs
    impact: string          # what breaks
    mitigation: string      # how the code handles it
    test: string            # test id that validates this
edge_cases:
  - category: string        # from 10 categories below
    case: string            # description
    expected: string        # correct behavior
    test: string            # test id
  # Categories: invalid_input, dependency_failure, duplicate, concurrency,
  #   limits, time, config, startup_shutdown, capacity, upgrade
  # Cover at least 5 of 10 categories for Large tier
determinism:
  time_injection: string    # how time is injected for testability
  random_injection: string  # how randomness is controlled
  id_injection: string      # how IDs are generated deterministically in tests
feature_flags:              # mandatory for Large
  - name: string
    default: boolean        # must be false
    rollout: string         # "gradual" | "immediate" | "percentage"
concurrency:
  idempotent: boolean
  shared_state: string      # "none" | description of shared state
  thread_safety: string     # strategy used
resource_safety:
  timeouts:
    connect_ms: integer
    read_ms: integer
    total_ms: integer
  bounded_resources: [string] # queues, pools, buffers with max sizes
  cleanup: string           # how resources are released
```

## Rules

1. **Single-scope rule:** Every story has exactly one `scope` value (Medium+ tiers).
2. **Test name contract:** Every `test` field value must match a test id in `test_specs`.
3. **Error case required:** `io_examples` must include at least one error-case example (Medium+).
4. **Edge case coverage:** Large tier must cover at least 5 of 10 edge case categories.
5. **Inheritance:** Higher tiers include all lower-tier fields — never omit inherited fields.
6. **Story points range:** `metadata.story_points` must be from `[1, 2, 3, 5, 8, 10]`.
7. **Blocked-by validity:** `metadata.blocked_by` references must be valid story IDs.
8. **Status default:** `metadata.status` defaults to `"planned"` on creation.

## Allowed Scope Values

`bug_fix` · `feature` · `refactor` · `config` · `docs` · `test` · `performance` · `security` · `integration` · `migration` · `scaffold`
