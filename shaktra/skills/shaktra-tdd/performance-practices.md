# Performance Practices

Performance engineering practices for the TDD pipeline. Loaded by sw-engineer during planning and developer during implementation. These practices prevent the most common performance pitfalls that ship to production.

---

## 1. Algorithmic Complexity Awareness

### O(n^2) Traps

Common patterns that introduce quadratic (or worse) complexity on user-controlled input:

| Pattern | Why It's Dangerous | Alternative |
|---------|-------------------|-------------|
| Nested loops over same/related collections | O(n^2) scans; unnoticeable at n=10, catastrophic at n=10,000 | Hash map lookup, index, pre-sort |
| `array.includes()` / `list.index()` inside a loop | Linear search per iteration = O(n^2) | Convert to Set/Map first, then O(1) lookup |
| String concatenation in a loop | Many languages create new string objects per iteration | StringBuilder, join(), array + join |
| Sort inside a loop | O(n * n log n) | Sort once before the loop |
| Repeated full-collection filter inside loop | Scans entire collection per outer iteration | Pre-compute lookup structure |

### Bounded vs Unbounded Input

- **Bounded:** Fixed-size config, enum values, admin-controlled limits → O(n^2) is acceptable
- **Unbounded:** User input, API results, database query results → O(n^2) is a P0/P1 risk
- When in doubt, assume unbounded and design for linear or log-linear

---

## 2. N+1 Query Detection

### The Pattern

```
# BAD: N+1 — 1 query for orders + N queries for users
orders = db.query("SELECT * FROM orders")
for order in orders:
    user = db.query("SELECT * FROM users WHERE id = ?", order.user_id)  # N queries
```

### Detection Signals

| Signal | Example |
|--------|---------|
| DB call inside a loop | `db.query()` or ORM `.get()` inside `for`/`while` |
| ORM lazy-load in loop | Accessing relationship attribute in a loop without eager loading |
| Single-ID function called in loop | `get_user(id)` called per iteration instead of `get_users(ids)` |
| HTTP call inside a loop | `api.get(f"/users/{id}")` per item instead of batch endpoint |

### Batch Alternatives

| N+1 Pattern | Batch Alternative |
|-------------|-------------------|
| Single-row SELECT in loop | `WHERE id IN (...)` with collected IDs |
| ORM lazy-load | Eager load with `select_related` / `include` / `JOIN` |
| Single-ID API call | Batch endpoint or query parameter (`?ids=1,2,3`) |
| Single-row INSERT in loop | Bulk insert (`INSERT INTO ... VALUES (...), (...)`) |

---

## 3. Caching Strategy

### Decision Framework

Cache when:
- Data is read frequently (>10:1 read:write ratio)
- Data is expensive to compute or fetch
- Staleness is acceptable for the use case

Do NOT cache when:
- Data changes frequently relative to reads
- Strong consistency is required (financial balances, inventory counts)
- Cache invalidation is harder than the query

### Cache Patterns

| Pattern | Read | Write | Best For |
|---------|------|-------|----------|
| **Cache-aside** | Check cache → miss → query DB → populate cache | Write to DB; invalidate cache | General purpose; simple |
| **Write-through** | Read from cache (always populated) | Write to DB + cache atomically | Read-heavy; consistency important |
| **Write-behind** | Read from cache | Write to cache; async flush to DB | Write-heavy; can tolerate data loss |

### Invalidation Strategies

| Strategy | How | Trade-offs |
|----------|-----|-----------|
| **TTL** | Cache expires after fixed duration | Simple; stale during TTL; good for rarely-changing data |
| **Event-based** | Invalidate on write event | Consistent; requires event infrastructure |
| **Version-based** | Cache key includes data version | Consistent; requires version tracking |

### Stampede Prevention

When a popular cache key expires, many concurrent requests hit the DB simultaneously:
- **Lock-based:** First requester acquires lock, others wait for cache repopulation
- **Probabilistic early expiry:** Expire slightly before TTL with randomization
- **Background refresh:** Refresh cache before expiry via background job

---

## 4. Connection Pooling

### Pool Sizing Heuristic

```
pool_size = (2 * cpu_cores) + spindle_count
```

For most applications: start with `pool_size = 10-20`, measure, adjust.

### Configuration

| Setting | Guideline |
|---------|----------|
| `min_idle` | 2-5 (avoid cold start; don't waste resources) |
| `max_size` | Based on heuristic; never unbounded |
| `max_wait_ms` | 5000ms (fail fast rather than queue indefinitely) |
| `validation_query` | Simple query to verify connection health (`SELECT 1`) |
| `idle_timeout_ms` | 300000ms (5 min; release unused connections) |
| `max_lifetime_ms` | 1800000ms (30 min; prevent stale connections) |

### Anti-Patterns

- Creating connections per request (no pool)
- Unbounded pool (grows until DB max_connections exhausted)
- No connection validation (using dead connections)
- Leaking connections (acquiring without releasing in error paths)

---

## 5. Pagination and Streaming

### Cursor-Based Pagination

Preferred for large datasets:
- Stable results even when data changes between pages
- Consistent performance regardless of page depth
- Requires a unique, orderable column (usually `id` or `created_at`)

### Offset-Based Pagination

Acceptable when:
- Dataset is small and stable
- Random page access is needed ("jump to page 5")
- Total count is required for UI

### Streaming for Large Payloads

When response would exceed memory limits or take too long:
- Use streaming responses (chunked transfer encoding)
- Process rows incrementally (cursor-based DB reads)
- Set memory bounds on aggregation operations

---

## 6. Profiling Methodology

### Hot Path Identification

1. Identify the critical user-facing paths (login, search, checkout, dashboard load)
2. Measure end-to-end latency for each path
3. Break down: network, application, database, external services
4. Focus optimization on the largest contributor

### Target Latency

| Metric | Target | Action |
|--------|--------|--------|
| p50 | Interactive feel (<200ms for API, <1s for page load) | Baseline; most users' experience |
| p95 | Acceptable degradation (<500ms API, <3s page) | Tail latency; usually DB or external service |
| p99 | Investigation threshold | Outliers; often GC, connection pool exhaustion, or cold cache |

### Measurement Approach

- Measure in production (or production-like environment), not just dev
- Use distributed tracing for multi-service paths
- Measure the whole path, not just the function you optimized
- Before/after comparisons with the same dataset and load

---

## AI-Enforceable Checks

Applied during code review by sw-quality agent. Full detection details in `shaktra-quality/performance-data-checks.md`.

| ID | Check | Severity |
|----|-------|----------|
| PG-01 | Nested iteration on user input without bound | P1 |
| PG-02 | N+1 query (DB call in loop) | P1 |
| PG-03 | Unbounded collection return (no pagination) | P1 |
| PG-04 | Per-request connection creation (no pool) | P1 |
| PG-05 | Cache without TTL or invalidation strategy | P1 |
| PG-06 | O(n^2)+ algorithm on unbounded input | P0 |
| PG-07 | String concatenation in loop (language-dependent) | P2 |
| PG-08 | Missing connection pool configuration (idle timeout, max lifetime) | P2 |
