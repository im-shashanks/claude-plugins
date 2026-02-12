# Refactoring — Code Smell Catalog

24 code smells in 6 categories. Each smell has an AI-detectable pattern for automated assessment. Used by sw-engineer in `refactoring-plan` mode during the ASSESS phase.

---

## Bloaters — Code That Has Grown Too Large

### BL-01: Long Function

- **Signal:** Function body exceeds 30 lines (excluding comments/blank lines)
- **Detection:** Count non-blank, non-comment lines per function
- **Risk:** Hard to understand, test, and modify
- **Transform:** EX-01 (Extract Function), SI-03 (Guard Clauses)

### BL-02: Large Class

- **Signal:** Class body exceeds 200 lines or has more than 10 public methods
- **Detection:** Count lines per class; count public methods
- **Risk:** Multiple responsibilities, high coupling
- **Transform:** EX-02 (Extract Class), ST-05 (Split Module)

### BL-03: Long Parameter List

- **Signal:** Function accepts more than 4 parameters
- **Detection:** Count function parameters
- **Risk:** Hard to call correctly, indicates missing abstraction
- **Transform:** EX-04 (Extract Parameter Object)

### BL-04: Data Clumps

- **Signal:** Same group of 3+ fields appears together in multiple places
- **Detection:** Find repeated field groups across classes/functions
- **Risk:** Missing domain concept; changes require multi-site updates
- **Transform:** EX-02 (Extract Class), OR-01 (Replace Primitive with Domain Type)

---

## Couplers — Excessive Interdependency

### CP-01: Feature Envy

- **Signal:** Method accesses more fields/methods of another class than its own
- **Detection:** Count external vs internal references per method
- **Risk:** Logic in wrong location; changes to data require changes to unrelated class
- **Transform:** MV-01 (Move Method)

### CP-02: Inappropriate Intimacy

- **Signal:** Class directly accesses private/internal fields of another class
- **Detection:** Grep for direct field access across class boundaries
- **Risk:** Tight coupling; breaking internal changes cascade
- **Transform:** MV-01 (Move Method), MV-02 (Move Field), ST-06 (Introduce Facade)

### CP-03: Message Chains

- **Signal:** Chain of 3+ method calls (a.b().c().d())
- **Detection:** Grep for chained dot-notation calls
- **Risk:** Fragile — any intermediate change breaks the chain
- **Transform:** MV-01 (Move Method), EX-01 (Extract Function)

### CP-04: Circular Dependencies

- **Signal:** Module A imports B and B imports A (directly or transitively)
- **Detection:** Build import graph; detect cycles
- **Risk:** Untestable in isolation; deployment ordering problems
- **Transform:** ST-04 (Break Circular Dependency)

---

## Dispensables — Code That Shouldn't Exist

### DS-01: Dead Code

- **Signal:** Functions, classes, imports, or variables never referenced
- **Detection:** Cross-reference all definitions against all usages
- **Risk:** Confusing; maintenance burden; false sense of coverage
- **Transform:** OR-03 (Remove Dead Code)

### DS-02: Speculative Generality

- **Signal:** Abstract class with only one implementation; unused parameters; unused configuration options
- **Detection:** Count implementations per interface; find unused parameters
- **Risk:** Complexity without value; YAGNI violation
- **Transform:** MV-03 (Inline Function), OR-03 (Remove Dead Code)

### DS-03: Commented-Out Code

- **Signal:** Code blocks in comments (not documentation comments)
- **Detection:** Grep for commented code patterns (language-specific)
- **Risk:** Confusing; version control makes this unnecessary
- **Transform:** OR-03 (Remove Dead Code)

### DS-04: Duplicate Code

- **Signal:** Identical or near-identical code blocks (>5 lines) in 2+ locations
- **Detection:** Token-based or AST-based similarity analysis; simpler: grep for identical multi-line blocks
- **Risk:** Bug fixed in one copy but not others; inconsistent evolution
- **Transform:** EX-01 (Extract Function), OR-04 (Consolidate Duplicates)

---

## OO Abusers — Misuse of Object-Oriented Mechanisms

### OA-01: Switch/Type-Check Chains

- **Signal:** Switch/if-else chain on type field or instanceof (3+ branches)
- **Detection:** Grep for switch + type patterns; long if/elif on same variable
- **Risk:** Every new type requires changes in multiple places
- **Transform:** SI-01 (Replace Conditional with Polymorphism)

### OA-02: Primitive Obsession

- **Signal:** Using strings/ints for domain concepts (email as string, money as float)
- **Detection:** Find domain terms used as primitive types across boundaries
- **Risk:** No validation at construction; no domain-specific behavior
- **Transform:** OR-01 (Replace Primitive with Domain Type)

### OA-03: Refused Bequest

- **Signal:** Subclass overrides parent method to throw or no-op; subclass uses <50% of inherited interface
- **Detection:** Find empty/throwing overrides; count used vs total inherited methods
- **Risk:** Liskov Substitution Principle violation; incorrect abstraction hierarchy
- **Transform:** MV-04 (Push Down), EX-02 (Extract Class)

### OA-04: God Object

- **Signal:** Class that coordinates many other classes; high fan-out (>10 dependencies)
- **Detection:** Count import/dependency count per class; measure fan-out
- **Risk:** Single point of failure; impossible to test in isolation
- **Transform:** EX-02 (Extract Class), MV-01 (Move Method)

---

## Change Preventers — Code That Resists Modification

### CH-01: Divergent Change

- **Signal:** One class changes for multiple unrelated reasons
- **Detection:** Analyze git history — same file touched in commits with different scopes/concerns
- **Risk:** SRP violation; changes for one concern risk breaking another
- **Transform:** EX-02 (Extract Class), ST-05 (Split Module)

### CH-02: Shotgun Surgery

- **Signal:** One logical change requires edits in 5+ files
- **Detection:** Analyze git history — multiple files always change together
- **Risk:** Easy to miss a site; high error rate for changes
- **Transform:** MV-01 (Move Method), MV-02 (Move Field), OR-04 (Consolidate Duplicates)

### CH-03: Parallel Inheritance

- **Signal:** Adding a subclass in one hierarchy requires adding one in another
- **Detection:** Find parallel class hierarchies with matching names/prefixes
- **Risk:** Coupled hierarchies; double the change cost
- **Transform:** MV-01 (Move Method), MV-02 (Move Field)

### CH-04: Layer Violations

- **Signal:** Direct access across architectural layers (e.g., controller calling DB directly)
- **Detection:** Cross-reference imports against declared layer boundaries
- **Risk:** Bypasses validation/transformation; tight coupling across boundaries
- **Transform:** ST-05 (Enforce Layer Boundaries)

---

## Complexity — Unnecessarily Hard to Understand

### CX-01: Deep Nesting

- **Signal:** Code indented 4+ levels deep
- **Detection:** Count indentation depth per statement
- **Risk:** Cognitive overload; hard to trace execution path
- **Transform:** EX-01 (Extract Function), SI-03 (Guard Clauses)

### CX-02: Complex Conditionals

- **Signal:** Boolean expression with 3+ operators or nested ternaries
- **Detection:** Count boolean operators per expression; find nested ternaries
- **Risk:** Hard to reason about all paths; error-prone modifications
- **Transform:** SI-02 (Decompose Conditional), EX-03 (Extract Variable)

### CX-03: Mutable Accumulators

- **Signal:** Variable reassigned in a loop with complex accumulation logic
- **Detection:** Find loop variables modified inside loop body with conditional logic
- **Risk:** Hard to verify correctness; off-by-one errors; unclear intent
- **Transform:** EX-01 (Extract Function), functional alternatives (map/filter/reduce)

### CX-04: Mixed Abstraction Levels

- **Signal:** Function mixes high-level orchestration with low-level detail
- **Detection:** Identify functions that both coordinate workflow AND manipulate data structures
- **Risk:** Obscures intent; hard to test high-level logic without low-level setup
- **Transform:** EX-01 (Extract Function), OR-05 (Introduce Intermediate Abstraction)
