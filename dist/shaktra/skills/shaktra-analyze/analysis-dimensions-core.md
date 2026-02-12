# Analysis Dimensions — Core (D1-D4)

Dimensions that answer "What IS this codebase?" — its structure, domain model, interfaces, and coding style.

**Used by:** shaktra-cba-analyzer agent during `/shaktra:analyze` workflow.
**Input dependency:** All dimensions consume `static.yml` (ground truth) and `overview.yml` (project context).
**Companion:** `analysis-dimensions-health.md` defines D5-D8.

---

## D1: Architecture & Structure → `structure.yml`

**Scope:** How the codebase is organized, what each module does, and how modules relate.

**What to analyze:**
1. **Module inventory** — every top-level directory and significant sub-module. For each: name, purpose (why it exists), responsibilities, public interface, key files.
2. **Module relationships** — which modules depend on which (from `static.yml` dependency graph). Identify intended boundaries and violations.
3. **Architectural patterns** — layering (MVC, hexagonal, clean), domain separation, dependency direction. Detect if patterns are consistent or mixed.
4. **Boundary violations** — cases where module A reaches into module B's internals, circular dependencies, layers skipping levels.
5. **Convention violations** — identify the codebase's own architectural conventions (import patterns, module boundaries, layering direction), then catalog instances that deviate. Dominant pattern identified first, then deviating instance cited.

**Evidence requirements:**
- Module purposes derived from directory names, README files, docstrings, and code content — not guessed
- Dependency relationships verified against `static.yml` dependency graph
- Boundary violations cite specific import paths
- Convention violations: dominant pattern identified first, then deviating instance cited with file:line

**Output structure:**
```yaml
summary: |
  {Self-contained 400-token overview: module count, architectural style,
   key boundary violations, overall structural health}
details:
  modules:
    - name: string
      path: string
      why_exists: string
      responsibilities: [string]
      public_interface: [string]
      key_files: [string]
  relationships:
    - from: string
      to: string
      type: imports | calls | extends
      direction: expected | violation
  patterns:
    detected: [string]
    consistency: high | mixed | low
    notes: string
  boundary_violations:
    - from_module: string
      to_module: string
      via: string  # specific import path
      severity: string
  diagrams:
    architecture: |
      {Mermaid diagram of module relationships}
  convention_violations:
    - module: string
      violation: string
      expected_pattern: string
      location: string
      severity: minor | moderate | significant
```

---

## D2: Domain Model & Business Rules → `domain-model.yml`

**Scope:** The business logic encoded in the codebase — entities, rules, state machines, invariants, and critically: edge cases and lessons learned discovered from code.

**What to analyze:**
1. **Entities & value objects** — core domain types, their attributes, relationships. Distinguish entities (identity-based) from value objects (attribute-based).
2. **State machines** — any entity with lifecycle states (order: pending→confirmed→shipped→delivered). Document transitions, guards, and side effects.
3. **Business invariants** — rules that must always hold (e.g., order total = sum of line items, user email is unique). Where enforced (DB, app layer, both).
4. **Business rules** — conditional logic encoding domain knowledge (e.g., "free shipping over $50", "3 failed logins = account lock").
5. **Edge cases & lessons learned** — non-obvious behaviors discovered from: code comments (TODO, HACK, FIXME, WORKAROUND), test edge cases, error handling special cases, git history patterns (files with many bug-fix commits).
6. **Error propagation** — trace error flow from origin through handler chains. For each significant error type: where it's thrown/created, how it propagates through the call chain, where it's finally caught/handled, and whether it's swallowed or reaches the user.

**Evidence requirements:**
- Entities traced to actual class/type definitions
- State machines traced to actual code (enum, state field, transition methods)
- Edge cases cite the specific comment, test, or code pattern
- Error propagation traced through actual throw/catch/return chains in code

**Output structure:**
```yaml
summary: |
  {Self-contained 500-token overview: entity count, state machines found,
   critical invariants, notable edge cases}
details:
  entities:
    - name: string
      type: entity | value_object
      file: string
      attributes: [string]
      relationships: [{target: string, type: string}]
  state_machines:
    - entity: string
      states: [string]
      transitions:
        - from: string
          to: string
          trigger: string
          guard: string
          side_effects: [string]
  invariants:
    - rule: string
      enforced_at: [string]  # DB constraint, app validation, both
      evidence: string
  business_rules:
    - rule: string
      location: string
      conditions: string
  edge_cases:
    - description: string
      source: comment | test | error_handling | git_history
      location: string
      lesson: string
  error_propagation:
    - error_origin: string
      propagation_path: [string]
      terminal_handler: string
      transforms: [string]
      swallowed: boolean
      user_visible: boolean
```

---

## D3: Entry Points & Interfaces → `entry-points.yml`

**Scope:** All ways external actors interact with the system — not just HTTP APIs but event handlers, CLI commands, scheduled jobs, webhooks, message consumers, and WebSocket endpoints.

**What to analyze:**
1. **HTTP/REST endpoints** — routes, methods, request/response shapes, auth requirements
2. **Event handlers** — message queue consumers, event bus listeners, pub/sub subscribers
3. **CLI commands** — command-line interfaces, management commands, admin scripts
4. **Scheduled jobs** — cron jobs, periodic tasks, background workers
5. **Webhooks** — incoming webhook handlers, callback endpoints
6. **WebSocket/streaming** — real-time endpoints, SSE handlers
7. **Internal interfaces** — shared libraries, SDK surfaces, plugin APIs

For each entry point: document the handler, its dependencies, and the data contract (input/output).

**Evidence requirements:**
- Every entry point traced to a specific file and handler function
- Auth requirements verified against middleware/decorator presence
- Data contracts derived from actual type definitions or validation code

**Output structure:**
```yaml
summary: |
  {Self-contained 400-token overview: endpoint count by type,
   auth coverage, notable gaps}
details:
  http:
    - path: string
      method: string
      handler: string  # file:function
      auth: string | none
      request_shape: string
      response_shape: string
  events:
    - event: string
      handler: string
      source: string
  cli:
    - command: string
      handler: string
      description: string
  jobs:
    - name: string
      schedule: string
      handler: string
  webhooks:
    - path: string
      handler: string
      source: string
  websockets:
    - path: string
      handler: string
  internal_interfaces:
    - name: string
      surface: [string]
      consumers: [string]
```

---

## D4: Coding Practices & Conventions → `practices.yml`

**Scope:** How code is written in this project — the 14 practice areas, naming conventions, and canonical examples per detected pattern. This is what developer and sw-engineer agents need to generate code that matches the existing codebase.

**14 Practice Areas to Analyze:**

| # | Area | What to Detect |
|---|---|---|
| 1 | Type annotations | Usage level (full/partial/none), style (inline, stubs, generics) |
| 2 | Docstrings/comments | Style (Google, NumPy, JSDoc), coverage, quality |
| 3 | Import organization | Grouping, ordering, aliasing conventions |
| 4 | Dependency injection | Pattern used (constructor, parameter, container, none) |
| 5 | API patterns | REST conventions, response envelope, pagination style |
| 6 | Testing patterns | Naming, fixtures, mocking approach, assertion style |
| 7 | Database patterns | ORM vs raw SQL, migration tooling, transaction handling |
| 8 | Error handling | Strategy (exceptions, result types, error codes), custom error types |
| 9 | Logging | Framework, structured vs unstructured, log levels, correlation |
| 10 | Configuration | Source (env, files, services), validation, hierarchy |
| 11 | Authentication | Strategy (JWT, session, OAuth), middleware pattern |
| 12 | Async patterns | Concurrency model (async/await, threads, actors), patterns used |
| 13 | File organization | Grouping (by feature, by type, by layer), naming conventions |
| 14 | Code structure | Function length norms, class size norms, module boundaries |

**Naming conventions to detect:**
- File naming (snake_case, camelCase, kebab-case, PascalCase)
- Function/method naming convention
- Class naming convention
- Variable naming convention
- Test file naming (test_*.py, *.test.ts, *_test.go)
- Test function naming (test_*, it('should...'), Test*)

**Canonical examples:** For each detected pattern, extract a 10-40 line code snippet from the actual codebase showing exactly how to implement that pattern in THIS project. These examples teach the developer agent "how we do things here."

**Violation catalog:** For each detected pattern, catalog instances that deviate from the established convention. Cite the canonical pattern first, then the deviating file:line. This turns practices from a style guide into a bug-finding tool.

**Evidence requirements:**
- Practice detection based on actual code samples, not filenames
- Canonical examples are real code from the codebase, not generated
- Naming conventions verified across minimum 5 files
- Violation catalog entries: cite canonical pattern + deviating file:line

**Output structure:**
```yaml
summary: |
  {Self-contained 600-token overview: dominant practices,
   naming conventions, notable deviations, consistency level}
details:
  practices:
    - area: string  # one of the 14 areas
      detected_pattern: string
      consistency: high | mixed | low
      evidence: [string]  # file:line references
      canonical_example:
        description: string
        file: string
        lines: string  # "42-67"
        snippet: |
          {10-40 lines of actual code}
  naming_conventions:
    files: string
    functions: string
    classes: string
    variables: string
    tests_files: string
    tests_functions: string
    evidence: [string]
  deviations:
    - area: string
      description: string
      location: string
  violation_catalog:
    - area: string
      canonical_pattern: string
      violation: string
      location: string
      impact: low | medium | high
```
