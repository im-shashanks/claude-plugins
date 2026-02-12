# Architecture Governance Practices

Developer-facing practices for complying with architecture boundaries enforced by `architecture-checks.md` (ARC-01 through ARC-06). Read `settings.project.architecture` to determine which rules apply.

---

## Layer Dependency Rules

Each architecture style defines layers with a strict dependency direction. New files must respect these boundaries.

### Layered Architecture

```
presentation  →  service/business  →  data/repository  →  infrastructure
     ↓                  ↓                    ↓
  (controllers,    (domain logic,       (data access,
   views, DTOs)     orchestration)       persistence)
```

**Rules:**
- Presentation imports service — never the reverse
- Service imports data/repository — never the reverse
- Infrastructure is the lowest layer — imported by data layer only
- Cross-cutting concerns (logging, auth) use middleware or decorators, not direct layer imports

### Hexagonal Architecture

```
Driving Adapters  →  Ports (interfaces)  ←  Driven Adapters
         ↘              ↓                ↙
                    Domain Core
```

**Rules:**
- Domain core imports nothing external — zero framework dependencies
- Ports are interfaces defined in the domain layer
- Driving adapters (API controllers, CLI) call domain through ports
- Driven adapters (DB, external APIs) implement ports defined by domain
- Adapter → Port → Domain — never Domain → Adapter

### Clean Architecture

```
Frameworks & Drivers  →  Interface Adapters  →  Use Cases  →  Entities
     (outermost)                                              (innermost)
```

**Rules:**
- Entities are pure business objects — no framework imports
- Use cases orchestrate entities — import entities only
- Interface adapters convert between use case formats and external formats
- Frameworks & drivers are the outermost ring — all framework-specific code lives here
- Dependency rule: source code dependencies point inward only

### Feature-Based Architecture

```
feature-A/           feature-B/           shared/
  index.ts (public)    index.ts (public)    index.ts (public)
  internal/            internal/            internal/
```

**Rules:**
- Each feature exposes a public API via its root index/barrel file
- Cross-feature imports go through the public API only — never import internal files
- Shared modules are explicitly designated and imported via their public API
- No feature may import from another feature's internal directory

---

## Module Boundary Rules

A module's **public API** is what it explicitly exports from its root file:
- **Python:** names in `__init__.py` or `__all__`
- **TypeScript/JavaScript:** exports from `index.ts` / `index.js`
- **Go:** exported (capitalized) identifiers in the package
- **Rust:** `pub` items in `mod.rs` or `lib.rs`
- **Java:** public classes in the package

**Boundary discipline:**
1. Internal implementation files are private — other modules should not import them directly
2. If a consumer needs something internal, expand the public API — don't break the boundary
3. Re-exports in the index file serve as the module's contract

---

## Dependency Direction Enforcement

When creating a new file, determine its layer placement:

1. **Read `settings.project.architecture`** — identifies the architecture style
2. **Identify the target layer** — based on the file's purpose and directory location
3. **Check imports** — every import must point to the same layer or a lower layer
4. **No upward imports** — if you need something from a higher layer, restructure:
   - Extract an interface (port) in the lower layer
   - Have the higher layer implement/inject it
   - Use dependency inversion — depend on abstractions, not concretions

**Common restructuring patterns:**
- **Callback/event:** lower layer emits an event, higher layer subscribes
- **Dependency injection:** lower layer declares an interface, higher layer passes the implementation
- **Shared interface package:** both layers depend on a shared interface, neither depends on the other

---

## Feature Isolation Patterns

When features need to share functionality:

**Pattern 1 — Shared module:**
- Extract shared logic into a `shared/` or `common/` module
- Both features import from shared — neither imports from the other
- Shared module must not import from any feature

**Pattern 2 — Event-based communication:**
- Feature A emits a domain event
- Feature B subscribes to the event
- No direct import between features

**Pattern 3 — Service interface:**
- Define a service interface in the consuming feature
- Implement it in the providing feature
- Wire via dependency injection at the composition root

---

## Architecture Style → Layer Map

Quick reference for `settings.project.architecture` values:

| Architecture | Layers (top → bottom) | Domain Layer | Framework Allowed In |
|---|---|---|---|
| `layered` | presentation → service → data → infrastructure | service | presentation, infrastructure |
| `hexagonal` | adapters → ports → domain | domain | adapters only |
| `clean` | frameworks → interface-adapters → use-cases → entities | entities + use-cases | frameworks ring only |
| `mvc` | view → controller → model | model | view, controller |
| `feature-based` | features (lateral) + shared | per-feature internal | feature internals |
| `event-driven` | producers → broker → consumers | consumer handlers | producers, broker adapters |

When `architecture` is empty or unrecognized, only the always-on checks apply (ARC-02, ARC-05, ARC-06).
