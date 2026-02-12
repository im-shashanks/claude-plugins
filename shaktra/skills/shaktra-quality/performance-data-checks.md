# Performance & Data Layer Checks

Gate-specific checks loaded by sw-quality during code review. These checks detect the most impactful performance and data layer issues that commonly ship to production.

---

## Performance Checks

### PG-01: Nested Iteration on User Input

- **Severity:** P1
- **Detection:** Loop variable from one collection used to filter/search another collection inside the loop body, where input size is unbounded
- **Example (bad):** `for item in items: for other in others: if item.id == other.ref:`
- **Example (good):** Pre-build lookup map: `lookup = {o.ref: o for o in others}; for item in items: match = lookup.get(item.id)`
- **Applies to:** Code gate

### PG-02: N+1 Query

- **Severity:** P1
- **Detection:** Database query, ORM `.get()`/`.load()`, or API call inside a loop body
- **Example (bad):** `for order in orders: user = db.get_user(order.user_id)`
- **Example (good):** `user_ids = [o.user_id for o in orders]; users = db.get_users(user_ids)`
- **Applies to:** Code gate

### PG-03: Unbounded Collection Return

- **Severity:** P1
- **Detection:** API endpoint or function that returns a collection without pagination (no limit, no cursor, no page_size)
- **Example (bad):** `return db.query("SELECT * FROM logs")`
- **Example (good):** `return db.query("SELECT * FROM logs ORDER BY id LIMIT ? OFFSET ?", limit, offset)`
- **Applies to:** Code gate, Plan gate (API design)

### PG-04: Per-Request Connection Creation

- **Severity:** P1
- **Detection:** `new Connection()`, `connect()`, or `create_engine()` inside a request handler or function called per-request
- **Example (bad):** `def handle(req): conn = db.connect(); ...`
- **Example (good):** Connection acquired from pool configured at application startup
- **Applies to:** Code gate

### PG-05: Cache Without TTL or Invalidation

- **Severity:** P1
- **Detection:** `cache.set(key, value)` without TTL parameter and no nearby invalidation logic
- **Example (bad):** `cache.set("user:1", user_data)` — cached forever, never invalidated
- **Example (good):** `cache.set("user:1", user_data, ttl=300)` or event-based invalidation on user update
- **Applies to:** Code gate

### PG-06: O(n^2)+ on Unbounded Input

- **Severity:** P0
- **Detection:** Nested loops where outer loop iterates over unbounded user input AND inner operation is O(n) (linear search, string concat, sort)
- **Distinguishing from PG-01:** PG-06 is P0 when the input is demonstrably unbounded (API request body, query result without LIMIT). PG-01 is P1 for bounded-but-large inputs.
- **Applies to:** Code gate

### PG-07: String Concatenation in Loop

- **Severity:** P2
- **Detection:** String concatenation (`+` operator on strings) inside a loop body, in languages where strings are immutable (Python, Java, JavaScript, Go)
- **Example (bad):** `result = ""; for item in items: result += str(item)`
- **Example (good):** `result = "".join(str(item) for item in items)` or use StringBuilder
- **Applies to:** Code gate

### PG-08: Missing Connection Pool Configuration

- **Severity:** P2
- **Detection:** Connection pool created without idle timeout, max lifetime, or validation query configuration
- **Example (bad):** `pool = create_pool(max_size=20)` — no idle timeout, no max lifetime
- **Example (good):** `pool = create_pool(max_size=20, idle_timeout=300, max_lifetime=1800, validation_query="SELECT 1")`
- **Applies to:** Code gate

---

## Data Layer Checks

### DL-01: SELECT * in Application Code

- **Severity:** P2
- **Detection:** `SELECT *` in query strings or ORM calls that fetch all columns in production code paths (not tests, not scripts)
- **Example (bad):** `db.query("SELECT * FROM users WHERE id = ?", id)`
- **Example (good):** `db.query("SELECT id, name, email FROM users WHERE id = ?", id)`
- **Applies to:** Code gate

### DL-02: Query on Unindexed Field

- **Severity:** P1
- **Detection:** WHERE clause on a column without an index, on a table expected to have significant rows. Requires schema context.
- **Note:** This check requires knowledge of the table schema. If schema is available (migration files, ORM models), verify. If not, flag as observation (P2).
- **Applies to:** Code gate

### DL-03: Network Call Inside Transaction

- **Severity:** P0
- **Detection:** HTTP call, RPC call, queue publish, or external service call within a database transaction block
- **Example (bad):** `with db.transaction(): result = api.charge_payment(amount); db.update_balance(result)`
- **Example (good):** `result = api.charge_payment(amount); with db.transaction(): db.update_balance(result)`
- **Applies to:** Code gate

### DL-04: Loop-Based Single-Row Mutations

- **Severity:** P1
- **Detection:** INSERT, UPDATE, or DELETE statement inside a loop body (one row per iteration)
- **Example (bad):** `for user in users: db.execute("INSERT INTO audit VALUES (?)", user.id)`
- **Example (good):** `db.execute("INSERT INTO audit VALUES " + ",".join(["(?)"] * len(users)), user_ids)`
- **Applies to:** Code gate

### DL-05: Cache Mutation Without Invalidation

- **Severity:** P1
- **Detection:** Database write (INSERT/UPDATE/DELETE) to a table that has a corresponding cache key, without invalidating or updating the cache
- **Note:** Requires mapping between DB tables and cache keys. If mapping is unclear, flag as observation.
- **Applies to:** Code gate

### DL-06: Hardcoded Batch Size

- **Severity:** P2
- **Detection:** Batch processing with hardcoded numeric literal for batch size (not configurable via settings or parameter)
- **Example (bad):** `for i in range(0, len(items), 500): process(items[i:i+500])`
- **Example (good):** `batch_size = config.get("batch_size", 500); for i in range(0, len(items), batch_size): ...`
- **Applies to:** Code gate

### DL-07: Connection Without Guaranteed Release

- **Severity:** P1
- **Detection:** Database connection acquired without context manager, try/finally, or middleware guaranteeing release on error paths
- **Example (bad):** `conn = pool.acquire(); result = conn.execute(query); conn.release()`
- **Example (good):** `with pool.acquire() as conn: result = conn.execute(query)`
- **Applies to:** Code gate

### DL-08: Raw SQL with String Interpolation

- **Severity:** P0
- **Detection:** SQL query string built with string interpolation (f-strings, `format()`, `%` operator, template literals, concatenation) instead of parameterized queries. Also covered by SE-01.
- **Example (bad):** `db.execute(f"SELECT * FROM users WHERE name = '{name}'")`
- **Example (good):** `db.execute("SELECT * FROM users WHERE name = ?", (name,))`
- **Applies to:** Code gate
