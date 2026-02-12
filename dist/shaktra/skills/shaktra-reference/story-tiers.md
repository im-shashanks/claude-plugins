# Story Tiers

4-tier classification system for user stories. Tier determines required fields, quality gates, and coverage thresholds. Field definitions and YAML schema live in `schemas/story-schema.md` — this file defines only the tier matrix, detection logic, and gate behavior.

## Tier Summary

| Tier | Typical Scope | Required Fields | Coverage Threshold | Check Depth |
|---|---|---|---|---|
| **Trivial** | Typo fix, config change, docs update | 3 | `settings.tdd.hotfix_coverage_threshold` | Quick |
| **Small** | Single-function change, minor bugfix | 5 | `settings.tdd.small_coverage_threshold` | Quick |
| **Medium** | Feature addition, multi-file change | 12 | `settings.tdd.coverage_threshold` | Full |
| **Large** | Cross-cutting feature, architectural change | 18+ | `settings.tdd.large_coverage_threshold` | Thorough |

## Auto-Detection Logic

```
if story has no acceptance criteria AND estimated_hours <= 1:
    tier = Trivial
else if files_touched <= 3 AND no new public API:
    tier = Small
else if files_touched <= 10 OR new public API:
    tier = Medium
else:
    tier = Large
```

The auto-detected tier is a suggestion. The user or TPM can override it explicitly in the story file.

## Gate Behavior Matrix

| Gate | Trivial | Small | Medium | Large |
|---|---|---|---|---|
| Failing test before code (Red) | Skip | Required | Required | Required |
| Tests pass after code (Green) | Required | Required | Required | Required |
| Coverage threshold | `settings.tdd.hotfix_coverage_threshold` | `settings.tdd.small_coverage_threshold` | `settings.tdd.coverage_threshold` | `settings.tdd.large_coverage_threshold` |
| Quality check depth | Quick | Quick | Full | Thorough |
| Design review | Skip | Skip | Required | Required |
| PR review | Skip | Required | Required | Required |

## Check Depth Definitions

Check depth controls **review scope**, not check loading. All ~36 checks from `shaktra-quality/quick-check.md` are always loaded regardless of tier. Depth determines how findings are treated and whether comprehensive review runs.

**Quick (Trivial/Small):** sw-quality runs quick-check only. All ~36 checks loaded, but P2+ findings are reported as observations, not blockers. No comprehensive review phase.

**Full (Medium):** sw-quality runs quick-check at each TDD gate + comprehensive review (dimensions A-M + N) at QUALITY phase. Standard severity enforcement — P0 blocks, P1 threshold applies, P2 reported.

**Thorough (Large):** Full depth + expanded comprehensive review with architecture impact analysis, performance profiling review, dependency audit, and cross-cutting concern validation.
