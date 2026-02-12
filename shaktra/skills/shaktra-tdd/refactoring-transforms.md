# Refactoring — Transformation Catalog

20 refactoring techniques in 5 categories. Each technique specifies the mechanical steps, pre/post conditions, and AI reliability level. Used by developer in `refactor` mode during the TRANSFORM phase.

---

## Atomic Protocol

Every transformation follows this protocol:

1. **Pre-check:** Verify all tests pass before starting
2. **Apply:** Execute one transformation
3. **Post-check:** Run all tests immediately after
4. **Decide:**
   - Tests pass → transformation committed, proceed to next
   - Tests fail → revert transformation, log as `reverted`, report to user
5. **Never batch:** One transformation at a time. Never combine multiple transforms in a single step.

---

## Extraction — Breaking Large Things into Smaller Pieces

### EX-01: Extract Function

- **AI Reliability:** Very High
- **When:** Code block has a clear single purpose within a larger function
- **Steps:**
  1. Identify the code block and its inputs (variables read) and outputs (variables written)
  2. Create a new function with descriptive name (verb + noun)
  3. Parameters = variables read that are not local to the block
  4. Return value = variables written that are used after the block
  5. Replace the block with a call to the new function
  6. Run tests
- **Smells Addressed:** BL-01, CP-03, CX-01, CX-03, CX-04, DS-04

### EX-02: Extract Class

- **AI Reliability:** Very High
- **When:** Class has multiple responsibilities or groups of related fields/methods
- **Steps:**
  1. Identify the cohesive group of fields and methods to extract
  2. Create a new class with those fields and methods
  3. In the original class, create a field holding the new class instance
  4. Delegate calls from old methods to the new class
  5. Update all external callers if the new class is exposed
  6. Run tests
- **Smells Addressed:** BL-02, BL-04, CH-01, OA-03, OA-04

### EX-03: Extract Variable

- **AI Reliability:** Very High
- **When:** Complex expression used inline; extraction adds clarity
- **Steps:**
  1. Compute the expression result into a named local variable
  2. Replace the inline expression with the variable name
  3. Choose a name that explains the expression's meaning, not its computation
  4. Run tests
- **Smells Addressed:** CX-02

### EX-04: Extract Parameter Object

- **AI Reliability:** Very High
- **When:** Function has 4+ parameters that conceptually belong together
- **Steps:**
  1. Create a new class/type containing the related parameters
  2. Replace individual parameters with the new object
  3. Update all call sites to construct the object
  4. Move any behavior that operates on these parameters into the new class
  5. Run tests
- **Smells Addressed:** BL-03, BL-04

---

## Movement — Relocating Code to Where It Belongs

### MV-01: Move Method

- **AI Reliability:** High
- **When:** Method uses more features of another class than its own (Feature Envy)
- **Steps:**
  1. Copy the method to the target class
  2. Adjust references to use `self`/`this` of the new class
  3. If the old class still needs the behavior, delegate to the new location
  4. Update all callers
  5. Remove the old method (if no longer needed)
  6. Run tests
- **Smells Addressed:** CP-01, CP-02, CH-02, CH-03

### MV-02: Move Field

- **AI Reliability:** High
- **When:** Field is used more by another class than its owning class
- **Steps:**
  1. Create the field in the target class
  2. Update all read/write access to use the new location
  3. Remove the field from the original class
  4. Run tests
- **Smells Addressed:** CP-02, CH-02, CH-03

### MV-03: Inline Function

- **AI Reliability:** High
- **When:** Function body is as clear as its name; or function is called exactly once
- **Steps:**
  1. Verify the function is not polymorphic (not overridden in subclasses)
  2. Replace every call site with the function body
  3. Adjust variable names to fit the calling context
  4. Remove the function definition
  5. Run tests
- **Smells Addressed:** DS-02

### MV-04: Pull Up / Push Down

- **AI Reliability:** High
- **When:** Method belongs in parent class (shared by all subclasses) or only in specific subclass
- **Steps (Pull Up):**
  1. Verify method body is identical or can be generalized across subclasses
  2. Move method to parent class
  3. Remove from subclasses
  4. Run tests
- **Steps (Push Down):**
  1. Move method from parent to specific subclass that uses it
  2. Remove from parent
  3. Run tests
- **Smells Addressed:** OA-03

---

## Simplification — Reducing Conditional Complexity

### SI-01: Replace Conditional with Polymorphism

- **AI Reliability:** Very High
- **When:** Switch/if-else chain dispatches behavior based on type
- **Steps:**
  1. Create an interface/base class with the dispatched method
  2. Create a concrete class for each branch
  3. Move branch logic into the corresponding class's method
  4. Replace the conditional with a polymorphic call
  5. Ensure all call sites use the interface type
  6. Run tests
- **Smells Addressed:** OA-01

### SI-02: Decompose Conditional

- **AI Reliability:** Very High
- **When:** Complex boolean condition (3+ operators) or complex branch bodies
- **Steps:**
  1. Extract the condition into a descriptive predicate function
  2. Extract the "then" body into a function (if non-trivial)
  3. Extract the "else" body into a function (if non-trivial)
  4. Result: `if is_eligible_for_discount(): apply_discount() else: use_standard_price()`
  5. Run tests
- **Smells Addressed:** CX-02

### SI-03: Replace with Guard Clauses

- **AI Reliability:** Very High
- **When:** Function has deeply nested conditionals where early returns simplify flow
- **Steps:**
  1. Identify preconditions that should cause early return/throw
  2. Add guard clauses at the function's start for each precondition
  3. Remove the corresponding nested branches
  4. Flatten the remaining "happy path" logic
  5. Run tests
- **Smells Addressed:** BL-01, CX-01

### SI-04: Null Object Pattern

- **AI Reliability:** Very High
- **When:** Repeated null checks for the same type throughout the code
- **Steps:**
  1. Create a NullObject class implementing the same interface
  2. NullObject methods return neutral values (empty list, 0, no-op)
  3. Replace null returns with NullObject instances
  4. Remove null checks from callers
  5. Run tests
- **Smells Addressed:** CX-02 (when null checks create complex conditionals)

---

## Organization — Improving Data and Code Structure

### OR-01: Replace Primitive with Domain Type

- **AI Reliability:** High
- **When:** Primitive type represents a domain concept (email as string, money as float)
- **Steps:**
  1. Create a value object/class for the domain concept
  2. Add validation in the constructor (email format, money non-negative)
  3. Add domain-specific methods (email.domain(), money.add())
  4. Replace primitive usages with the new type at boundaries
  5. Update call sites
  6. Run tests
- **Smells Addressed:** OA-02

### OR-03: Remove Dead Code

- **AI Reliability:** High
- **When:** Unreferenced functions, classes, imports, or variables found
- **Steps:**
  1. Verify no reference exists (grep/search entire codebase, including tests)
  2. Verify not used via reflection/dynamic dispatch (language-specific check)
  3. Delete the dead code
  4. Run tests
- **Smells Addressed:** DS-01, DS-02, DS-03

### OR-04: Consolidate Duplicates

- **AI Reliability:** High
- **When:** Same logic exists in 2+ locations
- **Steps:**
  1. Identify all instances of the duplicated logic
  2. Extract the logic into a shared function/module
  3. Replace all instances with calls to the shared version
  4. Parameterize any differences between instances
  5. Run tests
- **Smells Addressed:** DS-04, CH-02

### OR-05: Introduce Intermediate Abstraction

- **AI Reliability:** High
- **When:** Function mixes high-level orchestration with low-level operations
- **Steps:**
  1. Identify the high-level steps (what the function does conceptually)
  2. Extract low-level details into helper functions
  3. Rewrite the original function as a sequence of high-level calls
  4. Each helper function operates at a single abstraction level
  5. Run tests
- **Smells Addressed:** CX-04

---

## Structural — Cross-Cutting Architectural Changes

### ST-04: Break Circular Dependency

- **AI Reliability:** Medium
- **When:** Modules import each other directly or transitively
- **Steps:**
  1. Map the dependency cycle (A → B → C → A)
  2. Identify the weakest link — which dependency is easiest to invert?
  3. Strategy options:
     - **Extract interface:** Create an interface in A, implement in B (dependency inversion)
     - **Extract shared module:** Move shared code to a new module both can import
     - **Event-based:** Replace direct call with event/callback
  4. Apply the chosen strategy
  5. Verify no import cycles remain
  6. Run tests
- **Smells Addressed:** CP-04

### ST-05: Enforce Layer Boundaries / Split Module

- **AI Reliability:** Medium
- **When:** Code bypasses architectural layer boundaries or module is too large
- **Steps:**
  1. Identify the boundary violation (which layers are directly coupled?)
  2. Define the correct dependency direction
  3. Introduce an interface/adapter at the boundary
  4. Route the violating access through the proper layer
  5. For module splitting: identify cohesive groups and separate into new modules
  6. Run tests
- **Smells Addressed:** CH-04, BL-02

### ST-06: Introduce Facade

- **AI Reliability:** Medium
- **When:** Client code interacts with many classes in a subsystem directly
- **Steps:**
  1. Identify the common interaction patterns with the subsystem
  2. Create a Facade class with methods for each common operation
  3. Facade methods coordinate the subsystem internally
  4. Migrate client code to use the Facade
  5. Consider making subsystem classes package-private (if language supports)
  6. Run tests
- **Smells Addressed:** CP-02, CP-03
