# Security Practices

Deep security engineering practices aligned with OWASP Top 10. Loaded by developer during implementation and by sw-quality during code review. Deepens the existing 6 security essentials in `coding-practices.md` into comprehensive, AI-enforceable patterns.

---

## A03: Injection

### SQL Injection

- **Rule:** Never interpolate user input into SQL strings
- **Pattern:** Use parameterized queries / prepared statements exclusively
- **Bad:** `db.query(f"SELECT * FROM users WHERE email = '{email}'")`
- **Good:** `db.query("SELECT * FROM users WHERE email = ?", [email])`

### ORM Injection

- **Rule:** Never pass raw user input to ORM `where` clauses as strings
- **Pattern:** Use ORM query builder methods with typed parameters
- **Bad:** `User.where(f"name = '{name}'")`
- **Good:** `User.where(name=name)` or `User.where("name = ?", name)`

### NoSQL Injection

- **Rule:** Sanitize query operators in user input for document databases
- **Pattern:** Reject or strip `$`-prefixed keys from user-provided objects
- **Bad:** `db.find({"email": user_input})` — user sends `{"$gt": ""}` to match all
- **Good:** Validate that `user_input` is a string, not an object/dict

### Template Injection (SSTI)

- **Rule:** Never render user input as template code
- **Pattern:** Use auto-escaping templates; treat user input as data, not code
- **Bad:** `render_template_string(user_input)`
- **Good:** `render_template("page.html", content=user_input)`

### Command Injection

- **Rule:** Never pass user input to shell commands via string concatenation
- **Pattern:** Use subprocess with argument lists (not shell=True)
- **Bad:** `os.system(f"convert {filename}")`
- **Good:** `subprocess.run(["convert", filename], shell=False)`

### Argument Injection

- **Rule:** Validate that user input cannot be interpreted as command flags
- **Pattern:** Use `--` to separate options from arguments; validate input format
- **Bad:** `subprocess.run(["git", "checkout", branch_name])` — user sends `-f main`
- **Good:** Validate `branch_name` matches `^[a-zA-Z0-9_/-]+$`

### Path Traversal

- **Rule:** Never use unsanitized user input in file paths
- **Pattern:** Resolve to absolute path and verify it stays within allowed directory
- **Bad:** `open(f"uploads/{user_filename}")`
- **Good:** `path = os.path.realpath(os.path.join("uploads", user_filename)); assert path.startswith(UPLOAD_DIR)`

---

## A07: Broken Authentication

### Password Storage

- **Rule:** Hash passwords with bcrypt, scrypt, or argon2 — never MD5, SHA-1, or SHA-256 alone
- **Pattern:** Use language-standard password hashing library with default cost factor
- **Cost factor:** bcrypt ≥ 12, argon2id with memory ≥ 64MB

### Account Lockout

- **Rule:** Rate-limit failed login attempts per account and per IP
- **Pattern:** Lock account after N failures (configurable); unlock after timeout or admin action
- **Never:** Lock permanently without admin unlock path

### Session Management

- **Rule:** Sessions expire after configurable inactivity timeout
- **Pattern:** Regenerate session ID after authentication state change (login, privilege change)
- **Invalidation:** Provide server-side session invalidation (logout must destroy server session, not just client cookie)

---

## A01: Broken Access Control

### IDOR (Insecure Direct Object Reference)

- **Rule:** Every data access must verify the requesting user owns or is authorized to access the resource
- **Pattern:** `get_resource(id, user_id)` — always filter by owner, not just by resource ID
- **Bad:** `db.get(Resource, id=request.params.id)`
- **Good:** `db.get(Resource, id=request.params.id, owner_id=current_user.id)`

### Vertical Privilege Escalation

- **Rule:** Check role/permission on every protected endpoint — not just in middleware for some routes
- **Pattern:** Default-deny — every endpoint requires explicit permission grant
- **Never:** Rely on UI hiding to prevent unauthorized access

### Default-Deny

- **Rule:** All resources are denied by default; access is explicitly granted
- **Pattern:** Whitelist authorized roles/permissions per endpoint, not blacklist unauthorized ones

---

## A05: Security Misconfiguration

### Debug Mode

- **Rule:** Debug mode, verbose errors, and development tools must never be active in production
- **Pattern:** Environment-based configuration with production as the safe default
- **Check:** Grep for `DEBUG=True`, `debug: true`, development-only middleware in production config

### Default Credentials

- **Rule:** No default passwords, API keys, or tokens in code or configuration
- **Pattern:** Require explicit configuration; fail to start if security-critical config is missing

### Security Headers

Required headers for web applications:
- `Strict-Transport-Security` (HSTS)
- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` (or CSP frame-ancestors)
- `Referrer-Policy: strict-origin-when-cross-origin`

### CORS

- **Rule:** Never use `Access-Control-Allow-Origin: *` for authenticated endpoints
- **Pattern:** Whitelist allowed origins; validate against the list

---

## A02: Cryptographic Failures

### Weak Algorithms

| Purpose | Acceptable | Unacceptable |
|---------|-----------|--------------|
| Password hashing | bcrypt, scrypt, argon2id | MD5, SHA-1, SHA-256 (without salt/iteration) |
| Symmetric encryption | AES-256-GCM | DES, 3DES, AES-ECB |
| Asymmetric encryption | RSA-2048+, Ed25519 | RSA-1024, DSA |
| Hashing (non-password) | SHA-256, SHA-3 | MD5, SHA-1 |

### Key Management

- **Rule:** Never hardcode encryption keys, API keys, or secrets in source code
- **Pattern:** Environment variables, secret manager (Vault, AWS Secrets Manager), or encrypted config
- **Rotation:** Document key rotation procedure; design for rotation without downtime

### Random Number Generation

- **Rule:** Use cryptographically secure random for tokens, keys, session IDs, and nonces
- **Bad:** `math.random()`, `random.randint()`, `Math.random()`
- **Good:** `secrets.token_urlsafe()`, `crypto.randomBytes()`, `SecureRandom`

---

## A06: Vulnerable Components

- Pin dependency versions (lock files: `package-lock.json`, `Pipfile.lock`, `go.sum`)
- Minimize dependencies — each dependency is an attack surface
- Check for known CVEs before adding new dependencies
- Update strategy: automated vulnerability scanning (Dependabot, Snyk, pip-audit)

---

## A09: Logging Failures

### What to Log

- Authentication attempts (success and failure) with actor identity
- Authorization failures with actor and requested resource
- Input validation failures with sanitized input
- State changes to critical data (create, update, delete)
- System errors and exceptions

### What NOT to Log

- Passwords (even hashed)
- Session tokens, API keys, or bearer tokens
- Credit card numbers or full SSNs
- PII beyond what's necessary for the log's purpose
- Encryption keys or secrets

---

## A10: SSRF (Server-Side Request Forgery)

- **Rule:** Never allow user-controlled URLs to be fetched by the server without validation
- **Pattern:** Allowlist of permitted domains/IPs; block private IP ranges (10.x, 172.16-31.x, 192.168.x, 127.x, ::1)
- **DNS rebinding:** Resolve the hostname, then validate the IP, then connect — don't resolve twice
- **Protocol restriction:** Only allow `https://` (never `file://`, `gopher://`, `dict://`)

---

## AI-Enforceable Checks

Applied during code review by sw-quality agent. Full detection details in `shaktra-quality/security-checks.md`.

| ID | Check | Severity |
|----|-------|----------|
| SE-01 | Injection via string interpolation with user input | P0 |
| SE-02 | Password stored without bcrypt/scrypt/argon2 | P0 |
| SE-03 | Data access without ownership check (IDOR) | P0 |
| SE-04 | Missing authorization on endpoint | P0/P1 |
| SE-05 | Debug mode in production path | P0 |
| SE-06 | Weak crypto algorithm for security purpose | P0 |
| SE-07 | SSRF via user-controlled URL | P0 |
| SE-08 | Credential/PII in log output | P0 |
| SE-09 | Insecure random for tokens/keys | P0 |
| SE-10 | Dependency without version pinning | P1 |
| SE-11 | Missing security headers | P2 |
| SE-12 | Auth failure without logging | P1 |
