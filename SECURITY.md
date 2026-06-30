# Security Architecture

Voice2Justice handles sensitive citizen grievance data and implements defense-in-depth strategies across the application layer.

## 1. Request Rate Limiting
Implemented via `Flask-Limiter` using in-memory IP tracking to prevent DDoS and brute-force attacks.
- **Global API Default**: 200 per day, 50 per hour
- **Complaint Submission (`/api/process`)**: 5 per minute
- **Admin/Citizen Login (`/login`)**: 10 per minute

## 2. HTTP Security Headers
Applied globally via Flask `@app.after_request` middleware:
- `Strict-Transport-Security` (HSTS): `max-age=31536000; includeSubDomains` (Forces HTTPS)
- `X-Content-Type-Options`: `nosniff` (Prevents MIME type sniffing)
- `X-Frame-Options`: `SAMEORIGIN` (Prevents Clickjacking via iframes)
- `X-XSS-Protection`: `1; mode=block` (Browser XSS filter)

## 3. Injection Prevention
- **SQL Injection**: All database interactions in `models/` use parameterized SQLite queries (`?` placeholders). No string concatenation is ever used in SQL commands.
- **Cross-Site Scripting (XSS)**: User inputs (like complaint text and location) are explicitly sanitized using Werkzeug's `markupsafe.escape()` before being stored in the database or reflected in HTML outputs.

## 4. Authentication & Session Management
- **Passwords**: Hashed securely using Werkzeug's implementation of PBKDF2 with SHA-256 (`generate_password_hash()`). Raw passwords are never logged or stored.
- **Session Expiry**: Sessions are marked as `permanent = True` with an absolute timeout of 30 minutes (`app.permanent_session_lifetime`).
- **Secret Key Validation**: The application strictly refuses to boot in `production` mode if `SECRET_KEY` is missing or left as the default development value.

## 5. Fraud Detection Engine
The application implements a multi-signal behavioral scoring system (0.0 to 1.0) rather than hard CAPTCHAs, preventing legitimate urgent complaints from being blocked.
**Scoring Signals:**
1. **IP Velocity** (+0.4): ≥5 complaints from the same IP in 1 hour.
2. **Account Velocity** (+0.3): ≥5 complaints from the same User ID in 1 hour.
3. **Text Duplication** (+0.5): Exact string match of complaint text previously submitted.
4. **ML Confidence** (+0.2): Classifier confidence < 30% (indicating likely spam/gibberish).

## 6. Document Integrity
- **SHA-256 Hashing**: Generated PDF reports include a cryptographic SHA-256 hash derived from the complaint ID, number, and verbatim text. This allows authorities to verify that a printed PDF has not been manipulated after the fact.
