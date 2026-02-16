# Shaktra Commands Reference

Complete reference for all Shaktra commands. Commands are organized into **main workflow commands** that drive development and **utility commands** that support setup, diagnostics, and navigation.

---

## Main Workflow Commands

### `/shaktra:tpm` — Technical Project Manager

**Purpose:** Design documents, user story creation, sprint planning, hotfix routing

**When to use:**
- Starting a new feature or epic
- Breaking down a large request into stories
- Planning a sprint
- Creating a hotfix with minimal process

**Typical workflow:**
1. You describe what you want to build
2. TPM creates a design doc with architecture, API contracts, data models
3. TPM breaks the design into stories (XS/S/M/L) with acceptance criteria
4. TPM schedules stories into a sprint based on velocity
5. You then invoke `/shaktra:dev` on each story to implement

**Options:**
- `hotfix: <description>` — Fast-track minimal-ceremony hotfix (70% coverage)
- `epic: <description>` — Large multi-sprint feature

---

### `/shaktra:dev <story-id>` — Developer

**Purpose:** Implement a story with TDD, following the state machine

**State machine:** PLAN → RED → GREEN → QUALITY → MEMORY → COMPLETE

**When to use:**
- Implementing any user story from the backlog
- Refactoring existing code with test coverage
- Fixing a bug after diagnosis

**Typical workflow:**
1. Dev Manager reads the story from `.shaktra/stories/<story-id>.yml`
2. PLAN phase: Develop a test plan and skeleton code structure
3. RED phase: Write failing tests
4. GREEN phase: Write minimal code to pass tests
5. QUALITY phase: Run quality checks (36 checks), fix any findings
6. MEMORY phase: Document decisions and lessons learned
7. COMPLETE: Story ready for review

**Quality gates:** Each transition must pass quality checks. P0 findings block progress.

**Coverage thresholds by tier:**

| Tier | Threshold | Use case |
|------|-----------|----------|
| XS   | 70%       | Hotfixes |
| S    | 80%       | Small stories |
| M    | 90%       | Medium stories (default) |
| L    | 95%       | Large stories |

---

### `/shaktra:review <story-id|pr>` — Code Reviewer

**Purpose:** Story review and PR review with 13-dimension quality analysis

**When to use:**
- After `/shaktra:dev` completes (story review)
- Before merging a PR (PR review)
- Validating architectural decisions

**13 review dimensions:**

| # | Dimension | What it checks |
|---|-----------|---------------|
| 1 | Contract & API | Do public signatures match behavior? Is input validated? |
| 2 | Failure Modes | Does every operation that can fail have an error path? |
| 3 | Data Integrity | Are writes atomic? Is data validated before persistence? |
| 4 | Concurrency | Is shared state protected? Are operations atomic? |
| 5 | Security | Are inputs sanitized? Are secrets excluded? Is auth enforced? |
| 6 | Observability | Are operations logged? Do calls carry trace IDs? |
| 7 | Performance | Do network calls have timeouts? Are collections bounded? |
| 8 | Maintainability | Does each unit have single responsibility? Is code readable? |
| 9 | Testing | Do tests cover edge cases? Are tests independent? |
| 10 | Deployment | Is change backward-compatible? Can it be rolled back? |
| 11 | Configuration | Are values externalized? Are secrets handled securely? |
| 12 | Dependencies | Are imports real packages? Are versions pinned? |
| 13 | Compatibility | Is backward compatibility maintained? Are breaking changes documented? |

**Verification tests:** Code Reviewer runs at least 5 independent verification tests to validate behavior beyond what the story's tests check.

**P0 rules:** Any P0 finding blocks merge. Must be fixed or escalated.

---

### `/shaktra:analyze` — Codebase Analyzer

**Purpose:** Brownfield codebase assessment across 9 dimensions

**When to use:**
- On-boarding to an unfamiliar codebase
- Assessing development readiness before feature work
- Planning refactoring efforts

**9 analysis dimensions:**

| # | Dimension | What it assesses |
|---|-----------|-----------------|
| 1 | Architecture | Layering, modularity, dependency cycles |
| 2 | Testing | Coverage, test pyramid, test quality |
| 3 | Code Quality | Duplication, complexity, maintainability |
| 4 | Error Handling | Exception handling patterns, error propagation |
| 5 | Performance | Hot paths, resource leaks, N+1 queries |
| 6 | Security | Injection vulnerabilities, authentication, data protection |
| 7 | Observability | Logging, tracing, monitoring instrumentation |
| 8 | Dependencies | Outdated packages, security vulnerabilities, license compliance |
| 9 | Documentation | API docs, architecture docs, runbook completeness |

**Output:** Detailed findings organized by dimension with evidence, severity, and remediation guidance.

---

### `/shaktra:bugfix <bug-description>` — Bug Diagnostician

**Purpose:** 5-step bug diagnosis followed by TDD remediation

**When to use:**
- Investigating a reported bug
- Triaging a production issue
- Understanding root cause before fixing

**5-step diagnosis:**

| Step | Name | What happens |
|------|------|-------------|
| 1 | Triage | Is this a real bug? Reproducible? Security-related? |
| 2 | Reproduce | Create minimal test case demonstrating the bug |
| 3 | Root Cause | Trace the code path, identify what's wrong |
| 4 | Blast Radius | What else could this bug affect? |
| 5 | Create Story | Write a user story with test case for TDD remediation |

**Remediation:** After diagnosis, creates a story for `/shaktra:dev` to fix via TDD.

---

### `/shaktra:general` — Domain Expert

**Purpose:** Domain expertise, architectural guidance, technical questions

**When to use:**
- Architectural questions (patterns, tradeoffs)
- Domain expertise on unfamiliar technology
- Technical design review
- "How do we..." questions

**Capabilities:**
- Design pattern suggestions
- Technology tradeoff analysis
- Best practices for your language/framework
- Architectural alternatives evaluation

---

## Utility Commands

### `/shaktra:init` — Initialize Project

**Purpose:** Creates the `.shaktra/` directory with default configuration, templates, and project structure.

**Interactive setup:**
- Project type: greenfield or brownfield
- Language and framework
- Test framework and coverage tool
- Architecture style (layered, hexagonal, clean, mvc, etc.)
- Package manager

**Creates:**

| Path | Purpose |
|------|---------|
| `.shaktra/settings.yml` | Project configuration |
| `.shaktra/sprints.yml` | Sprint tracking |
| `.shaktra/memory/` | Decision and lesson log |
| `.shaktra/stories/` | User story storage |
| `.shaktra/designs/` | Design document storage |
| `.shaktra/templates/` | Artifact templates |

---

### `/shaktra:doctor` — Health Check

**Purpose:** Diagnoses framework health and configuration issues.

**Checks:**
- Plugin structure (all required files present)
- `.shaktra/` configuration valid YAML
- `settings.yml` has all required keys
- Hook scripts executable and valid Python
- Agent and skill count matches expectations
- No design constraint violations (no >300-line files, etc.)
- All P0 findings resolved

**Output:** Pass/fail for each check with remediation guidance for failures.

**Read-only:** Doctor reports problems but never fixes them. You stay in control.

---

### `/shaktra:workflow` — Smart Router

**Purpose:** Natural language router that automatically dispatches you to the right agent.

**When to use:**
- When you're not sure which command to use
- Complex requests that might span multiple agents
- You prefer natural language over command names

**Example:**
```
"We need to refactor the authentication module but we're worried about breaking things"
```
Routes to `/shaktra:analyze` (assessment) + `/shaktra:dev` (refactoring with TDD)

---

### `/shaktra:help` — Help & Documentation

**Purpose:** Shows all commands, workflows, and detailed usage guide.

**Available anytime for reference within Claude Code.**
