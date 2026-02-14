# Review Workflow

13-dimension code review with independent verification testing and evidence-based merge gating.

## Overview

The review workflow (`/shaktra:review`) performs app-level code review -- not "does it match the spec" (that is SW Quality's job during TDD), but "is this code I would trust in production at scale." It examines how changes fit the overall application: architecture coherence, cross-cutting concerns, integration risks, and systemic quality.

**When to use:**
- After `/shaktra:dev` completes a story
- Before merging a pull request
- When you want a second opinion on production-readiness

**Entry points:**
- `/shaktra:review ST-001` -- review a completed story
- `/shaktra:review #123` -- review a GitHub pull request

## How It Works

```
invoke /shaktra:review
        |
        v
  Intent Classification
  (story-review or pr-review)
        |
        v
  Load Project Context
  (.shaktra/settings.yml, memory/decisions.yml, memory/lessons.yml)
        |
        v
  Load Changed Files + Test Files + Surrounding Code
        |
        v
  Dispatch CR Analyzer Agents (4 parallel groups)
  +-----------+-----------+-----------+-----------+
  | Group 1   | Group 2   | Group 3   | Group 4   |
  | A,B,C,D   | E,F,K     | G,I,L     | H,J,M     |
  | Correct.  | Security  | Reliab.   | Evolution |
  +-----------+-----------+-----------+-----------+
        |
        v
  Aggregate + Deduplicate Findings
        |
        v
  Independent Verification Testing (>=5 tests)
        |
        v
  Apply Merge Gate (P0/P1 threshold logic)
        |
        v
  Memory Capture (lessons.yml)
        |
        v
  Structured Report with Verdict
```

## The 13 Dimensions

Every review evaluates code across 13 quality dimensions. Each dimension has 3 core checks plus a P0 trigger assessment. Dimensions are grouped for parallel analysis by CR Analyzer agents.

### Group 1 -- Correctness and Safety

**A: Contract and API** -- Do the APIs introduced or modified maintain consistency with the application's existing API surface? Checks naming conventions, error response formats, parameter validation patterns, and breaking change versioning. The reviewer deliverable is a Contract Analysis table mapping each function/endpoint to its assumptions and validation evidence.

**B: Failure Modes** -- When this code fails, does the application degrade gracefully or cascade? Checks failure propagation, circuit breakers, blast radius, and retry safety (idempotent operations only). Produces a Failure Mode Analysis table mapping each dependency to its failure modes, app impact, and mitigations.

**C: Data Integrity** -- Do data writes maintain consistency across the entire application's data model? Checks referential integrity, concurrent write handling, migration paths, and cascading deletes. Produces an Invariants Table showing where each data invariant is enforced and how.

**D: Concurrency** -- Does the code interact safely with the application's concurrency model? Checks shared state access, transaction isolation levels, async await patterns, and request-scoped state leakage. Produces a Concurrency Analysis mapping shared resources to their access patterns and protections.

### Group 2 -- Security and Operations

**E: Security** -- Does this code maintain the application's security posture? Checks input sanitization patterns, auth/authz middleware on new endpoints, secret management consistency, and error message information leakage. Produces a Security Analysis mapping each threat surface to its risks, mitigations, and verification status.

**F: Observability** -- Can an on-call engineer diagnose a failure in this code at 3 AM with only logs and metrics? Checks structured logging format, trace/correlation ID propagation, request traceability, and business event logging. Produces an Incident Debugging Path showing each diagnostic step and whether the needed log/metric exists.

**K: Configuration** -- Does configuration management remain consistent across the application? Checks that new config values exist in all environments, that config is validated at startup (fail fast), that defaults are safe, and that sensitive values use the application's secret management.

### Group 3 -- Reliability and Scale

**G: Performance** -- Does this code maintain the application's performance characteristics under load? Checks for O(n^2+) algorithms on user-controlled input, missing database indexes, N+1 query patterns, and hot path bottlenecks. Produces a Performance Analysis mapping hotspots to their complexity and bounding.

**I: Testing** -- Do the tests verify integration with the application, not just isolated unit behavior? Checks for integration tests on cross-component interactions, test coverage of identified failure modes (Dimension B), regression tests for review edge cases, and balanced coverage beyond happy paths. Produces a Risk-Based Test Coverage table.

**L: Dependencies** -- Do new dependencies fit the application's dependency strategy? Checks for duplicate functionality in the dependency tree, license compatibility, maintenance status, and whether stdlib or existing dependencies could cover the use case.

### Group 4 -- Evolution

**H: Maintainability** -- Does this code follow the application's established patterns, or does it introduce drift? Checks module organization, consistency of problem-solving approaches, readability for new team members, and whether new patterns are justified in decisions.yml.

**J: Deployment** -- Can this change be safely deployed and rolled back? Checks backward-compatibility with in-flight requests, database migration reversibility, feature flag needs, and deployment ordering constraints.

**M: Compatibility** -- Does this change maintain compatibility with the application's consumers and integrations? Checks public API contracts, event schema backward-compatibility, configuration file formats, and CLI interfaces.

## Verification Tests

After dimension analysis, the reviewer generates independent tests that are fundamentally different from the developer's test suite. The developer's tests may share assumptions with their implementation -- independent tests catch blind spots.

**Minimum count:** Controlled by `settings.review.min_verification_tests` (default: 5).

### Five Required Categories

At least one test from each category:

1. **Core Behavior from External Perspective** -- Test the feature as an outsider would use it. Write tests from the spec alone, without reading implementation first. This catches cases where tests and code share the same wrong assumption.

2. **Error Handling at System Boundaries** -- What happens when external dependencies fail? Test timeouts, malformed responses, connection drops, and auth failures. These are the scenarios that surface at 3 AM.

3. **Edge Cases from the Edge-Case Matrix** -- The review-dimensions.md defines 10 edge-case categories (invalid inputs, dependency failure, duplicate delivery, concurrency, limits, time, configuration, startup/shutdown, capacity, upgrade). Select the highest-risk categories and test at least 3.

4. **Security Boundary Probing** -- Attempt to violate security assumptions: injection in inputs, privilege escalation, data leakage through error messages. These tests validate what Dimension E claims.

5. **Integration Point Stress** -- Test how the change behaves when upstream/downstream components are slow, unavailable, or return unexpected data. This complements Dimension B's failure mode analysis with actual test evidence.

### Test Results and Persistence

Every verification test is executed. If any test fails, the failure is automatically a P1 finding (behavior claim without evidence).

The `settings.review.verification_test_persistence` setting controls what happens after the review:

| Setting | Behavior |
|---|---|
| `auto` | Persist tests that cover previously-untested risk areas |
| `always` | Persist all verification tests to the project's test suite |
| `never` | Discard after review (findings still reported) |
| `ask` | Present test results and ask user whether to persist |

## Evidence Enforcement

Every claim in a review must be backed by evidence. "Looks good" is never valid.

**Six evidence types:** test result, assertion in code, type system, benchmark, log output, code reference. When evidence is missing for a behavior claim, severity escalates:

| Claim Category | Missing Evidence Severity |
|---|---|
| Security ("input is sanitized") | P0 -- unverified security is no security |
| Correctness ("it handles X correctly") | P1 |
| Error handling ("errors are handled") | P1 |
| Concurrency ("it's thread-safe") | P1 |
| Data integrity ("writes are atomic") | P1 |
| Performance ("it's fast enough") | P2 |

## Merge Gate Logic

After all findings are collected and deduplicated, the merge gate determines the verdict.

```
p0_count = count findings where severity == P0
p1_count = count findings where severity == P1
p1_max   = settings.quality.p1_threshold

if p0_count > 0:
    verdict = BLOCKED           -- fix all P0s first, no exceptions
elif p1_count > p1_max:
    verdict = CHANGES_REQUESTED -- too many major issues
elif p1_count > 0 or p2_count > 0:
    verdict = APPROVED_WITH_NOTES -- merge with awareness
else:
    verdict = APPROVED          -- ship it
```

### Verdict Reference

| Verdict | Condition | Meaning |
|---|---|---|
| APPROVED | 0 P0, 0 P1, 0 P2 | Ship it |
| APPROVED_WITH_NOTES | 0 P0, P1 within threshold, P2+ exist | Merge with awareness |
| CHANGES_REQUESTED | 0 P0, P1 exceeds threshold | Fix P1s before merge |
| BLOCKED | Any P0 exists | Critical issues -- cannot merge |

P2 and P3 findings are always allowed through the gate. They appear in the report for future improvement but never block a merge.

## Example Review Sessions

### Story Review -- Clean Pass

```
> /shaktra:review ST-042

Loading story ST-042... payment retry logic
Running 13-dimension analysis (4 parallel groups)...
Running 6 verification tests...

## Code Review: ST-042
Verdict: APPROVED

All 13 dimensions passed. 6/6 verification tests passed.
No findings. Memory captured.
```

### PR Review -- Blocked on P0

```
> /shaktra:review #187

Loading PR #187... add user search endpoint
Running 13-dimension analysis...
Running 5 verification tests...

## Code Review: PR #187
Verdict: BLOCKED

P0 Findings (2):
  - [E: Security] User search query concatenated into SQL string
    at search_handler.py:34. No parameterized query. Evidence: injection
    test failed with "'; DROP TABLE users; --" input.
  - [B: Failure Modes] External geocoding API call has no timeout.
    Unbounded network call at location.py:67. Could hang indefinitely
    under load.

Fix both P0s before re-review.
```

### Story Review -- Approved with Notes

```
> /shaktra:review ST-089

Loading story ST-089... notification preferences
Running 13-dimension analysis...
Running 7 verification tests...

## Code Review: ST-089
Verdict: APPROVED_WITH_NOTES

P1 Findings (1):
  - [I: Testing] No integration test for notification delivery
    when email service returns 503. Failure mode identified in
    Dimension B but not covered by tests.

P2 Findings (2):
  - [F: Observability] Success path for preference update has
    no structured log entry. Gaps in incident debugging path.
  - [H: Maintainability] New notification channel enum defined
    inline rather than using the shared enum in models/enums.py.

P1 count (1) within threshold (3). Merge allowed.
Consider adding the missing integration test before next sprint.
```

## Reviewer Discipline

These anti-patterns degrade review quality and must be avoided:

- **Rubber-stamping** -- Every dimension must be evaluated with evidence
- **Bikeshedding** -- Address highest severity first; do not spend effort on P3 while P0/P1 issues exist
- **Severity inflation** -- Apply severity-taxonomy.md strictly; style issues are P3, not P1
- **Preference as finding** -- Every finding must cite a concrete risk, not an alternative approach
- **Diff-only review** -- Always review changed code in context of surrounding application code
- **Deferring P0/P1** -- Never approve with critical or major issues deferred to "later"

## Related

- [Severity Taxonomy](../../skills/shaktra-reference/severity-taxonomy.md) -- canonical P0-P3 definitions
- [Review Dimensions](../../skills/shaktra-review/review-dimensions.md) -- app-level dimension details and edge-case matrix
- [Dev Workflow](./DEV.md) -- the TDD workflow that precedes review
