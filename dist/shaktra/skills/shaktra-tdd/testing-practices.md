# Testing Practices

12 core principles for writing tests in the Shaktra TDD pipeline. These guide the test-agent during RED phase and sw-quality during test review.

---

## 1. Test Behavior, Not Implementation

Tests assert WHAT the code does (outcomes), not HOW it does it (internals). A refactoring that preserves behavior must not break any test.

**The Refactoring Test:** If you rename a private method, change an internal data structure, or reorder implementation steps — and a test breaks — that test is coupled to implementation, not behavior.

**BAD:** `assert mock_db.save.called_with(user)` — proves wiring, not behavior.
**GOOD:** `assert get_user(id) == expected_user` — proves the system returns the right result.

---

## 2. Red-Green-Refactor

The TDD cycle is non-negotiable:
1. **RED:** Write a failing test for the next behavior. Verify it fails.
2. **GREEN:** Write the minimum code to make the test pass.
3. **REFACTOR:** Clean up while keeping tests green.

Never write code without a failing test first. Never refactor while tests are red.

---

## 3. One Behavior Per Test

Each test verifies exactly one behavior — not one assertion, but one logical behavior. Multiple assertions are fine if they verify the same behavior from different angles.

**BAD:** A test that checks user creation AND email sending AND audit logging.
**GOOD:** Three tests: `test_creates_user_with_valid_input`, `test_sends_welcome_email_on_creation`, `test_logs_audit_entry_on_creation`.

---

## 4. Deterministic Testing

Eliminate all sources of non-determinism. Tests that pass "most of the time" are worse than no tests.

**Banned in test code:**
- `time.time()`, `datetime.now()`, `Date.now()` — inject a clock
- `random.random()`, `Math.random()` — use seeded generators or inject values
- Unordered collections compared with `==` — sort before comparing or use set assertions
- `time.sleep()` / `setTimeout()` — use fakes or event-based synchronization

---

## 5. Test Isolation

Each test runs in complete isolation. No test depends on another test's outcome, execution order, or side effects.

**Rules:**
- Each test creates its own fixtures (or uses a factory)
- No shared mutable state between tests (shared constants are fine)
- Cleanup is guaranteed (use `setUp`/`tearDown`, `beforeEach`/`afterEach`, or context managers)
- Tests can run in any order, in parallel, or individually

---

## 6. Arrange-Act-Assert (AAA)

Every test follows the AAA structure with clear visual separation:

```
# Arrange — set up preconditions
user = create_test_user(role="admin")
request = build_request(user_id=user.id)

# Act — execute the behavior under test
response = handle_request(request)

# Assert — verify the outcome
assert response.status == 200
assert response.body["role"] == "admin"
```

The Act section should be exactly one call. If you need multiple calls, you're testing multiple behaviors.

---

## 7. Given-When-Then Naming

Test names describe the scenario, not the implementation:

**Pattern:** `test_<given_context>_<when_action>_<then_outcome>`

**BAD:** `test_process`, `test_handler`, `test_validate`
**GOOD:**
- `test_given_valid_credentials_when_login_then_returns_token`
- `test_given_expired_token_when_access_resource_then_returns_401`
- `test_given_duplicate_email_when_register_then_raises_conflict`

Shorter variant: `test_<action>_<context>_<outcome>` — e.g., `test_login_with_expired_credentials_returns_401`

---

## 8. Mock at Boundaries Only

Mock external dependencies (APIs, databases, filesystems, network calls). Never mock internal modules, private methods, or code you own.

**Mock these (boundaries):**
- HTTP clients, database connections, filesystem I/O
- Third-party service SDKs, message queues, caches
- System clock, random number generators

**Never mock these (internals):**
- Helper functions in the same module
- Private methods of the class under test
- Other classes in the same project (use real instances or test doubles)

**Mock count rule:** If a test has more mocks than real assertions, the test proves nothing. Target: mock count < assertion count.

---

## 9. Edge Case Strategy

Systematically test boundaries and failure modes, not just happy paths:

**Boundary values:** Zero, one, max, max+1, negative, empty string, empty collection.
**Invalid input:** Null/undefined/None, wrong type, out of range, malformed format.
**Timing:** Concurrent access, timeout, retry exhaustion, out-of-order events.
**Duplicates:** Duplicate keys, duplicate submissions, idempotency.
**Resource limits:** Full disk, memory pressure, connection pool exhaustion.

For each error code in the story's `error_handling` section, there must be at least one test.

---

## 10. Error Paths Are First-Class

Error paths are not afterthoughts — they are behaviors that must be tested with the same rigor as happy paths.

**For each error scenario, test:**
- The correct exception type is raised (not bare `Exception`)
- The error message includes sufficient context for debugging
- Side effects are rolled back or not applied
- The caller receives an actionable error (not "Something went wrong")

**Negative test ratio:** At least 30% of tests should be negative (testing failure scenarios). LLMs heavily bias toward happy paths — this ratio counteracts that.

---

## 11. Test Speed Thresholds

Fast tests get run; slow tests get skipped. Keep tests fast to enable continuous feedback.

**Targets:**
- Unit tests: < 10ms each
- Integration tests: < 1s each
- Full suite: < 30s total

If a test needs sleep, timer, or network calls, it belongs in integration tests. Isolate slow tests so unit tests can run independently.

---

## 12. Coverage Is a Minimum, Not a Goal

Coverage thresholds (from `settings.tdd.coverage_threshold`) are floors, not ceilings. Meeting the threshold with low-quality tests is worse than missing it with high-quality ones.

**Coverage rules:**
- Read thresholds from `.shaktra/settings.yml` — never hardcode
- Trivial tier: `settings.tdd.hotfix_coverage_threshold`
- Small tier: `settings.tdd.small_coverage_threshold`
- Medium tier: `settings.tdd.coverage_threshold`
- Large tier: `settings.tdd.large_coverage_threshold`
- Coverage must come from behavioral tests, not from tests that simply execute code without meaningful assertions
