# Guard Tokens

14 core workflow tokens used for signaling across Shaktra agents. Tokens are emitted as plain text markers in agent output. Domain-specific skills define additional tokens (review: 4, analyze: 3, general: 3, bugfix: 3, refactoring: 2) in their respective SKILL.md files.

## Phase Progression

| Token | When Emitted | Emitter | What Happens Next |
|---|---|---|---|
| `TESTS_NOT_RED` | Test suite does not have a failing test before implementation begins | Orchestrator, Test Agent | Block implementation — write a failing test first |
| `TESTS_NOT_GREEN` | Implementation complete but tests still failing | Developer | Return to implementation — fix until tests pass |
| `PHASE_GATE_FAILED` | A TDD phase transition check failed (red/green/refactor) | SW Quality | Block phase transition — resolve the failure |
| `COVERAGE_GATE_FAILED` | Coverage falls below the tier's required threshold | Developer, SW Quality | Block completion — add tests to meet threshold |

## Quality Gates

| Token | When Emitted | Emitter | What Happens Next |
|---|---|---|---|
| `CHECK_PASSED` | A quality check passed during development | SW Quality | Continue to next check or phase |
| `CHECK_BLOCKED` | A quality check failed during the TDD fix loop | SW Quality | Return to fix loop — address the finding |
| `QUALITY_PASS` | Quality gate passed (0 P0, P1 within threshold) | SW Quality, TPM Quality | Proceed to next phase or allow merge |
| `QUALITY_BLOCKED` | Quality gate failed (P0 exists or P1 exceeds threshold) | SW Quality, TPM Quality | Block — resolve findings first |
| `REFACTOR_PASS` | Refactoring verification passed — behavior preserved, metrics improved | SW Quality | Proceed to completion |
| `REFACTOR_BLOCKED` | Refactoring verification failed — tests broken, coverage decreased, or P0/P1 found | SW Quality | Return to fix loop — address regressions |

## Workflow

| Token | When Emitted | Emitter | What Happens Next |
|---|---|---|---|
| `MAX_LOOPS_REACHED` | A fix/retry loop hit its iteration cap without resolution | Any Agent | Stop loop, escalate to user with findings |

## Communication

| Token | When Emitted | Emitter | What Happens Next |
|---|---|---|---|
| `GAPS_FOUND` | Story or design has gaps that must be filled before work begins | Architect, TPM Quality | Return to planning — fill gaps before proceeding |
| `CLARIFICATION_NEEDED` | Ambiguity that cannot be resolved from available context | Any Agent | Ask user for clarification |
| `VALIDATION_FAILED` | Schema or state file validation failed | Any Agent | Report invalid fields, block until corrected |
