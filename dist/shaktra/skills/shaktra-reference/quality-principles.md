# Quality Principles

10 core principles for all Shaktra agents. Each principle has 2 verification checks — concrete questions to confirm the principle is met.

## 1. Correct Before Fast

Write code that produces the right result first. Optimize only after correctness is proven by tests.

- **Verify:** Do all tests pass with the current implementation?
- **Verify:** Were any shortcuts taken that trade correctness for speed?

## 2. Fail Explicitly

Never swallow errors silently. Every failure must be surfaced, logged, or propagated with context.

- **Verify:** Does every catch/except block either re-raise, log, or return a meaningful error?
- **Verify:** Can a caller distinguish success from failure without inspecting side effects?

## 3. Test Behavior, Not Implementation

Tests should assert what the code does, not how it does it. Refactoring internals should not break tests.

- **Verify:** Would renaming a private method or changing internal data structures break any test?
- **Verify:** Does each test describe a behavior a user or caller cares about?

## 4. One Responsibility Per Unit

Each function, class, or module should have a single reason to change.

- **Verify:** Can you describe what this unit does in one sentence without "and"?
- **Verify:** Would a change to an unrelated feature require modifying this unit?

## 5. Inject Dependencies, Own State

Accept collaborators from the outside; manage your own internal state. This enables testing and swapping.

- **Verify:** Can every external dependency be replaced with a test double without modifying the unit?
- **Verify:** Does the unit create or manage its own state rather than relying on global mutable state?

## 6. Handle Every Error Path

Every operation that can fail must have an explicit error path — no implicit assumption of success.

- **Verify:** For each I/O call, network request, or parse operation, is there an error handler?
- **Verify:** Are error paths tested, not just the happy path?

## 7. Log Structured, Trace Distributed

Use structured logging (key-value pairs) and propagate correlation IDs across service boundaries.

- **Verify:** Are log entries structured (not interpolated strings) with consistent field names?
- **Verify:** Do cross-service calls propagate a trace/correlation ID?

## 8. Bound All Resources

Every pool, queue, buffer, timeout, and retry must have an explicit upper bound.

- **Verify:** Does every network call have a timeout configured?
- **Verify:** Are queues, pools, and buffers capped with explicit max sizes?

## 9. Make It Work, Make It Right, Make It Fast

Follow the sequence: get it working with tests, clean up the design, then optimize with profiling data.

- **Verify:** Were all tests green before any refactoring or optimization began?
- **Verify:** Is any optimization backed by measured profiling data rather than intuition?

## 10. Document Every Tradeoff

When choosing between alternatives, record what was chosen, what was rejected, and why.

- **Verify:** Is there a decision record for each non-obvious architectural or design choice?
- **Verify:** Does the record state at least one rejected alternative and the reason for rejection?
