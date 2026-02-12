# Quick-Check — ~36 High-Impact Checks

36 checks organized by gate. The sw-quality agent loads all checks regardless of tier and applies the gate-specific subset during each TDD phase review.

**Check depth behavior** (from `story-tiers.md`):
- **Quick** (Trivial/Small): All checks applied; P2+ findings reported as observations, not blockers.
- **Full** (Medium): All checks applied with standard severity enforcement.
- **Thorough** (Large): All checks applied; expanded review in comprehensive-review.md adds architecture and dependency analysis.

---

## Plan Gate (5 checks — Medium+ tiers only)

Applied during PLAN phase review. Focus: "What would bite us in production?"

### PL-01 — AC ↔ Test Plan Mapping (P1)

Every acceptance criterion must map to at least one planned test.

**BAD:** Story has 5 ACs, test plan covers 3 — two behaviors will ship untested.
**GOOD:** Every AC has a named test; error codes each have a negative test.

### PL-02 — Error Handling Test Plans (P1)

Every error code in the story's `error_handling` must have a planned test.

**BAD:** Story defines `ERR_TIMEOUT`, `ERR_AUTH_FAILED`; test plan only mentions happy paths.
**GOOD:** `test_given_timeout_when_fetch_then_returns_ERR_TIMEOUT` planned for each error code.

### PL-03 — Failure Mode Analysis (P1)

Plan must identify failure modes relevant to the story's scope.

**BAD:** Plan for an API integration mentions no timeout, retry, or partial failure scenarios.
**GOOD:** "Redis timeout → fallback to DB", "Partial write → transaction rollback".

### PL-04 — Scope-Specific Risks (P2)

Plan identifies risks specific to scope and proposes mitigation.

**BAD:** No `scope_risks`, or risks are generic ("something might go wrong").
**GOOD:** Concrete risks with likelihood and prevention strategy per scope type.

### PL-05 — Implementation Order (P2)

Implementation order minimizes coupling — fewer-dependency components first.

**BAD:** Controller before the service it depends on — forces interface guessing.
**GOOD:** Data layer → service layer → controller — each builds on stable foundation.

---

## Test Gate (13 checks)

Applied during RED phase review. Focus: test quality, behavioral assertions, isolation.

### TQ-01 — Error Path Coverage (P0)

Every error code from the story's `error_handling` must have at least one test.

**BAD:** Story defines 4 error codes; tests only cover the happy path.
**GOOD:** Each error code has a dedicated negative test with specific exception assertions.

### TQ-02 — No Mock-Only Assertions (P1)

Tests must assert behavior (outcomes), not just that a mock was called.

**Look for:** `assert mock.called`, `mock.assert_called_with(...)` as the ONLY assertion in a test.
**BAD:** `mock_db.save.assert_called_once_with(user)` — proves wiring, not behavior.
**GOOD:** `assert get_user(saved_id) == expected_user` — proves the system works.

### TQ-03 — No Over-Mocking (P1)

Mock count should be less than real assertion count. Tests with 5+ mocks test nothing real.

**BAD:** 6 mocks, 2 assertions — exercises mocking framework, not production code.
**GOOD:** 1 mock (external API), 4 assertions on actual return values and side effects.

### TQ-04 — Test Isolation (P1)

No shared mutable state between tests. Each test creates its own fixtures.

**BAD:** `test_data = []` at module level, tests append to it, later tests depend on contents.
**GOOD:** Each test creates its own list via fixture or factory.

### TQ-05 — No Flickering Tests (P1)

Tests must not use real time, random, or non-deterministic operations.

**BAD:** `assert result.created_at == datetime.now()` — fails if clock ticks between call and assert.
**GOOD:** `clock = FakeClock(fixed_time); assert result.created_at == fixed_time`.

### TQ-06 — No Empty Assertions (P1)

Every test has at least one meaningful assertion. Tests without assertions prove nothing.

**BAD:** `def test_create_user(): create_user("test")` — runs code but verifies nothing.
**GOOD:** `def test_create_user(): user = create_user("test"); assert user.name == "test"`.

### TQ-07 — Mock at Boundaries Only (P1)

Mock external dependencies (APIs, DBs, filesystems). Never mock internal project code.

**BAD:** `@mock.patch("myapp.services.user_service.validate")` — mocking internal logic.
**GOOD:** `@mock.patch("myapp.services.user_service.http_client.post")` — mocking external boundary.

### TQ-08 — Invariant Coverage (P1)

Business invariants are tested both positively (invariant holds) and negatively (violation is caught).

**Look for:** Business rules from the story's ACs that are only tested in one direction.
**BAD:** Tests that an order total is positive, but no test for what happens with zero/negative.
**GOOD:** `test_order_total_sums_items` + `test_order_rejects_negative_quantity`.

### TQ-09 — Happy Path Coverage (P1)

AC scenarios from `io_examples` have corresponding tests with matching inputs and expected outputs.

**Look for:** `io_examples` in the story without corresponding test cases.
**BAD:** Story provides 3 io_examples; tests use different inputs entirely.
**GOOD:** Tests use the exact inputs from io_examples and verify the exact expected outputs.

### TQ-10 — Specific Exception Assertions (P2)

Tests catch specific exception types, not bare `Exception` or `Error`.

**BAD:** `with pytest.raises(Exception):` — any exception passes, including unrelated ones.
**GOOD:** `with pytest.raises(OrderNotFoundError, match="ORD-123"):`.

### TQ-11 — Tests Verify Behavior, Not Structure (P2)

Tests should survive internal refactoring. If changing a private method breaks a test, the test is structural.

**BAD:** `assert obj._internal_cache == {"key": "value"}` — coupled to internal state.
**GOOD:** `assert obj.get("key") == "value"` — tests through the public interface.

### TQ-12 — Negative Test Ratio (P2)

At least 30% of tests should be negative (testing failure scenarios).

**BAD:** 10 tests, all happy path — zero negative tests.
**GOOD:** 10 tests: 7 happy path, 3 negative (invalid input, timeout, auth failure).

### TQ-13 — Descriptive Test Names (P2)

Test names follow given/when/then or behavior-based naming that conveys intent.

**BAD:** `test_handler` — what handler? What scenario? What outcome?
**GOOD:** `test_given_expired_token_when_access_resource_then_returns_401`.

---

## Code Gate (18 checks)

Applied during GREEN phase review. Focus: security, reliability, production-readiness.

### CQ-01 — Hallucinated Imports (P0)

All imports must resolve to real modules in stdlib, project, or declared dependencies.

**Look for:** Import statements for non-existent packages, misspelled module names, fabricated APIs.
**BAD:** `from fastapi.security import OAuth2ClientBearer` — this class doesn't exist.
**GOOD:** `from fastapi.security import OAuth2PasswordBearer` — real API.

### CQ-02 — Missing Input Validation (P0)

User input used in queries, commands, eval, or template rendering must be validated first.

**Look for:** Request parameters passed directly to database queries, OS commands, or template engines.
**BAD:** `os.system(f"convert {user_filename}")` — command injection.
**GOOD:** Validate filename against allowlist, use `subprocess.run(["convert", filename])`.

### CQ-03 — External Calls Have Timeouts (P0)

Every HTTP request, DB query, RPC call, and network file operation has an explicit timeout.

**Look for:** `requests.get(url)` without `timeout=`, database queries without statement timeout, gRPC calls without deadline.
**BAD:** `requests.get(url)` — default timeout may be infinite.
**GOOD:** `requests.get(url, timeout=read_timeout_from_config())`.

### CQ-04 — No Hardcoded Credentials (P0)

No secrets, API keys, passwords, or tokens in source code.

**Look for:** Strings matching API key patterns, `password=`, `secret=`, `token=` with literal values.
**BAD:** `API_KEY = "sk-abc123def456"` in source code.
**GOOD:** `API_KEY = os.environ["API_KEY"]`.

### CQ-05 — Bounded User Input Operations (P0)

No unbounded loops, joins, or recursive processing on external input.

**Look for:** `for item in user_provided_list:` without length check, unbounded string concatenation, recursive calls without depth limit.
**BAD:** `" ".join(user_tags)` where `user_tags` has no size limit.
**GOOD:** `if len(user_tags) > MAX_TAGS: raise ValidationError(...)`.

### CQ-06 — Placeholder Logic (P1)

No TODO, FIXME, NotImplementedError, or pass statements in execution paths.

**Look for:** `TODO: implement`, `raise NotImplementedError`, `pass` in non-abstract methods, `// placeholder` comments.
**BAD:** `def process_payment(order): raise NotImplementedError` — in a code path that will execute.
**GOOD:** Full implementation or explicit removal of the unfinished feature.

### CQ-07 — Generic Error Messages (P1)

Error messages must include sufficient context for debugging.

**Look for:** `raise Exception("Failed")`, `raise Error("Something went wrong")`, `raise RuntimeError("Error")`.
**BAD:** `raise Exception("Failed")` — what failed, why, in what context?
**GOOD:** `raise PaymentError(f"Charge failed for order {order_id}: {gateway_response.code}")`.

### CQ-08 — No Exception Swallowing (P1)

Every catch/except block must re-raise, log, or return a meaningful error.

**Look for:** `except: pass`, `except Exception: pass`, `catch (e) {}`, empty catch blocks.
**BAD:** `try: send_email() except: pass` — email failures silently ignored.
**GOOD:** `try: send_email() except EmailError as e: logger.error("email_failed", error=str(e))`.

### CQ-09 — Error Classification (P1)

Errors are classified as retryable vs permanent where retry logic exists.

**Look for:** Retry loops that catch all exceptions without distinguishing type.
**BAD:** `except Exception: retry()` — retries permanent errors (400) alongside transient ones (503).
**GOOD:** `except RetryableError: retry()` with separate handling for permanent errors.

### CQ-10 — Copy-Paste Errors (P1)

No duplicated code blocks with subtle variable name mismatches.

**Look for:** Near-identical blocks where one variable was not renamed during copy-paste.
**BAD:** Two blocks processing `user_a` and `user_b`, but the second still references `user_a` in one line.
**GOOD:** Extract shared logic into a function, or verify all names match.

### CQ-11 — Code Duplication (P1)

No significant duplication (> 10% of changed code is duplicated logic).

**Look for:** Copy-pasted functions, repeated patterns that should be extracted.
**BAD:** Three handler functions with identical validation → processing → response pattern.
**GOOD:** Extract shared pattern into a reusable function or decorator.

### CQ-12 — Nesting Depth (P1)

No function exceeds 4 levels of nesting (if/for/try/with).

**Look for:** Deeply nested conditional or loop structures.
**BAD:** `if → for → if → try → if` — 5 levels deep, unreadable.
**GOOD:** Extract inner blocks into named functions or use early returns.

### CQ-13 — Cyclomatic Complexity (P2)

No function exceeds 10 branch points.

**Look for:** Functions with many if/elif/else, case/switch, and/or, ternary operators.
**BAD:** A function with 15 conditional branches — untestable without 15+ test cases.
**GOOD:** Split into smaller functions, use strategy pattern or lookup tables.

### CQ-14 — Generic Naming (P2)

No generic function or variable names that reveal no intent.

**Look for:** `process()`, `handle()`, `do_thing()`, `data`, `result`, `temp`, `item`, `val`, `obj`.
**BAD:** `def process(data): result = handle(data); return result`.
**GOOD:** `def calculate_shipping_cost(order): cost = apply_zone_rates(order); return cost`.

### CQ-15 — Magic Numbers/Strings (P2)

Literal values in logic must be named constants.

**Look for:** Bare numbers in comparisons, string literals in conditions, timeout values inline.
**BAD:** `if retries > 3:`, `if status == "active":`, `timeout=30`.
**GOOD:** `if retries > MAX_RETRIES:`, `if status == UserStatus.ACTIVE:`.

### CQ-16 — Self-Admitted Technical Debt (P2)

No TODO, FIXME, HACK, "temporary", or "quick fix" left in production code.

**Look for:** Comments or strings containing debt markers.
**BAD:** `# TODO: handle edge case properly`, `# HACK: workaround for bug #123`.
**GOOD:** Either fix the issue now or create a tracked story for it and remove the comment.

### CQ-17 — God Functions / SRP Violations (P2)

Functions should have a single responsibility. If the name contains "and", it should be two functions.

**Look for:** Functions over 50 lines, functions doing unrelated things, function names with "and".
**BAD:** `validate_and_save_and_notify(user)` — three responsibilities.
**GOOD:** `validate(user)`, `save(user)`, `notify(user)` — composed by the caller.

### CQ-18 — Resource Lifecycle Management (P1)

Resources that are acquired must be released — file handles, database connections, network sockets, locks, temporary files.

**Look for:** `open()` without `with`, manual `.close()` without try/finally, acquired locks without guaranteed release.
**BAD:** `f = open(path); data = f.read()` — leaks if exception occurs before close.
**GOOD:** `with open(path) as f: data = f.read()` — context manager guarantees cleanup.
Use `with`/context managers (Python), `defer` (Go), try-with-resources (Java), `using` (C#), or RAII (Rust).
