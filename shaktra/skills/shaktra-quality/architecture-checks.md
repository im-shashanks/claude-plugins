# Architecture Checks — ARC-01 through ARC-06

6 checks that enforce `settings.project.architecture` boundaries during code reviews. Applied by sw-quality at every code gate and during comprehensive review.

**Activation logic:** Read `settings.project.architecture` to determine which checks are conditional. Checks marked **Always** apply regardless of architecture style. Checks marked with specific styles apply only when the project declares one of those styles.

---

## ARC-01 — Layer Violation (P1)

**Applies when:** `architecture` = `layered`, `hexagonal`, `clean`

A module in layer X imports from layer Y in the wrong direction. Dependencies must flow in one direction only — higher layers depend on lower layers, never the reverse.

**Layer direction rules by architecture style:**

| Style | Layer Order (top → bottom) | Allowed Direction |
|---|---|---|
| `layered` | presentation → service/business → data/repository → infrastructure | Top imports bottom only |
| `hexagonal` | adapters (driving/driven) → ports → domain | Outside-in only; domain imports nothing external |
| `clean` | frameworks → interface-adapters → use-cases → entities | Outer imports inner only |

**Detection guidance:**
1. Identify the project's layer boundaries from directory structure and module names
2. Map each import to source layer → target layer
3. Flag any import where the target layer is above the source layer in the hierarchy

**Evidence template:**
```
File: {file_path}:{line}
Import: {import_statement}
Violation: {source_layer} → {target_layer} (reversed — {target_layer} should not be imported by {source_layer})
```

---

## ARC-02 — Circular Dependency (P1)

**Applies when:** Always

Two or more modules/packages form a circular import chain. Circular dependencies make modules untestable in isolation and create brittle coupling.

**Detection guidance:**
1. Trace import chains: if module A imports B, and B imports A (directly or transitively), it's circular
2. Check for mutual imports between packages/directories (not just files — package-level cycles are equally harmful)
3. Common pattern: service A calls service B which calls back to service A

**Evidence template:**
```
Cycle: {module_A} → {module_B} → {module_A}
Files: {file_A}:{line_A} imports {module_B}, {file_B}:{line_B} imports {module_A}
```

---

## ARC-03 — Domain Depends on Infrastructure (P0)

**Applies when:** `architecture` = `hexagonal`, `clean`

Domain logic contains direct imports from infrastructure frameworks, ORMs, HTTP libraries, or external service clients. In hexagonal and clean architectures, the domain layer must be pure — no framework dependencies.

**Detection guidance:**
1. Identify domain layer files (entities, value objects, domain services, use cases)
2. Check their imports for framework-specific modules:
   - ORMs: SQLAlchemy, TypeORM, Prisma, GORM, ActiveRecord
   - HTTP: Flask, Express, Gin, Spring MVC
   - External clients: boto3, redis, requests (in domain layer)
3. Domain may import standard library and its own domain modules — nothing else

**Evidence template:**
```
File: {file_path}:{line}
Import: {import_statement}
Violation: Domain file imports infrastructure ({framework_name}) — domain must remain framework-free
```

---

## ARC-04 — Feature Cross-Reach (P1)

**Applies when:** `architecture` = `feature-based`

A feature module reaches into another feature's internal files instead of using its public API (exported index/barrel file).

**Detection guidance:**
1. Identify feature boundaries (typically top-level directories under `src/features/` or similar)
2. Each feature should expose a public API via an index/barrel file (`index.ts`, `__init__.py`, `mod.rs`)
3. Cross-feature imports must go through the public API, not import internal files directly
4. Internal files: anything not re-exported from the feature's root

**Evidence template:**
```
File: {file_path}:{line}
Import: {import_statement}
Violation: Feature {source_feature} imports internal file from {target_feature} — use public API ({target_feature}/index instead)
```

---

## ARC-05 — God Module (P1)

**Applies when:** Always

A single module handles more than 3 distinct responsibilities. God modules are hard to test, hard to understand, and create a merge bottleneck.

**Detection guidance:**
1. Count the distinct responsibilities in the module (each responsibility = one cohesive group of functions/classes)
2. Indicators of multiple responsibilities:
   - Module imports from 4+ unrelated domains
   - Module exports functions serving different consumers
   - Module name is generic (`utils`, `helpers`, `common`, `misc`)
   - Module has 3+ class/interface definitions serving different purposes
3. Threshold: >3 distinct responsibilities = violation

**Evidence template:**
```
File: {file_path}
Responsibilities found: {count}
1. {responsibility_1} (functions: {fn_list})
2. {responsibility_2} (functions: {fn_list})
3. {responsibility_3} (functions: {fn_list})
4. {responsibility_4} (functions: {fn_list})
Violation: Module handles {count} responsibilities — split by responsibility
```

---

## ARC-06 — Shared Mutable State Across Boundaries (P0)

**Applies when:** Always

Mutable state is shared across module boundaries without synchronization or ownership discipline. Shared mutable state is the root cause of the hardest-to-diagnose production bugs.

**Detection guidance:**
1. Look for module-level mutable variables (`let`, `var`, mutable collections) that are imported by other modules
2. Look for singleton instances with mutable fields accessed from multiple modules
3. Look for global registries, caches, or configuration objects modified at runtime by multiple consumers
4. Acceptable patterns: read-only shared state (frozen/immutable), state behind a proper synchronization mechanism, state owned by a single module with controlled access

**Evidence template:**
```
File: {file_path}:{line}
Shared state: {variable_name} (type: {type})
Accessed from: {list of importing modules}
Violation: Mutable state shared across {module_A} and {module_B} without synchronization
```

---

## Summary

| ID | Check | Severity | Conditional |
|---|---|---|---|
| ARC-01 | Layer violation | P1 | `layered`, `hexagonal`, `clean` |
| ARC-02 | Circular dependency | P1 | Always |
| ARC-03 | Domain depends on infrastructure | P0 | `hexagonal`, `clean` |
| ARC-04 | Feature cross-reach | P1 | `feature-based` |
| ARC-05 | God module | P1 | Always |
| ARC-06 | Shared mutable state across boundaries | P0 | Always |
