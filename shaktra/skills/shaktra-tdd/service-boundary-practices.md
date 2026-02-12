# Service Boundary Practices

Design-first service and module boundary practices. Loaded by the architect agent during design doc creation and by tpm-quality during design review. Ensures clean ownership, explicit communication contracts, and failure isolation before implementation begins.

---

## 1. Bounded Context Identification

### Entity Ownership

Every domain entity belongs to exactly one bounded context:
- The owning context is the **single source of truth** for that entity's state
- Other contexts hold read-only projections, not copies
- When in doubt, ask: "Who creates, updates, and deletes this entity?" — that's the owner

### Context Mapping

Document relationships between bounded contexts:

| Relationship | Pattern | Example |
|-------------|---------|---------|
| **Shared Kernel** | Shared code/schema, both teams must agree on changes | Common domain types |
| **Customer-Supplier** | Upstream supplies, downstream consumes; upstream accommodates | Payment service → Order service |
| **Conformist** | Downstream conforms to upstream's model without influence | Third-party API integration |
| **Anti-Corruption Layer** | Downstream translates upstream's model to protect its own | Legacy system integration |
| **Published Language** | Shared schema/protocol (OpenAPI, Protobuf, Avro) | Public API contracts |

### Ubiquitous Language

- Each bounded context has its own vocabulary
- The same real-world concept may have different names in different contexts (User vs Customer vs Account)
- Document the mapping between contexts when the same concept appears in multiple contexts

---

## 2. Data Ownership

### Single Writer Principle

- Each piece of data has **exactly one service** that writes it
- Other services read via API, event, or read-only database view — never direct write access
- Violations indicate a missing service boundary or a shared database anti-pattern

### Read-Only Access Patterns

| Pattern | Use When | Trade-offs |
|---------|---------|-----------|
| API call | Strong consistency needed, low volume | Latency, coupling, availability dependency |
| Event subscription | Eventual consistency acceptable | Complexity, ordering, replay needed |
| Read replica / view | High read volume, low change frequency | Stale data, operational overhead |
| Cache with invalidation | Frequently read, rarely changed | Stale risk, invalidation complexity |

### Anti-Corruption Layer

When integrating with external or legacy systems:
- Never expose external models directly in your domain
- Translate at the boundary: external DTO → internal domain model
- Isolate integration code in a dedicated adapter module
- Changes to external systems affect only the adapter, not domain logic

---

## 3. Communication Patterns

### Sync vs Async Decision Matrix

| Factor | Prefer Sync (HTTP/gRPC) | Prefer Async (Events/Queues) |
|--------|------------------------|------|
| Response needed immediately | Yes | No |
| Consumer must know result | Yes | No |
| Temporal coupling acceptable | Yes | No |
| Multiple consumers | No | Yes |
| Spike tolerance needed | No | Yes |
| Order matters | N/A | Depends on guarantee |

### Sync Dependency Requirements

Every synchronous dependency must specify:
- **Timeout:** Connect timeout + read timeout (never unbounded)
- **Retry policy:** Max retries, backoff strategy, idempotency requirement
- **Circuit breaker:** Failure threshold, open duration, half-open behavior
- **Fallback:** What happens when the dependency is unavailable

### Async Delivery Guarantees

| Guarantee | Meaning | Implementation |
|-----------|---------|---------------|
| At-most-once | May lose messages | Fire-and-forget; no ack |
| At-least-once | May duplicate | Ack after processing; consumer must be idempotent |
| Exactly-once | No loss, no duplicates | Transactional outbox + idempotent consumer |

Document the chosen guarantee per event/message type in the design doc.

---

## 4. Failure Isolation

### Blast Radius Analysis

For each service dependency, document:
- **Classification:** Critical (service cannot function without it) vs Non-critical (degraded operation acceptable)
- **Failure impact:** What user-visible behavior changes when this dependency fails
- **Isolation mechanism:** How the failure is contained (circuit breaker, bulkhead, fallback)

### Bulkhead Pattern

- Isolate resources per dependency: separate thread pools, connection pools, or rate limiters
- A slow dependency should not exhaust resources needed by other dependencies
- Size bulkheads based on expected call volume and timeout settings

### Dependency Classification Template

```yaml
dependencies:
  - name: "payment-service"
    type: sync | async
    classification: critical | non-critical
    timeout_ms: 3000
    retry: {max: 3, backoff: exponential, base_ms: 100}
    circuit_breaker: {threshold: 5, open_duration_ms: 30000}
    fallback: "Queue payment for async processing"
    blast_radius: "Orders cannot be completed; items remain in cart"
```

---

## AI-Enforceable Checks

Applied during design review by tpm-quality agent.

| ID | Check | Severity | Detection |
|----|-------|----------|-----------|
| SB-01 | Every entity has a documented owning service/context | P1 | Entity referenced without ownership statement |
| SB-02 | No direct database writes from non-owning services | P0 | Service writing to another service's tables |
| SB-03 | Every sync dependency has timeout, retry, circuit breaker, and fallback specified | P0 | Sync dependency without any of these four fields |
| SB-04 | Async events have delivery guarantee documented | P1 | Event/message definition without at-most/at-least/exactly-once specification |
| SB-05 | Every dependency classified as critical or non-critical with blast radius documented | P1 | Dependency listed without classification or failure impact |
