# Quality Dimensions

13 review dimensions (A-M). Each dimension has 3 key checks and 1 P0 trigger. Full expanded checklists are defined in the shaktra-quality skill — this file defines the dimension framework.

## A: Contract & API

1. Do public method signatures match their documented behavior?
2. Are all input parameters validated at the boundary?
3. Are return types and error types consistent across the API surface?

**P0 trigger:** Public API accepts untrusted input without validation.

## B: Failure Modes

1. Does every operation that can fail have an explicit error path?
2. Are errors propagated with sufficient context for debugging?
3. Are transient vs permanent failures distinguished in retry logic?

**P0 trigger:** Error silently swallowed, causing incorrect state to propagate.

## C: Data Integrity

1. Are write operations atomic or wrapped in transactions?
2. Is user data validated before persistence?
3. Are backups or rollback mechanisms in place for destructive operations?

**P0 trigger:** Data written without atomicity guarantees, risking partial writes or corruption.

## D: Concurrency

1. Is shared mutable state protected by synchronization primitives?
2. Are read-modify-write sequences atomic?
3. Is lock ordering consistent to prevent deadlocks?

**P0 trigger:** Shared mutable state accessed without synchronization.

## E: Security

1. Are all external inputs sanitized before use in queries, commands, or templates?
2. Are secrets excluded from logs, error messages, and version control?
3. Are authentication and authorization enforced on every protected endpoint?

**P0 trigger:** Injection vulnerability (SQL, command, template) in code that processes external input.

## F: Observability

1. Are key operations logged with structured fields (not string interpolation)?
2. Do cross-service calls carry correlation/trace IDs?
3. Are failures logged with enough context to reproduce the issue?

**P0 trigger:** A failure path produces no log output whatsoever.

## G: Performance

1. Do all network calls have explicit timeouts?
2. Are collections bounded (no unbounded growth from external input)?
3. Are hot paths free of unnecessary allocations or repeated computation?

**P0 trigger:** Network call or loop with no timeout or upper bound on external input.

## H: Maintainability

1. Does each unit (function, class, module) have a single clear responsibility?
2. Are magic numbers and strings extracted into named constants or configuration?
3. Is the code readable without requiring comments to explain intent?

**P0 trigger:** None — maintainability issues are P2 at worst.

## I: Testing

1. Do tests cover the acceptance criteria and documented edge cases?
2. Are tests independent (no shared mutable state, no order dependency)?
3. Do tests assert behavior (what), not implementation (how)?

**P0 trigger:** None — testing gaps are P1 at worst.

## J: Deployment

1. Is the change backward-compatible or does it include a migration path?
2. Can the change be rolled back without data loss?
3. Are environment-specific values externalized to configuration?

**P0 trigger:** Deployment that cannot be rolled back and risks data loss.

## K: Configuration

1. Are all environment-specific values read from configuration, not hardcoded?
2. Are configuration values validated at startup?
3. Are sensitive configuration values (secrets, keys) handled through secure channels?

**P0 trigger:** Hardcoded credentials or secrets in source code.

## L: Dependencies

1. Are all imported modules real, published packages (not hallucinated)?
2. Are dependency versions pinned or constrained to avoid surprise breaks?
3. Are new dependencies justified (not duplicating existing functionality)?

**P0 trigger:** Hallucinated import — a module or package that does not exist in any registry.

## M: Compatibility

1. Does the change maintain backward compatibility with existing consumers?
2. Are breaking changes documented and versioned?
3. Are platform/runtime requirements explicitly declared?

**P0 trigger:** Silent breaking change to a public API consumed by external users.
