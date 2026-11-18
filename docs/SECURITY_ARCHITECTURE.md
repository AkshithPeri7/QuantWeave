# QuantWeave — Security Architecture & Hardening Reference

This document outlines the defense-in-depth security model implemented across QuantWeave.

---

## 1. Authentication & Session Management

### 1. Token Architecture
- **Stateless JSON Web Tokens (JWT)**: Signed using HMAC-SHA256 (`HS256`) with a cryptographically strong secret key (`SECRET_KEY`).
- **Token Separation**:
  - `access_token`: Short-lived (30 minutes) token authorizing individual API operations.
  - `refresh_token`: Longer-lived (7 days) token used strictly to rotate access credentials.

### 2. Cookie Hardening against Cross-Site Scripting (XSS)
Access tokens are stored inside browser cookies with hardened security flags:
- `HttpOnly`: Completely blocks JavaScript access (`document.cookie`), neutralizing token theft via XSS vulnerabilities.
- `Secure`: Ensures tokens are only transmitted across TLS/HTTPS connections.
- `SameSite=Lax`: Prevents cookies from being transmitted during cross-site third-party embedding.

### 3. Password Storage
- Passwords are never stored in plaintext or reversible formats.
- Hashed using **`bcrypt`** with automated salt generation.
- Defense against timing attacks: Password comparisons use constant-time verification functions.

---

## 2. Cross-Site Request Forgery (CSRF) Defense-in-Depth

Because authentication tokens reside in browser cookies, QuantWeave implements multi-tier CSRF defenses in `apps/api/app/api/deps.py`:

1. **Content-Type Enforcement**: All state-mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`) require `application/json` or `multipart/form-data`. Traditional cross-site HTML form submissions cannot submit raw JSON without triggering browser CORS preflight.
2. **Custom Client Header Verification**: Requests must present the custom header:
   ```http
   X-Requested-With: XMLHttpRequest
   ```
   Cross-origin scripts cannot forge custom headers without explicit CORS authorization from the server.
3. **Strict Origin & Referer Verification**: In production, the request `Origin` header must strictly match the whitelisted domain.

---

## 3. Sliding-Window Rate Limiter & Memory Protection

To protect endpoints against credential brute-forcing, scraping, and Denial of Service (DoS):

- Implemented in `apps/api/app/core/rate_limiter.py`.
- Tracks microsecond request timestamps per IP address within a rolling 60-second window.
- Exceeding the threshold immediately returns `HTTP 429 Too Many Requests` with a `Retry-After: 60` response header.
- **Memory Leak Mitigation**: A background garbage collector purges inactive IP buckets whose timestamp deques have expired, preventing dictionary bloat.

---

## 4. Cross-Tenant Data Isolation Guarantees

In multi-tenant financial environments, horizontal privilege escalation (User A accessing User B's portfolio or AI chat) is strictly prevented:

1. **Database Queries**: All portfolio, transaction, and AI conversation queries explicitly enforce `user_id == current_user.id`.
2. **Non-Enumerative Responses**: Accessing an unauthorized ID returns `HTTP 404 Not Found` rather than `HTTP 403 Forbidden` to prevent resource ID enumeration attacks.
3. **AI Copilot Server-Side Injection**: The AI Copilot cannot accept a user ID from generative model output. The user ID is injected server-side from the verified JWT context before executing any analytics tool.

---

## 5. File Upload & Input Validation

1. **CSV Upload Constraints**:
   - File size restricted to a maximum of 2 MB.
   - Rejection of files containing null bytes (`\0`) to prevent directory traversal or C-runtime buffer overflow exploits.
   - Pydantic v2 type validation for every numerical column.
2. **SQL Injection Prevention**:
   - 100% of database interactions utilize SQLAlchemy 2.0 parameterized queries and ORM objects. Raw string concatenation in SQL queries is prohibited.
