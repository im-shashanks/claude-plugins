# Concurrency Practices

Patterns for safe concurrent and parallel operations. Reference this file when implementing idempotent operations, optimistic locking, atomic state changes, or concurrent test harnesses.

---

## Idempotency Patterns

An operation is idempotent when executing it multiple times produces the same result as executing it once. Critical for any operation that may be retried (see `resilience-practices.md`).

### Pattern 1: Idempotency Key

Client generates a unique key per logical operation. Server uses the key to deduplicate.

```
# Server-side pattern
def process_payment(request):
    idempotency_key = request.headers["Idempotency-Key"]

    # Check if this key was already processed
    existing = db.get_by_idempotency_key(idempotency_key)
    if existing:
        return existing.result  # Return the cached result

    # Process and store the result atomically
    result = charge_card(request.amount)
    db.store_result(idempotency_key, result)
    return result
```

**Use when:** Payment processing, order creation, any write that must not duplicate on retry.

### Pattern 2: Natural Idempotency (PUT semantics)

Design the operation so repeated execution is inherently safe — set state rather than modify it.

```
# BAD — not idempotent (increments on retry)
def add_loyalty_points(user_id, points):
    user.points += points

# GOOD — idempotent (sets to final value)
def set_loyalty_points(user_id, transaction_id, new_total):
    if user.last_transaction_id == transaction_id:
        return  # Already applied
    user.points = new_total
    user.last_transaction_id = transaction_id
```

**Use when:** State updates where you can compute the final value.

### Pattern 3: Conditional Write (If-Not-Exists)

Use database constraints or conditional operations to prevent duplicates.

```
# SQL: INSERT only if not exists
INSERT INTO notifications (user_id, event_id, message)
VALUES ($1, $2, $3)
ON CONFLICT (user_id, event_id) DO NOTHING;

# DynamoDB: conditional put
table.put_item(
    Item=record,
    ConditionExpression="attribute_not_exists(event_id)"
)
```

**Use when:** Event processing, notification delivery, any write where a natural unique constraint exists.

---

## Optimistic Locking

Allow concurrent reads but detect conflicts at write time using a version field.

```
# Read with version
record = db.get(id)  # record.version = 5

# Modify locally
record.status = "approved"

# Write with version check — fails if someone else modified it
UPDATE records SET status = $1, version = version + 1
WHERE id = $2 AND version = $3;  -- $3 = 5

# If rows_affected == 0: conflict detected → reload and retry
```

**Rules:**
- Always increment the version on write. Use an integer counter or a timestamp (integer is safer — clocks can collide).
- On conflict, **reload the record** and re-apply business logic. Do not blindly retry the stale write.
- Set a **max conflict retry count** (typically 3). If conflicts persist, the operation fails — something is wrong.
- Prefer optimistic locking over pessimistic (SELECT FOR UPDATE) for read-heavy workloads. Use pessimistic locking only when conflicts are very frequent (>10% of writes).

---

## Atomic Operations

Use database transactions or atomic primitives to ensure state changes are all-or-nothing.

### Database Transactions

```
# Wrap related writes in a single transaction
BEGIN;
  UPDATE accounts SET balance = balance - 100 WHERE id = sender_id;
  UPDATE accounts SET balance = balance + 100 WHERE id = receiver_id;
  INSERT INTO transfers (sender, receiver, amount) VALUES (sender_id, receiver_id, 100);
COMMIT;
-- If any statement fails, all are rolled back
```

### Atomic Compare-and-Swap

```
# Redis: atomic increment with check
WATCH balance_key
current = GET balance_key
if current >= amount:
    MULTI
    DECRBY balance_key amount
    EXEC
else:
    UNWATCH
    raise InsufficientBalance()
```

**Rules:**
- Keep transactions **short**. Long transactions hold locks and degrade throughput.
- Never perform **network calls** inside a transaction. A timeout inside a transaction leaves locks held.
- Order lock acquisition **consistently** across all code paths to prevent deadlocks (e.g., always lock accounts by ascending ID).

---

## Concurrent Test Harness

Testing concurrent code requires purpose-built test patterns. Standard sequential tests cannot detect race conditions.

### Pattern: Deterministic Concurrency Test

```
# Simulate concurrent access with controlled interleaving
def test_concurrent_balance_update():
    account = create_account(balance=100)
    barrier = threading.Barrier(2)  # Synchronize start

    def withdraw():
        barrier.wait()  # Both threads start simultaneously
        account.withdraw(80)

    t1 = Thread(target=withdraw)
    t2 = Thread(target=withdraw)
    t1.start(); t2.start()
    t1.join(); t2.join()

    # Without proper locking, balance could go to -60
    # With proper locking, exactly one withdrawal succeeds
    assert account.balance >= 0
```

### Pattern: Stress Test for Race Conditions

```
# Run many concurrent operations to surface timing-dependent bugs
def test_no_lost_updates_under_contention():
    counter = SharedCounter(initial=0)
    num_threads = 10
    increments_per_thread = 100

    threads = [
        Thread(target=lambda: [counter.increment() for _ in range(increments_per_thread)])
        for _ in range(num_threads)
    ]
    for t in threads: t.start()
    for t in threads: t.join()

    assert counter.value == num_threads * increments_per_thread
```

**Rules:**
- Use **barriers** or **latches** to force concurrent execution (not `sleep`).
- Run stress tests with **enough iterations** to surface timing bugs (100+ per thread minimum).
- Test **both** the happy path (operations succeed under contention) and the conflict path (conflicting operations are detected and handled).
- Mark concurrent tests clearly (naming convention or marker) so they can be run separately — they are slower and may be flaky on constrained CI machines.
