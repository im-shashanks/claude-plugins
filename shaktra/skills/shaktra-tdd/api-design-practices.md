# API Design Practices

Design-first API engineering practices. Loaded by the architect agent during design doc creation and by tpm-quality during design review. Ensures API contracts are complete, consistent, and production-ready before implementation begins.

---

## 1. RESTful Contract Principles

### Resource Naming

- Resources are **nouns** (not verbs): `/users`, `/orders`, `/payments`
- Use **plural** nouns for collections: `/users` not `/user`
- Use **kebab-case** for multi-word resources: `/order-items` not `/orderItems`
- Nest for ownership: `/users/{id}/orders` — only when the child cannot exist without the parent
- Maximum nesting depth: 2 levels (`/a/{id}/b/{id}`) — deeper nesting uses query filters instead

### HTTP Semantics

| Method | Semantics | Idempotent | Safe | Response |
|--------|----------|------------|------|----------|
| GET | Read resource(s) | Yes | Yes | 200 + body |
| POST | Create resource | No | No | 201 + Location header + body |
| PUT | Replace resource entirely | Yes | No | 200 + body |
| PATCH | Partial update | No* | No | 200 + body |
| DELETE | Remove resource | Yes | No | 204 (no body) |

*PATCH is idempotent if using JSON Merge Patch (RFC 7396); not idempotent with JSON Patch (RFC 6902).

### Status Code Selection

| Scenario | Code | When |
|----------|------|------|
| Success (read) | 200 | GET, PUT, PATCH returning data |
| Created | 201 | POST creating new resource |
| Accepted | 202 | Async operation accepted, not yet complete |
| No content | 204 | DELETE, or PUT/PATCH with no response body |
| Bad request | 400 | Invalid input format, missing required fields |
| Unauthorized | 401 | No credentials or expired token |
| Forbidden | 403 | Valid credentials but insufficient permissions |
| Not found | 404 | Resource does not exist |
| Conflict | 409 | Optimistic lock failure, duplicate creation |
| Unprocessable | 422 | Valid format but business rule violation |
| Too many requests | 429 | Rate limit exceeded |
| Server error | 500 | Unhandled internal error |

---

## 2. Error Response Format

### Standard Error Envelope

Every error response follows the same structure:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Human-readable description",
    "details": [
      {
        "field": "email",
        "issue": "Invalid email format",
        "value": "not-an-email"
      }
    ],
    "request_id": "req-abc123"
  }
}
```

### Error Code Registry

- Error codes are **SCREAMING_SNAKE_CASE** strings (not HTTP status codes)
- Each API defines its error codes in the design doc
- Error codes are stable — removing a code is a breaking change
- `message` is for humans (may change); `code` is for machines (must not change)
- Never expose internal details (stack traces, SQL, file paths) in error responses

---

## 3. Versioning and Backward Compatibility

### Strategy Selection

| Strategy | Use When | Example |
|----------|---------|---------|
| URL path | Major versions, public APIs | `/v1/users`, `/v2/users` |
| Header | Minor variations, internal APIs | `Accept: application/vnd.api+json;version=2` |
| No versioning | Single consumer, rapid iteration | Direct client-server with synchronized deploys |

### Breaking Change Rules

A change is **breaking** if any existing consumer would fail:
- Removing a field from a response
- Adding a required field to a request
- Changing a field's type
- Changing error codes
- Removing an endpoint
- Changing authentication requirements

A change is **non-breaking**:
- Adding an optional field to a request
- Adding a field to a response
- Adding a new endpoint
- Adding a new error code

### Deprecation Protocol

1. Mark deprecated with `Sunset` header and response field
2. Log usage of deprecated endpoints (track remaining consumers)
3. Minimum deprecation period: defined per API in design doc
4. Remove only after zero traffic for the deprecation period

---

## 4. Pagination, Filtering, and Rate Limiting

### Pagination (Cursor-Based Preferred)

```
GET /users?cursor=abc123&limit=20

Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "def456",
    "has_more": true
  }
}
```

- Default page size: defined in settings/config (not hardcoded)
- Max page size: enforce a ceiling to prevent unbounded responses
- Cursor-based > offset-based for large datasets (avoids skip/scan cost)
- Offset-based acceptable for small, stable datasets

### Filtering

- Use query parameters for filtering: `GET /users?status=active&role=admin`
- Consistent naming: `created_after`, `created_before` (not `from_date`, `start`)
- Complex filters: consider a filter query language or POST-based search endpoint

### Rate Limiting

- Return `429 Too Many Requests` when limit exceeded
- Include `Retry-After` header (seconds until next allowed request)
- Rate limit headers on every response: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- Different limits per consumer tier if applicable

---

## 5. Request/Response Contract Specification

### Completeness Requirements

Every endpoint in the design doc must specify:
- HTTP method and path
- Request body schema (if applicable) with required/optional fields
- Response body schema with all fields typed
- All possible error responses with codes
- Authentication requirement (none, token, API key, etc.)

### Idempotency

- All mutating endpoints should document idempotency behavior
- Use `Idempotency-Key` header for non-idempotent POST endpoints
- Document what happens on duplicate requests (return existing resource, error, or no-op)

---

## AI-Enforceable Checks

Applied during design review by tpm-quality agent.

| ID | Check | Severity | Detection |
|----|-------|----------|-----------|
| AC-01 | Every endpoint has method, path, request schema, response schema, error codes, auth requirement | P1 | Missing any of these fields in endpoint definition |
| AC-02 | Error responses follow the standard envelope format | P1 | Error example without `code`, `message`, or `request_id` |
| AC-03 | Collection endpoints have pagination specified | P1 | GET endpoint returning a list without pagination fields |
| AC-04 | Removing a field, adding a required field, or changing a type without version bump | P0 | Change listed in design that matches breaking change rules |
| AC-05 | Endpoints that could be rate-limited have rate limiting specified | P2 | Public-facing endpoint without rate limit mention |
| AC-06 | Mutating endpoints document idempotency behavior | P1 | POST/PUT/PATCH/DELETE without idempotency statement |
