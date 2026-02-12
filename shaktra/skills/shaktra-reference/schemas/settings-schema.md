# Settings Schema

Defines `.shaktra/settings.yml` — the single configuration file for all Shaktra thresholds and project metadata. Every threshold in the framework reads from this file; none are hardcoded.

## Schema

```yaml
project:
  name: string            # required — project display name
  type: string            # "greenfield" | "brownfield"
  language: string        # "python" | "typescript" | "go" | "java" | "rust" | etc.
  architecture: string    # "layered" | "hexagonal" | "clean" | "mvc" | "feature-based" | "event-driven" | ""
  test_framework: string  # "pytest" | "jest" | "vitest" | "go test" | etc.
  coverage_tool: string   # "coverage" | "istanbul" | "c8" | etc.
  package_manager: string # "pip" | "npm" | "pnpm" | "cargo" | etc.

tdd:
  coverage_threshold: integer       # default: 90 — Medium tier target
  hotfix_coverage_threshold: integer # default: 70 — Trivial tier target
  small_coverage_threshold: integer  # default: 80 — Small tier target
  large_coverage_threshold: integer  # default: 95 — Large tier target

quality:
  p1_threshold: integer  # default: 2 — max P1 findings before merge block

review:
  verification_test_persistence: string  # default: "ask" — "auto" | "always" | "never" | "ask"
  min_verification_tests: integer        # default: 5 — minimum independent verification tests

analysis:
  summary_token_budget: integer  # default: 600 — max tokens per artifact summary section
  incremental_refresh: boolean   # default: true — enable checksum-based incremental refresh

refactoring:
  safety_threshold: integer              # default: 80 — min coverage % before targeted refactoring
  structural_safety_threshold: integer   # default: 90 — min coverage % before structural refactoring
  max_characterization_tests: integer    # default: 20 — max tests added during FORTIFY phase

sprints:
  enabled: boolean              # default: true
  velocity_tracking: boolean    # default: true
  sprint_duration_weeks: integer # default: 2
  default_velocity: integer     # default: 15 — story points per sprint, used when no velocity history exists

pm:
  default_framework: string           # default: "rice" — "rice" | "weighted" | "moscow"
  quick_win_effort_threshold: integer # default: 3 — max story points for Quick Win classification
  big_bet_impact_threshold: integer   # default: 7 — min impact score for Big Bet classification
  min_persona_evidence: integer       # default: 2 — minimum evidence entries per persona
  min_journey_stages: integer         # default: 3 — minimum stages in a journey map
```

## Consumer Reference

| Setting | Read By |
|---|---|
| `project.name` | init skill (writes), all agents (project identification) |
| `project.type` | analyze skill (brownfield guard), all agents (context) |
| `project.language` | analyze skill (glob patterns), general skill (domain context), all agents (context) |
| `project.architecture` | architect (validates alignment), sw-engineer (pattern selection), developer (code structure), sw-quality (ARC checks — conditional enforcement) |
| `project.test_framework` | all agents (implicit context — determines test syntax and runner conventions) |
| `project.coverage_tool` | all agents (implicit context — determines coverage report format) |
| `project.package_manager` | all agents (implicit context — determines install/build commands) |
| `tdd.coverage_threshold` | developer, story-tiers gate matrix |
| `tdd.hotfix_coverage_threshold` | developer, story-tiers gate matrix |
| `tdd.small_coverage_threshold` | developer, story-tiers gate matrix |
| `tdd.large_coverage_threshold` | developer, story-tiers gate matrix |
| `quality.p1_threshold` | sw-quality, code-reviewer, severity-taxonomy merge gate |
| `review.verification_test_persistence` | code-reviewer |
| `review.min_verification_tests` | code-reviewer |
| `analysis.summary_token_budget` | cba-analyzer (via analysis-output-schemas.md budgets), analyze skill (validation) |
| `analysis.incremental_refresh` | analyze skill (refresh workflow) |
| `refactoring.safety_threshold` | refactoring-pipeline (orchestrator), test-agent (characterization mode) |
| `refactoring.structural_safety_threshold` | refactoring-pipeline (orchestrator), test-agent (characterization mode) |
| `refactoring.max_characterization_tests` | test-agent (characterization mode) |
| `sprints.enabled` | scrummaster, tdd-pipeline (orchestrator), workflow-template (orchestrator) |
| `sprints.velocity_tracking` | scrummaster |
| `sprints.sprint_duration_weeks` | scrummaster |
| `sprints.default_velocity` | scrummaster (fallback when no velocity history) |
| `pm.default_framework` | product-manager (prioritize mode), pm skill (prioritization workflow) |
| `pm.quick_win_effort_threshold` | product-manager (RICE classification) |
| `pm.big_bet_impact_threshold` | product-manager (RICE classification) |
| `pm.min_persona_evidence` | product-manager (persona-create validation) |
| `pm.min_journey_stages` | product-manager (journey-create validation) |

## Environment Variable Overrides

Hook scripts support these environment variables for override scenarios (CI, testing, emergency fixes):

| Variable | Default | Purpose |
|---|---|---|
| `SHAKTRA_ALLOW_MAIN_BRANCH` | unset | Set to any value to bypass protected branch hook |
| `SHAKTRA_SKIP_P0_CHECK` | unset | Set to any value to bypass P0 finding check at completion |
| `CLAUDE_PROJECT_DIR` | `cwd` | Override project root for hook file resolution |

These are escape hatches — not regular workflow configuration. Do not set them permanently.
