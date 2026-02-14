# Shaktra Configuration Guide

All Shaktra settings live in `.shaktra/settings.yml`. Nothing is hardcoded in the plugin -- every threshold, toggle, and behavior is configurable from this single file. Hooks enforce constraints automatically at development time.

## settings.yml Reference

The settings file is created by `/shaktra:init` with sensible defaults. You can edit it at any time.

### TDD Thresholds

```yaml
tdd:
  coverage_threshold: 90          # Default coverage for normal stories
  hotfix_coverage_threshold: 70   # Coverage for hotfixes
  small_coverage_threshold: 80    # Coverage for S-tier stories
  large_coverage_threshold: 95    # Coverage for L-tier stories
```

Each story tier has its own coverage target. Quality gates enforce these during TDD cycles. Hotfixes use the lowest threshold (70%) to allow rapid fixes, while large stories require the highest (95%) to ensure thorough testing.

### Quality Thresholds

```yaml
quality:
  p1_threshold: 2  # Max P1 findings before merge block
```

**Merge gate logic:**

| Severity | Behavior |
|----------|----------|
| P0 | Always blocks merge |
| P1 | Blocks merge if count exceeds `p1_threshold` |
| P2 / P3 | Never blocks merge |

For the severity taxonomy (P0-P3 definitions), see the [severity reference](../skills/shaktra-reference/severity-taxonomy.md).

### Review Settings

```yaml
review:
  verification_test_persistence: ask   # auto | always | never | ask
  min_verification_tests: 5            # Minimum independent tests per review
```

Code Reviewer runs verification tests to independently validate behavior beyond the story's own tests.

**Persistence options:**

| Value | Behavior |
|-------|----------|
| `ask` | Prompt whether to keep tests after review |
| `auto` | Keep tests only if they improve coverage |
| `always` | Always keep verification tests |
| `never` | Always discard verification tests |

### Analysis Settings

```yaml
analysis:
  summary_token_budget: 600   # Max tokens per artifact summary
  incremental_refresh: true   # Use checksums for incremental refresh
```

These control the `/shaktra:analyze` workflow. `incremental_refresh` enables checksum-based caching so only changed files are re-analyzed.

### Sprint Settings

```yaml
sprints:
  enabled: true
  velocity_tracking: true
  sprint_duration_weeks: 2
  default_velocity: 15  # Story points per sprint (used at init)
```

Sprint tracking is enabled by default. `default_velocity` seeds the first sprint; subsequent sprints use actual velocity data.

### Product Management

```yaml
pm:
  default_framework: rice    # rice | weighted | moscow
  quick_win_effort_threshold: 3    # Max effort points for Quick Win
  big_bet_impact_threshold: 7      # Min impact score for Big Bet
```

The prioritization framework is used by the Product Manager agent during `/shaktra:tpm` to rank and categorize stories.

---

## Hooks: Enforcement Rules

Four blocking hooks enforce constraints automatically. Hooks are all-or-nothing -- they block the operation or they don't exist. There is no warn-only mode.

### block-main-branch

**Triggers:** Bash (git operations)

Blocks any git operation that targets `main`, `master`, or `prod` branches. This prevents accidental direct commits to protected branches -- all changes must go through stories and reviews.

**Resolution:** Create a feature branch, commit there, then open a PR when ready.

### validate-story-scope

**Triggers:** Write/Edit operations

Blocks file changes outside the current story's scope. During `/shaktra:dev`, the current story is tracked and edits are validated against the story's `files:` list. Out-of-scope changes are rejected.

**Resolution:** Either create a separate story for the out-of-scope change, or update the current story's file list and re-run validation.

### validate-schema

**Triggers:** Write/Edit operations (YAML files)

Blocks YAML files that don't match Shaktra schemas. Validates:

- `.shaktra/stories/*.md` -- Story schema
- `.shaktra/settings.yml` -- Config schema
- `.shaktra/sprints.yml` -- Sprint schema
- All other `.shaktra/` YAML files

**Resolution:** Check the error message for missing or invalid fields, fix the YAML, and retry.

### check-p0-findings

**Triggers:** Stop (session completion)

Blocks completion if unresolved P0 findings exist. When you finish work, all story findings are checked. Any P0 finding prevents the session from ending -- you must fix or escalate P0s before continuing.

P0 findings are critical issues (security vulnerabilities, data loss risks). They must be resolved before merging.

**Resolution:** Return to `/shaktra:dev` to fix the P0, or document why it cannot be fixed and escalate.

---

## Customization Examples

### Relaxing thresholds for a prototype project

```yaml
tdd:
  coverage_threshold: 70
  small_coverage_threshold: 60
  large_coverage_threshold: 80
quality:
  p1_threshold: 5
```

### Strict mode for production services

```yaml
tdd:
  coverage_threshold: 95
  hotfix_coverage_threshold: 80
  large_coverage_threshold: 98
quality:
  p1_threshold: 0
review:
  verification_test_persistence: always
  min_verification_tests: 10
```

### Disabling sprint tracking

```yaml
sprints:
  enabled: false
  velocity_tracking: false
```

---

## Full Default Configuration

For reference, here is the complete default `settings.yml` generated by `/shaktra:init`:

```yaml
tdd:
  coverage_threshold: 90
  hotfix_coverage_threshold: 70
  small_coverage_threshold: 80
  large_coverage_threshold: 95

quality:
  p1_threshold: 2

review:
  verification_test_persistence: ask
  min_verification_tests: 5

analysis:
  summary_token_budget: 600
  incremental_refresh: true

sprints:
  enabled: true
  velocity_tracking: true
  sprint_duration_weeks: 2
  default_velocity: 15

pm:
  default_framework: rice
  quick_win_effort_threshold: 3
  big_bet_impact_threshold: 7
```
