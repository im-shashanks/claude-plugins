# Product Requirements Document: User Authentication

## Overview

The application requires a user authentication system to manage access control.
Users must be able to register, log in, log out, and reset their passwords.

## Functional Requirements

### FR-1: User Registration
- Users can create an account with email and password
- Email must be unique across the system
- Password must be at least 8 characters with one uppercase, one number
- On success, return a confirmation message

### FR-2: User Login
- Users can log in with email and password
- On success, return a JWT access token (1-hour expiry) and refresh token (7-day expiry)
- On failure, return a generic "invalid credentials" error (no user enumeration)
- Rate limit: max 5 failed attempts per email per 15-minute window

### FR-3: User Logout
- Users can invalidate their current session
- Access token added to a deny list until expiry
- Refresh token revoked immediately

### FR-4: Password Reset
- Users can request a password reset via email
- System sends a time-limited reset link (15-minute expiry)
- Reset link is single-use
- New password must meet the same strength requirements as registration

## Non-Functional Requirements

### Security
- Passwords hashed with bcrypt (cost factor 12)
- JWT signed with RS256
- All endpoints over HTTPS
- No sensitive data in JWT payload (only user ID and role)

### Performance
- Login endpoint responds in < 200ms (p95)
- Token validation < 10ms (p95)

## Out of Scope
- OAuth/social login (future phase)
- Multi-factor authentication (future phase)
- User profile management (separate feature)

## Acceptance Criteria
- All endpoints return appropriate HTTP status codes
- Invalid inputs return 422 with field-level errors
- Authentication errors return 401
- Rate limiting returns 429 with Retry-After header
