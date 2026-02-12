# Schema Design Practices

Design-first database and data schema practices. Loaded by the architect agent during design doc creation and by tpm-quality during design review. Ensures data models are sound, indexed, and safely migratable before implementation begins.

---

## 1. Schema Design Principles

### Normalization Default

- Start at **3NF** (Third Normal Form) — every non-key field depends on the key, the whole key, and nothing but the key
- Denormalize intentionally with justification: read-heavy query, caching layer, materialized view
- Document every denormalization: what was denormalized, why, and how consistency is maintained

### Primary Key Strategy

| Strategy | Use When | Trade-offs |
|----------|---------|-----------|
| Auto-increment integer | Single-database, simple CRUD | Simple; exposes ordering; fragile for distributed |
| UUID v4 | Distributed systems, external exposure | No ordering; larger index; globally unique |
| UUID v7 | Distributed + time-ordering | Time-sorted; globally unique; larger than integer |
| Natural key | Stable, immutable business identifier exists | Domain-meaningful; can't change; composite risk |

Choose one PK strategy per project and apply consistently. Document the choice in design doc Section 3.

### Standard Fields

Every table should include:
- `created_at: timestamp` — immutable, set on insert
- `updated_at: timestamp` — updated on every modification
- Consider `deleted_at: timestamp` for soft-delete (see Temporal Data section)

### Soft Delete

- Default: soft delete (`deleted_at` timestamp, nullable)
- Hard delete only when: regulatory requirement (GDPR right to erasure), storage constraints, or no audit need
- All queries must filter `WHERE deleted_at IS NULL` by default (enforce via default scope/query builder)

---

## 2. Indexing Strategy

### Mandatory Indexes

- **Foreign keys:** Every FK column must be indexed (prevents full table scans on joins/deletes)
- **WHERE clause columns:** Fields used in frequent WHERE conditions
- **ORDER BY columns:** Fields used in sorting (combined with WHERE for composite indexes)
- **JOIN columns:** Fields used in JOIN conditions beyond FKs

### Composite Index Rules

- **Order matters:** Most selective column first, or leftmost prefix match for range queries
- **Covering indexes:** Include all SELECT columns in the index to avoid table lookups (for hot queries)
- **Don't over-index:** Each index slows writes; aim for the minimum set that covers critical queries

### Cardinality Awareness

- High cardinality columns (user_id, email) benefit most from indexing
- Low cardinality columns (status, type with few values) are poor index candidates alone
- Combine low cardinality with high cardinality in composite indexes: `(status, created_at)`

---

## 3. Migration Safety

### Safe vs Unsafe Operations

| Safe (Online) | Unsafe (Locking) |
|------|------|
| Add nullable column | Add NOT NULL column without default |
| Add index CONCURRENTLY | Add index (blocks writes) |
| Add table | Drop table |
| Add column with default (Postgres 11+) | Rename column |
| Create view | Change column type |

### Two-Phase Pattern for Unsafe Operations

When an unsafe operation is required:

**Phase 1 (deploy first):** Add new column/table alongside old. Write to both. Read from old.

**Phase 2 (deploy second):** Migrate data. Switch reads to new. Stop writing to old.

**Phase 3 (cleanup):** Remove old column/table after verification period.

### Migration Requirements

- Every migration must have a **rollback** — `up` and `down` scripts
- Rollback must be tested (not just written)
- Large data migrations use **batched processing** (not single UPDATE of millions of rows)
- Migrations must be idempotent — running twice produces the same result

---

## 4. Temporal Data and Audit

### Audit Trails

For tables with business significance:
- Record who changed what, when, and why
- Options: audit table (separate), event sourcing, CDC (Change Data Capture)
- Minimum: `created_by`, `updated_by` fields referencing the acting user/service

### Temporal Queries

- Use `created_at` and `updated_at` for basic temporal queries
- For point-in-time queries: consider temporal tables or event sourcing
- For range queries: ensure `(created_at)` is indexed; use cursor-based pagination over time ranges

---

## 5. Validation Layers

### Three-Layer Validation

| Layer | What | How | Example |
|-------|------|-----|---------|
| **API boundary** | Format, type, presence | Schema validation (JSON Schema, Zod, Pydantic) | Email format, required fields, string length |
| **Application** | Business rules, cross-field | Domain logic, service layer | Balance >= 0, start_date < end_date |
| **Database** | Constraints, referential integrity | DDL constraints | NOT NULL, UNIQUE, FK, CHECK |

All three layers are required. Do not rely on database constraints alone (poor error messages) or API validation alone (bypassed by direct DB access).

---

## AI-Enforceable Checks

Applied during design review by tpm-quality agent.

| ID | Check | Severity | Detection |
|----|-------|----------|-----------|
| SD-01 | PK strategy specified and consistent across all tables | P1 | Tables without PK strategy or mixed strategies without justification |
| SD-02 | FK columns have indexes | P1 | FK reference without corresponding index definition |
| SD-03 | Unsafe migration operation without two-phase pattern | P0 | Rename column, change type, or add NOT NULL without default in single migration |
| SD-04 | All three validation layers specified (API, application, database) | P1 | Schema design mentioning validation at fewer than 3 layers |
| SD-05 | Denormalization without documented justification and consistency strategy | P2 | Denormalized field without explaining why and how consistency is maintained |
| SD-06 | Migration without rollback script | P1 | Migration mentioned without corresponding rollback procedure |
