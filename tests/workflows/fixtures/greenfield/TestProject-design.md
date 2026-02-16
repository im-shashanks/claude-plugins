# TestProject — Design Document

## Overview

A minimal user registration service exposing a REST API. Built with Flask, using a layered architecture for clean separation of concerns.

## Architecture

```
Client → API Layer (Flask Blueprints) → Service Layer → Repository Layer → Data Store
```

### Layers

| Layer | Responsibility | Components |
|-------|---------------|------------|
| API | HTTP routing, request/response serialization | `user_routes` blueprint |
| Service | Business logic, validation | `UserService` |
| Repository | Data access abstraction | `UserRepository` |
| Utils | Cross-cutting concerns | `PasswordUtils` |
| Model | Domain entities | `User` |

## Components

### User Model

```python
class User:
    id: str           # UUID v4
    email: str        # Unique, validated
    password_hash: str # bcrypt hash
    created_at: str   # ISO 8601 timestamp
```

### UserRepository

- `save(user: User) -> User` — persist a user
- `find_by_email(email: str) -> Optional[User]` — lookup by email

Storage: in-memory dictionary keyed by email (suitable for testing).

### UserService

- `register(email: str, password: str) -> User` — validates input, hashes password, delegates to repository
- Raises `ValueError` if email already registered
- Raises `ValueError` if password shorter than 8 characters

### PasswordUtils

- `hash_password(password: str) -> str` — returns bcrypt hash
- `verify_password(password: str, hash: str) -> bool` — constant-time comparison

### user_routes Blueprint

Prefix: `/users`

## API Contract

### POST /users/register

**Request:**
```json
{
  "email": "alice@example.com",
  "password": "securepass123"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid-v4-string",
  "email": "alice@example.com",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Error (409 Conflict):**
```json
{
  "error": "Email already registered"
}
```

**Error (400 Bad Request):**
```json
{
  "error": "Password must be at least 8 characters"
}
```

## Data Model

| Field | Type | Constraints |
|-------|------|-------------|
| id | string (UUID v4) | Primary key, auto-generated |
| email | string | Unique, required, valid format |
| password_hash | string | bcrypt, never exposed in API |
| created_at | string (ISO 8601) | Auto-set on creation |

## Key Decisions

1. **bcrypt for password hashing** — industry standard, built-in salt, configurable work factor.
2. **In-memory store** — sufficient for testing; repository interface allows swapping to a real DB later.
3. **Flask blueprints** — modular route organization, easy to compose into a larger app.
4. **Service layer validation** — keeps business rules out of the API layer and testable in isolation.
5. **No authentication on register** — public endpoint by design.
