# Adversarial Probe Strategies

Loaded by the adversary agent for Group 2 (Input & Boundary Probes) and Group 3 (Fault & Resilience Probes). Defines probe types, test generation patterns, and finding classification.

---

## Group 2: Input & Boundary Probes

For each changed function that accepts external input (parameters from API calls, user input, file content, network responses, configuration values):

### Probe Types

#### 1. Null/Empty Probes
Test with: `null`, `undefined`, `None`, `""`, `[]`, `{}`, `0`, `false`
- Apply to each parameter individually (not all at once)
- Expected: graceful error, validation rejection, or documented default behavior
- Finding if: crash, unhandled exception, silent data corruption, or unexpected output

#### 2. Type Mismatch Probes
Test with: wrong types for each parameter
- String where integer expected, integer where string expected
- Object where array expected, array where object expected
- Boolean where string expected, nested object where flat value expected
- Expected: type error, validation rejection, or safe coercion
- Finding if: crash, silent wrong behavior, or data corruption

#### 3. Boundary Value Probes
Test with extreme values:
- Numbers: `MAX_INT`, `MIN_INT`, `-1`, `0`, `1`, `MAX_FLOAT`, `NaN`, `Infinity`, `-Infinity`
- Strings: empty string, single char, very long string (10K+ chars), unicode, emoji, RTL text, null bytes
- Collections: empty, single element, very large (1000+ items), nested deeply
- Expected: proper handling or documented limits
- Finding if: overflow, truncation without error, memory issues, or incorrect behavior

#### 4. Injection Probes
Test with common injection payloads:
- **SQL injection:** `' OR '1'='1`, `'; DROP TABLE users; --`, `1; SELECT * FROM`
- **Command injection:** `; ls`, `$(whoami)`, `` `id` ``, `| cat /etc/passwd`
- **XSS payloads:** `<script>alert(1)</script>`, `" onload="alert(1)`, `javascript:alert(1)`
- **Template injection:** `{{7*7}}`, `${7*7}`, `<%= 7*7 %>`
- **Path traversal:** `../../../etc/passwd`, `..\\..\\..\\windows\\system32`
- Expected: input rejected, sanitized, or safely escaped
- Finding if: injection executes, path traversal succeeds, or unsanitized input reaches output

#### 5. Format Probes
Test with malformed structured input:
- Malformed JSON: `{key:}`, `{"key": undefined}`, truncated JSON
- Invalid dates: `2024-13-45`, `0000-00-00`, `9999-99-99`, empty string as date
- Wrong encoding: Latin-1 bytes where UTF-8 expected, BOM-prefixed strings
- Malformed URLs: missing scheme, extra slashes, unicode in hostname
- Expected: parse error caught gracefully, validation rejection
- Finding if: crash, partial parse accepted, or undefined behavior

### Test Generation Pattern

```
For each changed function that accepts external input:
  For each applicable probe type:
    1. Write a test that calls the function with the adversarial input
    2. Assert one of:
       - Graceful error (specific exception type, error return)
       - Validation rejection (before processing)
       - Safe handling (documented behavior for edge case)
    3. Run the test
    4. If function crashes, hangs, produces wrong output, or silently
       corrupts data → record as finding with execution evidence
```

### Finding Classification

| Probe Result | Severity | Rationale |
|---|---|---|
| Injection payload executes | P0 | Security vulnerability — exploitable |
| Crash on null/empty input | P1 | Missing input validation — production failure risk |
| Silent data corruption on boundary | P1 | Data integrity risk — wrong results without error |
| Type mismatch causes wrong behavior | P1 | Type safety gap — unexpected input produces wrong output |
| Crash on extreme boundary value | P2 | Edge case not handled — unlikely but possible in production |
| Format probe causes unhandled exception | P2 | Missing format validation — malformed input not rejected |
| Boundary value produces degraded performance | P2 | Performance risk under extreme input |
| Type coercion produces surprising result | P3 | Implicit conversion — documented behavior may surprise users |

---

## Group 3: Fault & Resilience Probes

For each external dependency identified in changed code (database calls, API calls, file I/O, network requests, message queues, caches, external services):

### Probe Types

#### 1. Timeout Probe
- Mock/stub the dependency to never respond (sleep indefinitely or very long delay)
- Verify: the caller has a timeout and handles it gracefully
- Finding if: function hangs indefinitely, no timeout configured, or timeout not handled

#### 2. Error Response Probe
- Mock dependency to return an error (HTTP 500, exception, error code)
- Verify: error is caught, logged, and handled (retry, fallback, or meaningful error to caller)
- Finding if: error propagates unhandled, swallowed silently, or causes cascading failure

#### 3. Partial Response Probe
- Mock dependency to return incomplete data (truncated response, missing required fields, partial array)
- Verify: code validates response shape before processing
- Finding if: code assumes complete response and crashes or produces wrong results

#### 4. Connection Refused Probe
- Mock dependency to refuse connection entirely
- Verify: connection error is handled distinctly from response errors
- Finding if: connection error causes unhandled exception or misleading error message

#### 5. Slow Response Probe
- Mock dependency with significant delay (e.g., 5-10 seconds) but eventual success
- Verify: no blocking of main thread, no lock held during wait, proper async handling
- Finding if: function blocks, holds locks, or causes upstream timeout

#### 6. Race Condition Probe (when applicable)
Only for code with shared state, async operations, or parallel execution:
- Execute concurrent calls to the same function
- Verify: consistent results, no data corruption, proper synchronization
- Finding if: inconsistent results across runs, data corruption, or deadlock

#### 7. Idempotency Probe (when applicable)
Only for operations that should be safe to retry:
- Call the same function twice with identical input
- Verify: same result both times, no duplicate side effects
- Finding if: duplicate records created, inconsistent state, or different results

### Test Generation Pattern

```
For each external dependency in changed code:
  For each applicable probe type:
    1. Write a test with appropriate mock/stub at the dependency boundary
    2. Assert:
       - Proper error handling (no unhandled exceptions)
       - No data corruption (state consistent after failure)
       - No hang (test completes within timeout)
       - Graceful degradation (meaningful error or fallback)
    3. Run the test
    4. If function crashes, corrupts data, hangs, or propagates
       unhandled error → record as finding with execution evidence
```

### Finding Classification

| Probe Result | Severity | Rationale |
|---|---|---|
| No timeout on external call | P1 | Production hang risk — one slow dependency freezes the system |
| Error swallowed silently | P1 | Silent failure — system appears healthy while data is lost |
| Partial response causes crash | P1 | Fragile integration — real APIs return partial data under load |
| Race condition produces corruption | P0 | Data integrity — concurrent use corrupts state |
| Connection refused unhandled | P2 | Missing resilience — dependency outage causes crash |
| Slow response blocks main thread | P2 | Performance risk — one slow call degrades entire system |
| Idempotency violation | P1 | Retry safety — duplicate operations cause duplicate effects |
| Deadlock under concurrent access | P0 | Availability — system freezes under concurrent load |

---

## Test Persistence

Generated adversarial tests follow `settings.adversarial_review.test_persistence`:

| Setting | Behavior |
|---|---|
| `auto` | Persist tests that found bugs (failed assertions revealing real issues). Discard tests that passed (probes that found no issues). |
| `always` | Persist all generated adversarial tests to the project's test suite. |
| `never` | Discard all adversarial tests after review. Findings are still reported. |
| `ask` | Present results and let the user choose which tests to keep. |

### Persisted Test Location

- Place persisted tests alongside existing tests with an `_adversarial` suffix (e.g., `test_auth_adversarial.py`)
- If the project has no clear test directory, create `tests/adversarial/` and place them there
- Include a comment header in persisted tests: `# Generated by Shaktra adversarial review — {date}`

### Test Cap

Read `settings.adversarial_review.max_adversarial_tests` (default: 20) — cap the total number of adversarial tests generated per probe group. Prioritize probes most likely to find issues based on the behavior contract.
