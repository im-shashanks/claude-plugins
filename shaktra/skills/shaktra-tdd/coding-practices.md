# Coding Practices

Implementation patterns, error handling, security, observability, and resilience essentials for the Shaktra TDD pipeline. Guides the developer agent during GREEN phase and sw-engineer during planning.

---

## Implementation Patterns

### Single Responsibility

Each function, class, or module has one reason to change. If the name contains "and" — split it.

**BAD:** `validate_and_save_user()` — two responsibilities.
**GOOD:** `validate_user()` + `save_user()` — each does one thing.

**Size guidance:** Functions under 30 lines, classes under 200 lines, modules under 500 lines. These are guidelines, not hard limits — readability trumps line counts.

### Dependency Injection

Accept collaborators as parameters; never construct them internally. This enables testing and swapping.

**BAD:** `def send_email(): client = SmtpClient("smtp.prod.com")` — untestable.
**GOOD:** `def send_email(client: EmailClient):` — injectable, testable.

### Early Returns

Handle edge cases and errors at the top of functions. The main logic lives at the lowest indentation level.

**BAD:** Deeply nested if/else chains.
**GOOD:** Guard clauses that return/raise early, keeping the happy path flat.

### Small Functions

Extract when a block of code:
- Has a different level of abstraction than its surroundings
- Could be given a meaningful name that reveals intent
- Is duplicated more than once

Do NOT extract single-use code into a function just for "cleanliness." Three similar lines are better than a premature abstraction.

---

## Error Handling

### Explicit Error Paths

Every operation that can fail has an explicit handler. No implicit assumption of success.

**BAD:** `data = json.loads(response.text)` — crashes on invalid JSON with no context.
**GOOD:**
```
try:
    data = json.loads(response.text)
except json.JSONDecodeError as e:
    raise ParseError(f"Invalid JSON from {endpoint}: {e}") from e
```

### Error Classification

Distinguish retryable from permanent errors. Without this classification, no retry logic is possible.

**Retryable:** Network timeout, connection refused, rate limit (429), server error (503).
**Permanent:** Bad request (400), not found (404), authentication failure (401), validation error.

### Context-Rich Errors

Error messages must contain enough information to reproduce the issue without reading the code.

**BAD:** `raise Exception("Failed")` — what failed? Where? Why?
**GOOD:** `raise OrderProcessingError(f"Failed to charge card for order {order_id}: gateway returned {status_code}")` — specific type, context, root cause.

### No Exception Swallowing

`except: pass` and `catch (e) {}` hide real failures. Every catch block must:
- Re-raise the exception, OR
- Log the error with full context, OR
- Return a meaningful error to the caller

---

## Security Essentials

### Input Validation at Boundaries

Validate all external input where it enters the system — HTTP handlers, CLI parsers, file readers, message consumers. Never trust data that crosses a trust boundary.

**Validate:** Type, range, length, format, allowed values.
**Reject:** Inputs that fail validation with specific error messages (not stack traces).

### Parameterized Queries

Never interpolate user input into queries, commands, or templates.

**BAD:** `f"SELECT * FROM users WHERE id = {user_id}"` — SQL injection.
**GOOD:** `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))` — parameterized.

This applies to SQL, shell commands, template engines, LDAP queries, and any string-based API that interprets input.

### Secrets via Configuration

Credentials, API keys, and tokens come from environment variables or secret managers. Never from source code, config files checked into version control, or command-line arguments visible in process lists.

**BAD:** `API_KEY = "sk-abc123..."` — hardcoded in source.
**GOOD:** `API_KEY = os.environ["API_KEY"]` — from environment.

### Output Encoding

When rendering user-provided data in HTML, logs, or error messages, encode the output to prevent injection.

- HTML context: HTML-encode `<`, `>`, `&`, `"`, `'`
- Log context: Sanitize newlines and control characters to prevent log injection
- Error messages: Never include raw user input in messages shown to other users

### Web Security Patterns

**XSS Prevention:**
- Use framework-provided auto-escaping for templates (Jinja2 `autoescape=True`, React JSX, Go `html/template`). Never use `|safe`, `dangerouslySetInnerHTML`, or `text/template` with user data.
- Validate and sanitize rich-text input with an allowlist-based sanitizer (e.g., Bleach, DOMPurify). Blocklists are always incomplete.
- Set `Content-Security-Policy` headers to restrict script sources. At minimum: `default-src 'self'; script-src 'self'`.

**CSRF Prevention:**
- Require a CSRF token on all state-changing requests (POST, PUT, DELETE). Most frameworks provide middleware — enable it.
- Verify the `Origin` or `Referer` header matches the expected domain on state-changing requests.
- Use `SameSite=Lax` or `SameSite=Strict` on session cookies.

**Deserialization Safety:**
- Never deserialize untrusted data with formats that execute code: Python `pickle`/`shelve`, Java `ObjectInputStream`, Ruby `Marshal.load`, PHP `unserialize`.
- Use data-only formats (JSON, MessagePack, Protocol Buffers) for untrusted input.
- If YAML is required, use `yaml.safe_load()` — never `yaml.load()` without `Loader=SafeLoader`.

**Authentication & Session:**
- Hash passwords with `bcrypt`, `scrypt`, or `argon2` — never MD5, SHA-1, or SHA-256 alone.
- Generate session tokens with a cryptographic RNG (`secrets.token_urlsafe()`, `crypto.randomBytes()`). Never use predictable values.
- Set cookie flags: `HttpOnly`, `Secure`, `SameSite`.

---

## Observability Essentials

### Structured Logging

Log entries use key-value pairs, not string interpolation. Structured logs are queryable; interpolated strings are not.

**BAD:** `logger.info(f"User {user_id} created order {order_id}")` — not queryable.
**GOOD:** `logger.info("order_created", user_id=user_id, order_id=order_id)` — queryable by any field.

### Correlation IDs

Every cross-boundary call (HTTP, message queue, RPC) carries a correlation ID. Generate at the entry point; propagate through all downstream calls.

This enables tracing a request across services without grep-by-timestamp guesswork.

### Error Context

Every logged error includes enough context to reproduce the issue:
- What operation was attempted
- What input triggered the error
- What the expected vs actual outcome was
- The correlation ID (if applicable)

---

## Resilience Essentials

### Timeouts on All External Calls

Every HTTP request, database query, RPC call, and file operation on network storage has an explicit timeout. Missing timeouts cascade into production outages.

Read timeout values from configuration when possible. Never use language defaults that may be infinite.

### Bounded Operations on User Input

Never perform unbounded operations on external input:
- No unbounded loops over user-provided collections
- No unbounded string joins or concatenations
- No recursive processing without depth limits
- No unbounded queue growth from external producers

Cap all operations with explicit limits. If the input exceeds the limit, reject it early with a clear error.

### Graceful Degradation

When a non-critical dependency fails, the system continues operating with reduced functionality rather than failing entirely.

**Pattern:** Check if the dependency is available. If not, skip the non-critical feature and log the degradation. If the dependency IS critical, fail fast with a clear error.

---

## Anti-Patterns

These are the most common AI-generated code problems. The sw-quality agent checks for all of them.

| Anti-Pattern | What It Looks Like | Why It's Bad |
|---|---|---|
| Generic naming | `process()`, `handle()`, `data`, `result`, `temp` | Reveals no intent; forces code reading |
| Placeholder logic | `TODO: implement`, `NotImplementedError`, `pass` in execution paths | Incomplete code shipped as complete |
| Exception swallowing | `except: pass`, `catch(e) {}` | Silent failures corrupt state |
| God functions | 100+ line functions doing multiple things | Untestable, unreadable, unmaintainable |
| Magic numbers | `if retries > 3`, `timeout=30`, `limit=100` | Hardcoded values obscure meaning; use named constants |
| Copy-paste errors | Duplicated blocks with subtle variable name mismatches | LLMs duplicate and forget to rename |
| SATD | `FIXME`, `HACK`, `"temporary"`, `"quick fix"` left in production code | Self-admitted tech debt compounds |
