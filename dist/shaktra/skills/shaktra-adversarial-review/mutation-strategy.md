# Mutation Testing Strategy

Loaded by the adversary agent for Group 1 (Mutation Probes). This file defines mutation operators, safety protocol, and finding classification.

## Mutation Operators

8 categories of code mutations, applied one at a time to changed functions:

### 1. Arithmetic
Replace arithmetic operators with alternatives:
- `+` → `-`, `-` → `+`
- `*` → `/`, `/` → `*`
- `%` → `*`, `**` → `*`

### 2. Relational
Replace comparison operators:
- `>` → `>=`, `>=` → `>`
- `<` → `<=`, `<=` → `<`
- `==` → `!=`, `!=` → `==`

### 3. Logical
Replace or remove logical operators:
- `and` → `or`, `or` → `and`
- `&&` → `||`, `||` → `&&`
- Remove `not`/`!` prefix
- Invert entire condition

### 4. Conditional
Modify control flow:
- Remove if-branch body (replace with no-op/pass)
- Remove else-branch entirely
- Flip condition (`if x` → `if not x`)
- Remove early return

### 5. Return Value
Replace return values:
- Return `null`/`None`/`nil` instead of real value
- Return `0` instead of computed number
- Return `""` instead of computed string
- Return empty collection (`[]`/`{}`) instead of populated one
- Negate boolean return (`true` → `false`)

### 6. Exception
Modify error handling:
- Remove try-catch/try-except body (let exception propagate)
- Change caught exception type to a narrower one
- Swallow error (replace handler with pass/no-op)
- Remove throw/raise statement

### 7. Boundary
Off-by-one and boundary mutations:
- `< n` → `<= n`, `<= n` → `< n`
- `0` → `1`, `1` → `0`
- `length` → `length - 1`, `length - 1` → `length`
- Array index `[0]` → `[1]`, `[-1]` → `[-2]`

### 8. Deletion
Remove statements:
- Remove a single statement (assignment, function call, method call)
- Remove a function call but keep its arguments evaluated
- Remove an assignment (variable retains previous/default value)

## Safety Protocol

This protocol is non-negotiable. Every mutation cycle must follow it exactly:

```
FOR EACH changed function:
  1. Read the file, store original content in memory
  2. FOR EACH mutation (up to max_mutations_per_function from settings):
     a. Apply ONE mutation via Edit tool
     b. Run test suite via Bash (with timeout from settings.adversarial_review.mutation_timeout)
     c. Record: KILLED (test failed) or SURVIVED (tests still pass)
     d. Restore original file content via Write tool
     e. Verify restoration (read file, confirm matches original)
  3. NEVER apply multiple mutations simultaneously
  4. NEVER proceed to next mutation until current file is verified restored
  5. If any error during mutation cycle, restore immediately and skip to next mutation
```

### Restoration Verification

After every mutation restoration:
1. Read the file back
2. Compare content to the stored original
3. If mismatch: attempt Write again with exact original content
4. If second attempt fails: STOP immediately, report the failure, do not continue

### Timeout Handling

- Read `settings.adversarial_review.mutation_timeout` (default: 30 seconds)
- Pass timeout to test command execution
- If test run times out: record as KILLED (timeout indicates the mutation caused a hang, which tests would catch)

## Mutation Selection Heuristic

When a function has more potential mutations than `max_mutations_per_function` allows, prioritize in this order:

1. **Error handling paths** — mutations in catch/except blocks, error returns, validation guards (most likely to be untested)
2. **Conditional branches** — mutations in if/else, switch/case, ternary expressions
3. **Return values** — mutations in return statements, especially computed returns
4. **Boundary conditions** — off-by-one in loops, array access, comparisons with limits

## Surviving Mutation → Finding Classification

A surviving mutation means existing tests do not detect the behavior change. Severity depends on what survived:

| Mutation Category | Survival Severity | Rationale |
|---|---|---|
| Return value mutation | P1 | Behavior unverified by tests — function could return wrong value undetected |
| Error handling mutation | P1 | Error path untested — failures may propagate silently |
| Boundary mutation | P1 | Off-by-one risk — boundary behavior unverified |
| Conditional removal | P1 | Dead code or missing branch test — entire code path may be untested |
| Security-relevant mutation (auth check, validation, sanitization) | P0 | Security gap — critical check can be removed without test failure |
| Arithmetic mutation | P2 | Calculation may be wrong but impact is context-dependent |
| Logical mutation | P1 | Logic inversion undetected — likely missing negative test case |
| Deletion mutation | P2 | Statement removal undetected — may indicate low-impact code or missing assertion |

### Security-Relevant Detection

Escalate any surviving mutation to P0 if the mutated code involves:
- Authentication or authorization checks
- Input validation or sanitization
- Cryptographic operations
- Access control decisions
- SQL/command construction
- Secret or credential handling
