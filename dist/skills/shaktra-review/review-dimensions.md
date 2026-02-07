# App-Level Review Dimensions

This file defines HOW to apply quality dimensions at the application level. It does NOT redefine the dimensions — those are canonical in `quality-dimensions.md`. This file adds: the app-level lens, per-dimension reviewer deliverables, evidence enforcement, edge-case matrix, and severity decision guidance.

**Used by:** shaktra-cr-analyzer agent during `/shaktra:review` workflow.

---

## App-Level Lens

Story-level review (SW Quality) asks: "Does this code match the story spec?"
App-level review (Code Reviewer) asks: "Does this code make the application better?"

The difference matters. Code can perfectly satisfy a story yet introduce architecture drift, duplicate patterns that exist elsewhere, create inconsistent error handling, or add a dependency that conflicts with the project's direction. App-level review catches what story-level cannot.

---

## Evidence Enforcement

Every claim in a review must be backed by evidence. This is non-negotiable.

### 6 Evidence Types

| Type | Example | Strength |
|------|---------|----------|
| **Test result** | "test_login_timeout passes — see line 84" | Strong |
| **Assertion in code** | "Guard clause at auth.py:23 validates token expiry" | Strong |
| **Type system** | "Return type `Result[User, AuthError]` enforces error handling" | Strong |
| **Benchmark** | "Load test: p99 latency 42ms at 1000 RPS" | Strong |
| **Log output** | "Structured log at handler.py:67 includes correlation_id" | Moderate |
| **Code reference** | "See config.py:12 — timeout set to 30s" | Moderate |

### Escalation Rules

When evidence is missing for a behavior claim:

| Claim Category | Missing Evidence → Severity |
|----------------|---------------------------|
| Correctness ("it handles X correctly") | P1 — behavior unproven |
| Error handling ("errors are handled") | P1 — failure path unverified |
| Security ("input is sanitized") | P0 — security claim without proof is critical |
| Performance ("it's fast enough") | P2 — performance claim without data |
| Concurrency ("it's thread-safe") | P1 — concurrency claim without proof is dangerous |
| Data integrity ("writes are atomic") | P1 — data safety claim without proof |

### Evidence Anti-Patterns

These do NOT constitute valid evidence:
- "I tested manually" — no reproducible proof
- "It worked in development" — environment-specific, not evidence of production safety
- "The framework handles it" — which framework API, which guarantee, where documented?
- "It's the same pattern as X" — similarity is not proof; each instance needs its own evidence
- "No one has reported a bug" — absence of reports is not evidence of correctness

---

## Dimensions A-M — App-Level Perspective

For each dimension: apply the 3 key checks from `quality-dimensions.md`, then add the app-level focus and produce the reviewer deliverable.

### A: Contract & API — App-Level

**Focus:** Do the APIs introduced or modified maintain consistency with the application's existing API surface?

**App-level checks:**
- Are naming conventions consistent with existing endpoints/functions?
- Are error response formats identical to the rest of the application?
- Do new parameters follow established validation patterns?
- Are breaking changes versioned or gated?

**Reviewer deliverable — Contract Analysis:**

| Function/Endpoint | Assumption | Validated? | Evidence |
|---|---|---|---|
| `POST /users` | email is unique | Yes | unique constraint + test_duplicate_email |
| `GET /orders/{id}` | caller is authenticated | No | no auth middleware on route |

### B: Failure Modes — App-Level

**Focus:** When this code fails, does the application degrade gracefully or cascade?

**App-level checks:**
- Does failure in this component propagate to unrelated features?
- Are circuit breakers or fallbacks in place for external calls?
- Is the blast radius of a failure bounded?
- Are retries safe (idempotent operations only)?

**Reviewer deliverable — Failure Mode Analysis:**

| Dependency | Failure Mode | App Impact | Mitigation | Tested? |
|---|---|---|---|---|
| Payment API | timeout | checkout blocked | 30s timeout + retry | test_payment_timeout |
| Redis cache | unavailable | fallback to DB | cache-aside pattern | no test |

### C: Data Integrity — App-Level

**Focus:** Do data writes maintain consistency across the entire application's data model?

**App-level checks:**
- Do writes respect referential integrity across tables/collections?
- Are concurrent writes to the same entity handled?
- Is there a data migration path if schemas change?
- Are cascading deletes bounded and intentional?

**Reviewer deliverable — Invariants Table:**

| Invariant | Enforced At | Mechanism | Evidence |
|---|---|---|---|
| User email unique | DB + app layer | unique index + pre-check | migration_003 + test |
| Order total = sum(items) | order_service.py:45 | computed property | test_order_total_consistency |

### D: Concurrency — App-Level

**Focus:** Does the code interact safely with the application's concurrency model?

**App-level checks:**
- Does this code access any shared state modified by other components?
- Are database transactions at the correct isolation level?
- Are async operations properly awaited/joined?
- Could request-scoped state leak between concurrent requests?

**Reviewer deliverable — Concurrency Analysis:**

| Shared Resource | Access Pattern | Protection | Risk |
|---|---|---|---|
| user_session cache | read-modify-write | no lock | race condition on concurrent login |
| order_counter | increment | atomic DB operation | safe |

### E: Security — App-Level

**Focus:** Does this code maintain the application's security posture?

**App-level checks:**
- Are new inputs sanitized using the application's established sanitization patterns?
- Do new endpoints enforce the same auth/authz middleware as existing ones?
- Are secrets handled consistently with the application's secret management?
- Could error messages leak internal state to external users?

**Reviewer deliverable — Security Analysis:**

| Threat Surface | Risk | Mitigation | Verified? |
|---|---|---|---|
| User input in search query | SQL injection | parameterized query at search.py:34 | test_search_injection |
| Error response body | internal path disclosure | generic error handler | no specific test |

### F: Observability — App-Level

**Focus:** Can an on-call engineer diagnose a failure in this code at 3 AM with only logs and metrics?

**App-level checks:**
- Do logs follow the application's structured logging format?
- Are trace/correlation IDs propagated through this code path?
- Can you trace a request from entry to exit using only log output?
- Are key business events (not just errors) logged?

**Reviewer deliverable — Incident Debugging Path:**

| Step | What to Check | Log/Metric | Available? |
|---|---|---|---|
| 1. Request received | entry log with request_id | api.log structured entry | yes |
| 2. Auth check | auth result | no log for success path | gap |
| 3. DB query | query time + result | query_duration metric | yes |

### G: Performance — App-Level

**Focus:** Does this code maintain the application's performance characteristics under load?

**App-level checks:**
- Are there O(n^2) or worse algorithms on user-controlled input?
- Do new database queries have appropriate indexes?
- Are there N+1 query patterns?
- Could this code create a hot path bottleneck?

**Reviewer deliverable — Performance Analysis:**

| Hotspot | Complexity | Bounded? | Mitigation |
|---|---|---|---|
| user search | O(n) full scan | n = user count, unbounded | needs index + pagination |
| report generation | O(n*m) nested loop | m bounded by config | acceptable at current scale |

### H: Maintainability — App-Level

**Focus:** Does this code follow the application's established patterns, or does it introduce drift?

**App-level checks:**
- Does the code follow existing module organization patterns?
- Are similar problems solved the same way as elsewhere in the codebase?
- Could a new team member understand this code by reading surrounding code?
- Does it introduce new patterns without justification in decisions.yml?

### I: Testing — App-Level

**Focus:** Do the tests verify integration with the application, not just isolated unit behavior?

**App-level checks:**
- Are integration tests present for cross-component interactions?
- Do tests cover the failure modes identified in Dimension B?
- Are there regression tests for edge cases found during review?
- Is test coverage balanced (not just happy path)?

**Reviewer deliverable — Risk-Based Test Coverage:**

| Risk | Covered? | Test | Gap |
|---|---|---|---|
| Payment timeout | yes | test_payment_timeout | — |
| Concurrent order update | no | — | needs concurrency test |
| Auth token expiry | yes | test_expired_token | — |

### J: Deployment — App-Level

**Focus:** Can this change be safely deployed and rolled back in the application's deployment environment?

**App-level checks:**
- Is the change backward-compatible with in-flight requests?
- Can the database migration be reversed without data loss?
- Are feature flags needed for gradual rollout?
- Does the deployment order matter (app before DB, or vice versa)?

### K: Configuration — App-Level

**Focus:** Does configuration management remain consistent across the application?

**App-level checks:**
- Are new config values added to all required environments?
- Is configuration validated at startup (fail fast, not at runtime)?
- Are defaults safe if config is missing?
- Are sensitive values using the application's secret management?

### L: Dependencies — App-Level

**Focus:** Do new dependencies fit the application's dependency strategy?

**App-level checks:**
- Does the new dependency duplicate functionality already in the dependency tree?
- Is the license compatible with the application's license?
- Is the dependency actively maintained?
- Could stdlib or an existing dependency cover this use case?

### M: Compatibility — App-Level

**Focus:** Does this change maintain compatibility with the application's consumers and integrations?

**App-level checks:**
- Are public API contracts preserved for external consumers?
- Are event schemas backward-compatible for downstream subscribers?
- Are configuration file formats backward-compatible?
- Are CLI interfaces backward-compatible?

---

## Edge-Case Matrix

For every critical flow touched by the change, the reviewer MUST systematically consider each category. Not all categories apply to every change — skip with documented reason.

| # | Category | What to Enumerate | Minimum |
|---|----------|-------------------|---------|
| 1 | **Invalid inputs** | null, empty, too large, wrong type, malformed encoding | 2 tests |
| 2 | **Dependency failure** | timeout, 5xx, slow response, partial response, DNS failure | 2 tests |
| 3 | **Duplicate delivery** | same request twice, retry after success, replay attack | 1 test |
| 4 | **Concurrency** | two requests same entity, out-of-order arrival, lost update | 1 test |
| 5 | **Limits** | rate limiting hit, storage full, payload at max size, pagination end | 1 test |
| 6 | **Time** | token expiry, DST transition, clock skew, operation timeout mid-work | 1 test |
| 7 | **Configuration** | missing config, invalid value, config change during operation | 1 test |
| 8 | **Startup/shutdown** | crash during write, graceful shutdown with in-flight requests | 1 test |
| 9 | **Capacity** | at quota, over quota, quota change mid-operation | 1 test |
| 10 | **Upgrade** | mixed versions during deploy, rollback after partial migration | 1 test |

**How to use:** For each critical flow, walk through all 10 categories. Record which are applicable, which are already tested, and which have gaps. Gaps feed into verification test generation.

---

## Severity Decision Guide

Quick reference for common app-level findings. Canonical definitions in `severity-taxonomy.md`.

| Finding Pattern | Severity | Rationale |
|----------------|----------|-----------|
| Security claim without test evidence | P0 | Unverified security is no security |
| External call without timeout | P0 | Unbounded resource consumption |
| Data write without atomicity | P0 | Corruption risk |
| Error swallowed silently | P0 | Incorrect state propagation |
| Missing integration test for failure mode | P1 | Unverified failure behavior |
| Concurrency claim without proof | P1 | Race conditions cause data loss |
| Performance assumption without measurement | P2 | Unquantified risk |
| Pattern inconsistency with codebase | P2 | Maintainability drift |
| Missing log on success path | P3 | Nice-to-have observability |
| Naming inconsistency | P3 | Style, not risk |
