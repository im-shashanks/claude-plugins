# Quality & Enforcement

### Quality Tiers

Shaktra operates at two quality levels:

#### SW Quality (Story-Level)
**When:** During `/shaktra:dev` at each state transition

**What it checks:** 36 checks across 8 dimensions
- Code correctness (logic, edge cases)
- Test quality (coverage, assertions)
- Error handling patterns
- Documentation completeness
- Security (input validation, secrets)
- Observability (logging, tracing)
- Performance (no obvious bottlenecks)
- Maintainability (naming, complexity)

**Blocks progress:** P0 findings block transition to next state

#### Code Review (App-Level)
**When:** After story completion via `/shaktra:review`

**What it checks:** 13 dimensions (see Commands Reference)
- Does it work in production context?
- Is it compatible with rest of system?
- Can it be safely deployed?
- Verified by independent tests

**Blocks merge:** P0 findings block merge; P1 count can block merge if exceeds threshold

### Severity Taxonomy (P0-P3)

Every finding is categorized by severity. This taxonomy is the single source of truth.

#### P0: Critical
**Definition:** Causes data loss, security breach, or unbounded resource consumption. Must be fixed before any merge.

**Examples:**
- SQL injection in query building
- File write without fsync (data loss on crash)
- Unbounded loop over external input
- Hardcoded credentials in code
- Missing authentication on protected endpoint
- Catch-all exception swallowing without re-raise

**Merge gate:** Blocks merge — always

#### P1: Major
**Definition:** Incorrect behavior, missing error handling, or inadequate test coverage. Allowed up to threshold.

**Examples:**
- Coverage below story tier threshold
- Missing error path for operation that can fail
- Off-by-one error in business logic
- Generic exception message that loses context
- Missing null guard on external data

**Merge gate:** Blocks merge if count > `settings.quality.p1_threshold`

#### P2: Moderate
**Definition:** Code quality, maintainability, or observability gaps. Does not affect correctness.

**Examples:**
- Missing docstring on public API
- Inconsistent error message formatting
- Code duplication that should be extracted
- Magic number without named constant

**Merge gate:** Does not block merge

#### P3: Minor
**Definition:** Style, naming, documentation. Cosmetic or subjective.

**Examples:**
- Variable naming style
- Import ordering
- Trailing whitespace
- Comment wording

**Merge gate:** Does not block merge

### Design Philosophy

These principles guide Shaktra's design:

**Prompt-driven, not script-driven**
- Agents and skills are markdown prompts, not Python scripts
- Leverages Claude's native tools (Glob, Read, Grep, Bash)
- More maintainable, more interpretable

**No file over 300 lines**
- Complexity stays manageable
- Every file has single clear purpose
- Easier to understand and modify

**Single source of truth**
- Severity taxonomy defined once: `shaktra-reference/severity-taxonomy.md`
- Quality dimensions defined once: `shaktra-reference/quality-dimensions.md`
- Other files reference, never duplicate

**Hooks block or don't exist**
- No warn-only hooks
- If a constraint matters, it's enforced
- Builds trust in the framework

**Ceremony scales with complexity**
- XS stories (hotfix): Minimal ceremony, 70% coverage
- S stories: Light ceremony, 80% coverage
- M stories: Standard ceremony, 90% coverage
- L stories: Full ceremony, 95% coverage + architecture review

**Read-only diagnostics**
- `/shaktra:doctor` reports problems but never fixes them
- You stay in control of your codebase
- Framework never auto-modifies code
