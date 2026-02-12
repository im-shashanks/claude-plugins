# Security Checks

Gate-specific security checks loaded by sw-quality during code and test review. Aligned with OWASP Top 10. These checks detect the most critical security vulnerabilities that commonly ship to production.

---

## Code Gate — Security Checks

### SE-01: Injection via String Interpolation

- **Severity:** P0
- **Detection:** String interpolation (f-strings, template literals, string concat, format()) containing user input used in SQL, shell commands, OS commands, LDAP queries, or template rendering
- **Example (bad):** `db.query(f"SELECT * FROM users WHERE id = {request.id}")`
- **Example (good):** `db.query("SELECT * FROM users WHERE id = ?", [request.id])`
- **Scope:** Any code path reachable from user input (request params, body, headers, query strings, file uploads)

### SE-02: Password Without Proper Hashing

- **Severity:** P0
- **Detection:** Password stored or compared using MD5, SHA-1, SHA-256 (without proper KDF), or plaintext. Look for `hashlib.md5`, `hashlib.sha1`, `crypto.createHash('md5')`, or password stored directly.
- **Example (bad):** `hashed = hashlib.sha256(password.encode()).hexdigest()`
- **Example (good):** `hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))`

### SE-03: IDOR — Data Access Without Ownership Check

- **Severity:** P0
- **Detection:** Database query fetching a resource by ID from request parameters without filtering by the authenticated user's identity
- **Example (bad):** `order = db.get(Order, id=request.params.order_id)`
- **Example (good):** `order = db.get(Order, id=request.params.order_id, user_id=current_user.id)`
- **Note:** Some endpoints (admin, public data) legitimately skip ownership checks — verify the endpoint's authorization model

### SE-04: Missing Authorization on Endpoint

- **Severity:** P0 (public endpoint that should be protected) / P1 (inconsistent auth middleware)
- **Detection:** Route/endpoint handler without authentication/authorization middleware or decorator when similar endpoints in the same module have auth
- **Example (bad):** `@app.route("/admin/users") def list_users(): ...` — no auth decorator
- **Example (good):** `@app.route("/admin/users") @require_role("admin") def list_users(): ...`

### SE-05: Debug Mode in Production Path

- **Severity:** P0
- **Detection:** `DEBUG=True`, `debug: true`, `app.debug = True`, verbose error handlers, or development-only middleware in production configuration or without environment guard
- **Example (bad):** `app = Flask(__name__); app.debug = True`
- **Example (good):** `app.debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"`

### SE-06: Weak Crypto Algorithm

- **Severity:** P0
- **Detection:** Use of DES, 3DES, RC4, MD5 (for security), SHA-1 (for security), AES-ECB, RSA-1024 in security-critical code (not checksums or non-security hashing)
- **Example (bad):** `cipher = AES.new(key, AES.MODE_ECB)`
- **Example (good):** `cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)`

### SE-07: SSRF via User-Controlled URL

- **Severity:** P0
- **Detection:** HTTP request (requests.get, fetch, urllib) where the URL or hostname comes from user input without allowlist validation
- **Example (bad):** `response = requests.get(request.params.webhook_url)`
- **Example (good):** `if urlparse(url).hostname in ALLOWED_HOSTS: response = requests.get(url)`

### SE-08: Credential/PII in Log Output

- **Severity:** P0
- **Detection:** Logging statements that output passwords, tokens, API keys, bearer tokens, credit card numbers, SSNs, or full user objects that contain sensitive fields
- **Example (bad):** `logger.info(f"Login attempt: user={email}, password={password}")`
- **Example (good):** `logger.info(f"Login attempt: user={email}")`

### SE-09: Insecure Random for Security Purpose

- **Severity:** P0
- **Detection:** `math.random()`, `random.randint()`, `Math.random()`, `rand()` used for tokens, session IDs, passwords, nonces, or cryptographic keys
- **Example (bad):** `token = ''.join(random.choices(string.ascii_letters, k=32))`
- **Example (good):** `token = secrets.token_urlsafe(32)`

### SE-10: Dependency Without Version Pinning

- **Severity:** P1
- **Detection:** Package dependency without version constraint (no lock file, or `*` / `latest` as version)
- **Example (bad):** `"lodash": "*"` or `pip install requests` without lock file
- **Example (good):** `"lodash": "^4.17.21"` with `package-lock.json`

### SE-11: Missing Security Headers

- **Severity:** P2
- **Detection:** Web application response without security headers (HSTS, CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy). Check middleware/framework configuration.
- **Note:** API-only services may not need all headers — apply contextually

### SE-12: Auth Failure Without Logging

- **Severity:** P1
- **Detection:** Authentication failure code path (wrong password, invalid token, expired session) without a log statement
- **Example (bad):** `if not verify_password(pw, hash): return 401`
- **Example (good):** `if not verify_password(pw, hash): logger.warning(f"Failed login: {email}"); return 401`

---

## Test Gate — Security Test Checks

### ST-01: No Injection Test for Input Endpoint

- **Severity:** P1
- **Detection:** Endpoint that accepts user input (POST/PUT/PATCH with body, GET with query params) without a test that sends injection payloads (SQL special chars, script tags, command separators)
- **What to verify:** Test exists that sends `'; DROP TABLE`, `<script>`, `| ls`, etc. and verifies safe handling

### ST-02: No Authorization Test for Protected Endpoint

- **Severity:** P1
- **Detection:** Protected endpoint without a test that verifies unauthorized access returns 401/403
- **What to verify:** Test exists that calls the endpoint without auth (or with wrong auth) and asserts rejection

### ST-03: No IDOR Test for User-Scoped Data

- **Severity:** P1
- **Detection:** Endpoint that returns user-specific data without a test where user A tries to access user B's resource
- **What to verify:** Test exists that authenticates as user A and requests user B's resource, asserting 403 or 404
