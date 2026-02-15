# Architecture Document: User Authentication Service

## Technology Stack

- **Language:** Python 3.11
- **Framework:** Flask 3.x
- **Database:** SQLite (development), PostgreSQL (production)
- **ORM:** SQLAlchemy 2.x
- **Auth:** PyJWT, bcrypt
- **Testing:** pytest, coverage

## Architecture Pattern

Layered architecture with clear separation of concerns.

## Components

### API Layer (`src/api/`)
- Flask blueprints for route definitions
- Request validation and serialization
- HTTP status code mapping
- Rate limiting middleware

### Service Layer (`src/services/`)
- `auth_service.py` — Login, logout, token refresh logic
- `user_service.py` — Registration, password reset logic
- Business rule enforcement
- No direct database access (uses repository layer)

### Repository Layer (`src/repositories/`)
- `user_repository.py` — CRUD operations for User model
- `token_repository.py` — Token deny list management
- SQLAlchemy session management

### Models (`src/models/`)
- `user.py` — User model (id, email, password_hash, created_at, updated_at)
- `token_denylist.py` — Denied token tracking (jti, expires_at)

### Utilities (`src/utils/`)
- `jwt_utils.py` — Token generation and validation
- `password_utils.py` — Hashing and verification
- `rate_limiter.py` — In-memory rate limiting

## Directory Structure

```
src/
  __init__.py
  app.py              # Flask app factory
  config.py           # Configuration management
  api/
    __init__.py
    auth_routes.py    # /auth/login, /auth/logout, /auth/refresh
    user_routes.py    # /users/register, /users/reset-password
  services/
    __init__.py
    auth_service.py
    user_service.py
  repositories/
    __init__.py
    user_repository.py
    token_repository.py
  models/
    __init__.py
    user.py
    token_denylist.py
  utils/
    __init__.py
    jwt_utils.py
    password_utils.py
    rate_limiter.py
tests/
  conftest.py
  test_auth_service.py
  test_user_service.py
  test_auth_routes.py
  test_user_routes.py
```

## Key Design Decisions

1. **JWT with deny list** over session-based auth — stateless verification with revocation capability
2. **Repository pattern** — isolates database access, enables testing with mocks
3. **SQLite for tests** — fast, no external dependencies, in-memory option
4. **bcrypt** over argon2 — widely supported, sufficient for this use case
