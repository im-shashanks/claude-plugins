# Data Layer Practices

Data access and query optimization practices for the TDD pipeline. Loaded by sw-engineer during planning and developer during implementation. These practices ensure efficient, safe, and maintainable database interactions.

---

## 1. Query Optimization

### SELECT Specific Columns

- Never use `SELECT *` in application code — it fetches unused columns, prevents covering indexes, and breaks when schema changes
- Explicitly list the columns needed: `SELECT id, name, email FROM users`
- `SELECT *` is acceptable in ad-hoc queries, debugging, and schema exploration — never in production code paths

### Index-Aware WHERE Clauses

- Check that WHERE columns are indexed (or part of a composite index with correct prefix)
- Avoid functions on indexed columns: `WHERE LOWER(email) = ?` negates the index — use a functional index or normalize on write
- Avoid leading wildcards: `WHERE name LIKE '%smith'` cannot use an index — restructure or use full-text search

### EXPLAIN Before Ship

- Run `EXPLAIN` (or equivalent) on every new query touching tables with >1000 rows
- Look for: full table scans, missing index usage, high row estimates, filesort, temporary tables
- Document expected query plan in the implementation plan for Medium+ stories

### Join Optimization

- Ensure join columns are indexed on both sides
- Prefer smaller result sets on the driving table (the table in the FROM clause)
- Avoid joining on computed/derived values

---

## 2. Transaction Management

### Minimize Scope

- Keep transactions as short as possible — hold locks for the minimum duration
- Compute business logic before opening the transaction; execute only DB operations inside
- Never include user input waits, network calls, or file I/O inside a transaction

### Never Network Calls Inside Transactions

This is a P0 violation:
- Network calls can timeout, holding DB locks for seconds or minutes
- Failed network calls leave the transaction in an uncertain state
- Pattern: execute network call first, then use the result inside a short transaction

### Isolation Level Selection

| Level | Use When | Trade-off |
|-------|---------|----------|
| READ COMMITTED | Default for most OLTP | May see non-repeatable reads |
| REPEATABLE READ | Need consistent snapshot within transaction | Higher lock contention |
| SERIALIZABLE | Financial calculations, inventory | Highest contention; retry on serialization failure |

Use the lowest isolation level that satisfies correctness requirements.

### Savepoints

- Use savepoints for partial rollback within a transaction
- Useful for "try this, fall back to that" patterns
- Each savepoint has overhead — don't nest deeply

---

## 3. Batch Processing

### Bulk Operations

| Single-Row Pattern | Bulk Alternative | Benefit |
|-------------------|------------------|---------|
| INSERT in loop | Bulk INSERT with multiple value sets | 10-100x fewer round trips |
| UPDATE in loop | UPDATE with CASE/WHEN or temp table join | Single statement, single lock |
| DELETE in loop | DELETE with IN clause or batch | Fewer round trips, predictable locking |

### Batch Configuration

- **Batch size:** Configurable (not hardcoded) — start with 500-1000, tune based on row size and DB capacity
- **Progress tracking:** Log progress per batch for long-running operations
- **Resumability:** Track last processed ID/cursor so a failed batch can resume without reprocessing
- **Backpressure:** Pause if downstream cannot keep up (queue depth, memory limits)

---

## 4. Cache Invalidation

### Read-Through Pattern

```
function get_user(id):
    cached = cache.get(f"user:{id}")
    if cached: return cached
    user = db.query("SELECT ... WHERE id = ?", id)
    cache.set(f"user:{id}", user, ttl=300)
    return user
```

### Write-Through with Delete-Over-Set

On writes, **delete** the cache key rather than setting it:
- Avoids race conditions where a stale SET overwrites a newer value
- Next read repopulates from the source of truth
- Exception: write-through with atomic DB+cache update (if supported by infrastructure)

### Distributed Cache Consistency

- Accept eventual consistency (cache TTL as the consistency window)
- For tighter consistency: use pub/sub invalidation across nodes
- Never rely on local cache alone in multi-instance deployments without invalidation

### Stampede Prevention

Reference `performance-practices.md` Section 3 — Stampede Prevention. Apply lock-based or probabilistic early expiry for high-traffic cache keys.

---

## 5. Data Access Organization

### Repository Pattern

- Encapsulate all data access for a domain entity in a repository class/module
- Repository exposes domain-level methods (`find_active_users()`) not SQL
- Repositories are the only code that contains SQL/ORM queries
- Controllers and services never construct queries directly

### Query Builder vs Raw SQL

| Approach | Use When |
|----------|---------|
| ORM/Query builder | Standard CRUD, simple joins, pagination |
| Raw SQL | Complex queries (CTEs, window functions, recursive), performance-critical paths |

When using raw SQL: parameterize all inputs (no string interpolation), document the query purpose, and add the query to the test suite.

### Connection Lifecycle

- Acquire connections from the pool at the start of the request/operation
- Release connections back to the pool after the operation completes
- Use context managers / try-finally / middleware to guarantee release on error paths
- Never store connections in long-lived objects (class fields, module globals)

---

## AI-Enforceable Checks

Applied during code review by sw-quality agent. Full detection details in `shaktra-quality/performance-data-checks.md`.

| ID | Check | Severity |
|----|-------|----------|
| DL-01 | SELECT * in application code | P2 |
| DL-02 | Query on unindexed field (large table) | P1 |
| DL-03 | Network call inside transaction | P0 |
| DL-04 | Loop-based single-row mutations (INSERT/UPDATE/DELETE in loop) | P1 |
| DL-05 | Cache mutation without invalidation | P1 |
| DL-06 | Hardcoded batch size (not configurable) | P2 |
| DL-07 | Connection acquired without guaranteed release (no context manager/finally) | P1 |
| DL-08 | Raw SQL with string interpolation (injection risk — also covered by SE-01) | P0 |
