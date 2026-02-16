# Implementation Plan — ST-TEST-001: User Registration

## Story

Implement a POST /users/register endpoint with input validation, password hashing, and persistence.

## Phases

### Phase 1: Data Model

- Create `User` dataclass with fields: id, email, password_hash, created_at
- File: `src/models/user.py`

### Phase 2: Repository Layer

- Implement `UserRepository` with in-memory storage
- Methods: `save(user)`, `find_by_email(email)`
- File: `src/repositories/user_repository.py`

### Phase 3: Utilities

- Implement `PasswordUtils` with bcrypt hashing
- Methods: `hash_password(password)`, `verify_password(password, hash)`
- File: `src/utils/password_utils.py`

### Phase 4: Service Layer

- Implement `UserService` with registration logic
- Validation: duplicate email check, password length >= 8
- Method: `register(email, password) -> User`
- File: `src/services/user_service.py`

### Phase 5: API Routes

- Create Flask blueprint `user_routes` with prefix `/users`
- Route: `POST /register` — parse JSON, call service, return response
- Error handling: 400 for validation, 409 for duplicate email
- File: `src/api/user_routes.py`

### Phase 6: Tests

- Unit tests for `UserService` (4 tests): happy path, duplicate email, short password, missing fields
- Integration tests for API routes (3 tests): successful registration, duplicate, invalid input
- Files: `tests/test_user_service.py`, `tests/test_user_routes.py`

## Dependencies

No external story dependencies. All components are self-contained.

## Estimated Effort

Story points: 5 | Expected tests: 7 | Target coverage: >90%
