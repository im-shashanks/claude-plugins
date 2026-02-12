# Resilience Practices

Patterns for building systems that survive failure. Reference this file when implementing retry logic, timeouts, circuit breakers, or fallback hierarchies. Complements the essentials in `coding-practices.md` with implementation-ready patterns.

---

## Retry with Exponential Backoff + Jitter

Retry transient failures with increasing delays. Always add jitter to prevent thundering herds.

**Formula:** `delay = min(base * 2^attempt + random(0, jitter), max_delay)`

```
# Pattern (language-agnostic pseudocode)
MAX_RETRIES = 3
BASE_DELAY = 0.5     # seconds
MAX_DELAY = 30        # seconds
JITTER_MAX = 0.5      # seconds

for attempt in range(MAX_RETRIES):
    try:
        return execute_operation()
    except RetryableError:
        if attempt == MAX_RETRIES - 1:
            raise
        delay = min(BASE_DELAY * (2 ** attempt) + random(0, JITTER_MAX), MAX_DELAY)
        sleep(delay)
```

**Critical rules:**
- Only retry **retryable** errors (see Error Classification in `coding-practices.md`). Never retry 400, 401, 404, or validation errors.
- Make retried operations **idempotent** (see `concurrency-practices.md`). Retrying a non-idempotent operation (like a charge) causes double-processing.
- Always set a **max retry count**. Without it, a permanent failure retries forever.
- Always add **jitter**. Without it, all clients retry at the same instant after an outage.

---

## Timeout Guidelines by Operation Type

Every external call needs a timeout. Use these as starting points — tune based on profiling.

| Operation | Connect Timeout | Read/Response Timeout | Notes |
|---|---|---|---|
| HTTP API call | 3s | 10s | Adjust read timeout for known-slow endpoints |
| Database query | 3s | 5s | Set statement-level timeout; don't rely on connection timeout alone |
| Cache read (Redis, Memcached) | 1s | 2s | Cache miss should be fast; long timeout defeats the purpose |
| File I/O (network storage) | 5s | 30s | NFS/S3 can stall; always set both |
| DNS resolution | 2s | — | Often overlooked; can hang indefinitely on misconfigured resolvers |
| Message queue publish | 3s | 5s | Broker backpressure can cause indefinite blocks |

**Rules:**
- Set **both** connect and read timeouts. A connect timeout without a read timeout still hangs on slow responses.
- Read timeout values from **configuration** (`.shaktra/settings.yml` or app config) when possible. Never use language defaults that may be infinite.
- For operations called in a request path, total timeout must be **less than the caller's timeout** to allow error handling before the caller times out.

---

## Circuit Breaker Pattern

Prevent cascading failures by stopping calls to a failing dependency.

**States:**
1. **CLOSED** (normal) — Requests pass through. Track failure count.
2. **OPEN** (tripped) — All requests fail immediately without calling the dependency. Start a reset timer.
3. **HALF-OPEN** (probing) — Allow one test request. If it succeeds → CLOSED. If it fails → OPEN.

```
# Pattern (language-agnostic pseudocode)
FAILURE_THRESHOLD = 5
RESET_TIMEOUT = 60    # seconds

state = CLOSED
failure_count = 0
last_failure_time = None

def call(operation):
    if state == OPEN:
        if now() - last_failure_time > RESET_TIMEOUT:
            state = HALF_OPEN
        else:
            raise CircuitOpenError("dependency unavailable, failing fast")

    try:
        result = operation()
        if state == HALF_OPEN:
            state = CLOSED
            failure_count = 0
        return result
    except RetryableError:
        failure_count += 1
        last_failure_time = now()
        if failure_count >= FAILURE_THRESHOLD:
            state = OPEN
        raise
```

**When to use:** Any dependency that experiences transient outages (external APIs, databases, third-party services). Do NOT use for local operations or in-process calls.

---

## Fallback Hierarchy

When the primary path fails, degrade gracefully through a defined hierarchy.

**Pattern:** Primary → Cache → Default → Error

```
def get_user_profile(user_id):
    # Level 1: Primary source
    try:
        return user_service.get(user_id, timeout=READ_TIMEOUT)
    except (TimeoutError, ServiceUnavailableError):
        log.warning("user_service_unavailable", user_id=user_id)

    # Level 2: Cached data (stale is better than nothing)
    cached = cache.get(f"user:{user_id}")
    if cached:
        log.info("serving_cached_profile", user_id=user_id, stale=True)
        return cached

    # Level 3: Safe default (feature degrades, doesn't break)
    log.warning("serving_default_profile", user_id=user_id)
    return DefaultProfile(user_id)

    # Level 4: If even defaults aren't possible, fail explicitly
    # raise UserProfileUnavailableError(user_id)
```

**Rules:**
- Each fallback level must be **logged** so you can detect degradation in production.
- Fallbacks must not trigger the **same failure** (e.g., don't fall back from API-A to API-A with different params).
- Mark responses from fallback sources so callers know the data may be stale.

---

## Failure Mode Table Template

For Medium+ stories, document expected failure modes during the PLAN phase.

| Dependency | Failure Mode | Detection | Response | Recovery |
|---|---|---|---|---|
| Payment gateway | Timeout (>5s) | Connect/read timeout | Return pending status, enqueue retry | Idempotency key prevents double-charge |
| User DB | Connection refused | Connection pool exception | Fail request with 503 | Circuit breaker; pool reconnect on HALF_OPEN |
| Cache (Redis) | Eviction / unavailable | Cache miss / connection error | Read-through to DB | Auto-reconnect; no user impact |
| Email service | Rate limited (429) | HTTP 429 response | Enqueue with backoff delay | Retry with exponential backoff |

Fill this table for every external dependency in the story's scope. Each row maps to at least one test in `test_specs`.
