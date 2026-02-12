---
name: shaktra-tdd
description: >
  TDD knowledge base — testing practices, coding practices, and implementation patterns.
  Loaded by SDM workflow agents (sw-engineer, test-agent, developer) for behavioral testing
  guidance and production-grade coding standards.
user-invocable: false
---

# Shaktra TDD — Testing & Coding Knowledge

This skill provides the knowledge base for writing tests and production code. It is loaded by agents during the TDD pipeline — it does not orchestrate any workflow.

## Boundary

**This skill defines:** HOW to write tests (practices, patterns, anti-patterns) and HOW to write production code (implementation patterns, security, observability, resilience).

**shaktra-quality defines:** HOW to evaluate code and tests (checks, review dimensions, gate logic).

**shaktra-reference defines:** WHAT severity levels mean (`severity-taxonomy.md`), WHAT quality principles apply (`quality-principles.md`), and WHAT the handoff state machine looks like (`schemas/handoff-schema.md`).

This skill never restates severity definitions, quality dimensions, or schema structures — it references them.

## Sub-Files

| File | Purpose |
|---|---|
| `testing-practices.md` | 12 core testing principles — behavioral testing, TDD cycle, isolation, mocking, edge cases |
| `coding-practices.md` | Implementation patterns, error handling, security, observability, resilience essentials |
| `resilience-practices.md` | Retry with backoff+jitter, timeouts by operation type, circuit breaker, fallback hierarchy, failure mode table |
| `concurrency-practices.md` | Idempotency patterns (3 types), optimistic locking, atomic operations, concurrent test harness |
| `refactoring-smells.md` | 24 code smells in 6 categories with AI-detectable patterns and transform mappings |
| `refactoring-transforms.md` | 20 refactoring techniques in 5 categories with atomic protocol and reliability ratings |
| `api-design-practices.md` | RESTful contracts, error envelopes, versioning, pagination, idempotency — 6 AI-enforceable checks (AC-01 through AC-06) |
| `schema-design-practices.md` | Schema design, indexing, migration safety, validation layers — 6 AI-enforceable checks (SD-01 through SD-06) |
| `service-boundary-practices.md` | Bounded contexts, data ownership, communication patterns, failure isolation — 5 AI-enforceable checks (SB-01 through SB-05) |
| `performance-practices.md` | Algorithmic complexity, N+1 queries, caching, connection pooling, pagination, profiling — 8 AI-enforceable checks (PG-01 through PG-08) |
| `data-layer-practices.md` | Query optimization, transaction management, batch processing, cache invalidation, data access patterns — 8 AI-enforceable checks (DL-01 through DL-08) |
| `threat-modeling-practices.md` | STRIDE framework, trust boundaries, data classification, threat model deliverable — 5 AI-enforceable checks (TM-01 through TM-05) |
| `security-practices.md` | OWASP Top 10 aligned — injection, auth, access control, crypto, SSRF, logging — 12 AI-enforceable checks (SE-01 through SE-12) |
| `architecture-governance-practices.md` | Layer dependency rules, module boundaries, dependency direction enforcement per `settings.project.architecture` |

## How Agents Use This Skill

**sw-engineer** loads this skill to inform implementation and test planning:
- Reads `testing-practices.md` for test strategy guidance
- Reads `coding-practices.md` for pattern selection during plan creation
- Reads `performance-practices.md` and `data-layer-practices.md` for data/performance-aware planning
- In `refactoring-plan` mode: reads `refactoring-smells.md` for smell detection

**test-agent** loads this skill to write behavioral tests:
- Follows `testing-practices.md` for test structure, naming, assertions
- References edge case strategy and mocking boundaries
- In `characterization` mode: writes behavior-preserving tests for refactoring safety

**developer** loads this skill to write production code:
- Follows `coding-practices.md` for implementation patterns
- Applies `security-practices.md` for OWASP-aligned secure coding
- Applies `performance-practices.md` and `data-layer-practices.md` for efficient data access
- References `resilience-practices.md` for retry, timeout, circuit breaker, and fallback patterns
- References `concurrency-practices.md` for idempotency, locking, and atomic operations
- In `refactor` mode: follows `refactoring-transforms.md` atomic protocol

**architect** loads this skill for design-first engineering:
- Reads `api-design-practices.md` for API contract design
- Reads `schema-design-practices.md` for data model design
- Reads `service-boundary-practices.md` for service decomposition
- Reads `threat-modeling-practices.md` for STRIDE-based threat modeling

## References

- `shaktra-reference/quality-principles.md` — 10 core principles guiding all code
- `shaktra-reference/severity-taxonomy.md` — severity definitions (never duplicated here)
- `shaktra-reference/schemas/handoff-schema.md` — TDD state machine phases
