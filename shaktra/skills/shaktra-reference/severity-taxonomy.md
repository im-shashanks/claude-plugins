# Severity Taxonomy

**Canonical source.** No other file in the Shaktra framework may define or redefine P0-P3 severity levels.

## Severity Levels

| Severity | Name | Definition | Merge Gate |
|---|---|---|---|
| **P0** | Critical | Causes data loss, security breach, or unbounded resource consumption. Must be fixed before any merge. | Blocks merge — always |
| **P1** | Major | Incorrect behavior, missing error handling, or inadequate test coverage. Allowed up to threshold. | Blocks merge if count > `settings.quality.p1_threshold` |
| **P2** | Moderate | Code quality, maintainability, or observability gaps. Does not affect correctness. | Does not block merge |
| **P3** | Minor | Style, naming, documentation. Cosmetic or subjective. | Does not block merge |

## P0 Examples by Category

**Data Loss** — Writing without fsync/flush, truncating files before confirming replacement, deleting user data without confirmation or backup.

**Security** — SQL/command injection, hardcoded credentials, missing authentication on endpoints, unvalidated redirects, exposed secrets in logs.

**Unbounded Operations** — Missing timeouts on network calls, unbounded loops over external input, uncapped queue/buffer growth, recursive calls without depth limit.

**Missing Safety** — No error handling on I/O operations, catch-all exception swallowing with no re-raise, missing null/undefined guards on external data.

**Concurrency** — Shared mutable state without synchronization, race conditions in read-modify-write sequences, deadlock-prone lock ordering.

**AI-Specific** — Hallucinated imports (modules that don't exist), placeholder logic (`// TODO: implement`), fabricated API endpoints or method signatures, mock data left in production paths.

## P1 Examples by Category

**Error Handling** — Generic catch blocks that lose context, missing retry logic on transient failures, error messages that expose internals to users.

**Testing** — Coverage below threshold for the story tier, missing edge case tests for boundary conditions, tests that pass trivially (no meaningful assertions).

**Observability** — Missing structured logging on key operations, no correlation IDs for distributed flows, silent failures with no log output.

**Behavioral** — Off-by-one errors, incorrect sort order, wrong default values, locale/timezone assumptions.

## P2-P3 Examples

**P2 (Moderate)** — Missing docstrings on public APIs, inconsistent error message formatting, duplicated logic that should be extracted.

**P3 (Minor)** — Variable naming style, import ordering, trailing whitespace, comment rewording.

## Merge Gate Logic

```
p0_count = count findings where severity == P0
p1_count = count findings where severity == P1
p1_max   = read settings.quality.p1_threshold

if p0_count > 0:
    emit QUALITY_BLOCKED
    reason: "{p0_count} P0 finding(s) must be resolved"
else if p1_count > p1_max:
    emit QUALITY_BLOCKED
    reason: "{p1_count} P1 findings exceed threshold of {p1_max}"
else:
    emit QUALITY_PASS
```

## Evidence Rule

Every behavior claim requires evidence: a test result, a log line, a command output, or a code reference. "It works" is never sufficient. "It works — see test_login_redirect (line 42) passing" is.
