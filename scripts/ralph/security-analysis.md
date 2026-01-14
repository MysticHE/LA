# Security Analysis Report
## Intelligent Image Generation with Nano Banana API

**Version:** 1.0
**Date:** 2026-01-14
**PRD Version:** 2.3

---

## 1. COMPLIANCE SCOPE IDENTIFICATION

### Regulatory Assessment

| Question | Answer | Regulation |
|----------|--------|------------|
| Handles personal data of individuals? | **YES** - User API keys, session data, user-generated content | **PDPA** applies |
| For financial institution (bank, insurer, payment)? | No | MAS TRM does not apply |
| Government/public sector project? | No | IM8 does not apply |
| Critical infrastructure (energy, healthcare, transport)? | No | CSA Cybersecurity Act does not apply |
| Data stored outside Singapore? | **YES** - API calls to Google Gemini (US servers) | Cross-border transfer assessment needed |

### Applicable Regulations

1. **PDPA (Personal Data Protection Act 2012)** - APPLICABLE
   - **Justification:** The application handles user API keys (which are linked to personal Google accounts), session identifiers, and user-generated LinkedIn post content. While the primary data is content (not PII), the API keys constitute personal data under PDPA as they are linked to identifiable individuals.
   - **Key Obligations:**
     - Consent for data collection (API key storage)
     - Protection of personal data (encryption at rest)
     - Data retention limits (session cleanup)
     - Notification of data breaches

2. **OWASP Security Standards** - APPLICABLE
   - **Justification:** Web application handling user authentication, API integrations, and user-generated content requires adherence to OWASP best practices.

3. **Cross-Border Data Transfer** - REQUIRES ASSESSMENT
   - **Justification:** LinkedIn post content and image generation prompts are sent to Google Gemini API servers located outside Singapore.
   - **Recommendation:** Ensure Google's data processing agreement covers PDPA requirements; consider adding user consent disclosure for cross-border transfer.

---

## 2. DATA CLASSIFICATION

| Data Type | Classification | Encryption Required | Access Level | Retention |
|-----------|---------------|---------------------|--------------|-----------|
| Gemini API Key | **SECRET** | TLS in transit + AES-256 at rest | Session-only, user who owns the key | Session lifetime (auto-cleanup on disconnect/expiry) |
| LinkedIn Post Content | **USER CONTENT** | TLS in transit | Processing-only, not persisted | Not retained (processed and discarded) |
| Generated Image Prompts | **USER CONTENT** | TLS in transit | Processing-only | Not retained |
| Generated Images (base64) | **USER CONTENT** | TLS in transit | User session only | Not persisted (returned to client only) |
| Session Identifier | **SENSITIVE** | TLS in transit | Server-side only | Session lifetime (24h max recommended) |
| Content Analysis Results | **INTERNAL** | TLS in transit | Processing-only | Not retained |
| Error Logs | **INTERNAL** | None required | DevOps/Admin | 30 days recommended |
| Rate Limit Tracking | **INTERNAL** | None required | System-only | Request window only |

### Data Flow Security Points

```
User Browser → [TLS 1.3] → FastAPI Backend → [TLS 1.3] → Google Gemini API
     ↓                           ↓
  Session ID              Encrypted API Key
                          (AES-256 at rest)
```

---

## 3. THREAT MODELING (STRIDE)

| Threat | Assets at Risk | Likelihood | Impact | Mitigation | Priority |
|--------|---------------|------------|--------|------------|----------|
| **Spoofing** - Attacker impersonates legitimate user session | User sessions, API keys | **M** | **H** | Session token validation, secure session cookies (HttpOnly, Secure, SameSite), session fixation prevention | **P0** |
| **Spoofing** - Attacker uses stolen API key | Gemini API quota, user billing | **M** | **H** | API key encryption, no key exposure in logs/responses, masked display in UI | **P0** |
| **Tampering** - Malicious prompt injection to generate harmful content | Image generation service, brand reputation | **M** | **M** | Input sanitization, prompt templates with bounded parameters, content moderation keywords block | **P1** |
| **Tampering** - Request manipulation to bypass rate limits | API resources, service availability | **L** | **M** | Server-side rate limiting per session, request signing, session validation | **P1** |
| **Repudiation** - User denies generating inappropriate content | Audit trail, legal compliance | **L** | **M** | Audit logging of generation requests (without sensitive content), session-user correlation | **P2** |
| **Information Disclosure** - API key leaked in logs/responses | Gemini API keys | **M** | **H** | Never log API keys, mask in all responses (show last 4 chars only), redact from error messages | **P0** |
| **Information Disclosure** - Generated content leaked to other users | User content, privacy | **L** | **H** | Session isolation, no server-side image caching, proper session scoping | **P1** |
| **Denial of Service** - Rate limit exhaustion attack | Service availability | **M** | **M** | Per-session rate limiting (20/min), global rate limiting, request queuing | **P1** |
| **Denial of Service** - Large payload attacks | Server resources | **L** | **M** | Request size limits (post content: 10KB max, prompt: 2KB max) | **P2** |
| **Elevation of Privilege** - Session hijacking to access another user's API key | User API keys, session data | **L** | **H** | Secure session management, session binding to IP/User-Agent (optional), short session lifetime | **P0** |
| **Elevation of Privilege** - API endpoint accessed without authentication | Protected endpoints | **M** | **H** | Middleware authentication on all /generate and /auth endpoints, 401 for missing auth | **P0** |

---

## 4. SECURITY REQUIREMENTS MATRIX

| Req ID | Requirement | Regulation | Priority | Acceptance Criteria |
|--------|-------------|------------|----------|---------------------|
| SEC-001 | Encrypt Gemini API keys at rest using AES-256 | PDPA, OWASP A02 | **P0** | GIVEN a Gemini API key is stored WHEN encryption_service.encrypt() is called THEN key is encrypted using AES-256 AND original plaintext is never persisted |
| SEC-002 | Never log or expose API keys in responses | PDPA, OWASP A02 | **P0** | GIVEN any API response or log entry WHEN API key is involved THEN only masked version (last 4 chars) is visible AND full key is never in logs/responses |
| SEC-003 | Validate and sanitize all user inputs | OWASP A03 | **P0** | GIVEN user input (post content, prompt, style) WHEN received by API THEN Pydantic validates against schema AND special characters are escaped AND max lengths enforced |
| SEC-004 | Implement session-based authentication for protected endpoints | OWASP A01, A07 | **P0** | GIVEN request to /api/generate/* or /api/auth/* WHEN session is invalid or missing THEN return 401 Unauthorized |
| SEC-005 | Apply rate limiting to image generation endpoint | OWASP A04 | **P0** | GIVEN image generation requests WHEN more than 20 requests per minute from same session THEN return 429 with Retry-After header |
| SEC-006 | Implement secure session management | OWASP A07 | **P0** | GIVEN session cookie WHEN set THEN include HttpOnly, Secure, SameSite=Strict flags AND session expires within 24 hours |
| SEC-007 | No sensitive data in error responses | OWASP A02, A09 | **P1** | GIVEN API error occurs WHEN error response is generated THEN response contains user-friendly message AND no stack traces/internal paths/API keys exposed |
| SEC-008 | Implement audit logging for security events | PDPA, OWASP A09 | **P1** | GIVEN API key connect/disconnect or image generation WHEN action completes THEN log event with timestamp, session ID, action type (no sensitive data) |
| SEC-009 | Secure cross-origin requests | OWASP A05 | **P1** | GIVEN CORS configuration WHEN request from unauthorized origin THEN reject with 403 AND only allow configured frontend origin |
| SEC-010 | Content size limits on all endpoints | OWASP A04 | **P1** | GIVEN request body WHEN size exceeds limit (10KB for post, 2KB for prompt) THEN return 413 Payload Too Large |
| SEC-011 | Prompt injection prevention | OWASP A03 | **P1** | GIVEN user-customized prompt WHEN sent to Gemini API THEN wrap in safe prompt template AND filter known injection patterns |
| SEC-012 | Session cleanup on disconnect | PDPA | **P1** | GIVEN user disconnects or session expires WHEN cleanup triggered THEN encrypted API key is securely deleted AND session data cleared |
| SEC-013 | Input validation for image dimensions | OWASP A03 | **P2** | GIVEN dimension parameter WHEN received THEN validate against allowed values only (1200x627, 1080x1080, 1200x1200) |
| SEC-014 | Secure image download (prevent path traversal) | OWASP A01, A03 | **P2** | GIVEN download request WHEN filename generated THEN use sanitized UUID-based filename AND no user-controlled path components |

---

## 5. SECURITY USER STORIES

```gherkin
Feature: API Key Protection
  As a user
  I want my Gemini API key to be securely stored
  So that my API credentials cannot be stolen or misused

  Scenario: API key encryption at rest
    Given I have entered my Gemini API key
    When I submit the key to the connect endpoint
    Then the key is encrypted using AES-256 before storage
    And the plaintext key is not written to any log or storage
    And the response contains only a masked key (last 4 characters)

  Scenario: API key not exposed in error responses
    Given my Gemini API key is stored in the session
    When an API error occurs during image generation
    Then the error response does not contain my API key
    And the error log does not contain my API key
    And I receive a user-friendly error message

  Scenario: API key cleanup on disconnect
    Given my Gemini API key is stored in the session
    When I disconnect from the Gemini service
    Then my encrypted API key is securely deleted
    And subsequent requests return "not connected" status
```

```gherkin
Feature: Session Security
  As a system administrator
  I want secure session management
  So that user sessions cannot be hijacked or misused

  Scenario: Protected endpoint requires valid session
    Given I am not authenticated
    When I request /api/generate/image
    Then I receive a 401 Unauthorized response
    And no image generation is attempted

  Scenario: Session cookie security attributes
    Given I successfully connect my API key
    When a session cookie is set
    Then the cookie has HttpOnly flag set
    And the cookie has Secure flag set
    And the cookie has SameSite=Strict attribute

  Scenario: Session expiration
    Given I have an active session
    When 24 hours have passed since session creation
    Then my session is automatically invalidated
    And my stored API key is securely deleted
```

```gherkin
Feature: Input Validation and Injection Prevention
  As a security system
  I want all user inputs validated
  So that injection attacks are prevented

  Scenario: Post content validation
    Given I am generating an image
    When I submit post content exceeding 10KB
    Then I receive a 413 Payload Too Large response
    And no processing is performed

  Scenario: Prompt injection prevention
    Given I am customizing the image prompt
    When I enter text containing "ignore previous instructions"
    Then the malicious pattern is filtered or escaped
    And the sanitized prompt is used for generation

  Scenario: Invalid dimension rejection
    Given I am selecting image dimensions
    When I submit dimensions not in the allowed list
    Then I receive a 400 Bad Request response
    And the error message lists valid dimension options
```

```gherkin
Feature: Rate Limiting
  As a system operator
  I want rate limiting on image generation
  So that the service remains available and abuse is prevented

  Scenario: Rate limit enforcement
    Given I have made 20 image generation requests in the last minute
    When I make another request
    Then I receive a 429 Too Many Requests response
    And the response includes a Retry-After header
    And the frontend displays a countdown timer

  Scenario: Rate limit per session
    Given User A has exhausted their rate limit
    When User B makes a request
    Then User B's request is processed normally
    And User A remains rate limited
```

```gherkin
Feature: Audit Logging
  As a compliance officer
  I want security events logged
  So that I can investigate incidents and demonstrate PDPA compliance

  Scenario: API key connection logged
    Given I submit my Gemini API key
    When the connection succeeds
    Then an audit log entry is created
    And the log contains timestamp and session ID
    And the log does NOT contain the API key

  Scenario: Image generation logged
    Given I request image generation
    When the generation completes
    Then an audit log entry is created
    And the log contains request metadata
    And the log does NOT contain the generated prompt or image content
```

---

## 6. OWASP TOP 10 CHECKLIST

| Risk | Vulnerable? | Status | Notes |
|------|-------------|--------|-------|
| **A01: Broken Access Control** | Potential | [x] Requires mitigation | Image generation endpoints must validate session; ensure user can only access their own session data |
| **A02: Cryptographic Failures** | Potential | [x] Requires mitigation | API keys must be encrypted with AES-256; TLS 1.3 required for all traffic; no hardcoded secrets |
| **A03: Injection** | Potential | [x] Requires mitigation | User prompts could contain injection attempts; require Pydantic validation and prompt sanitization |
| **A04: Insecure Design** | Low Risk | [x] Addressed in PRD | Rate limiting designed in; session-based auth pattern follows existing secure implementation |
| **A05: Security Misconfiguration** | Potential | [x] Requires mitigation | CORS must be properly configured; error pages must not leak info; default credentials must not exist |
| **A06: Vulnerable Components** | Unknown | [ ] Requires review | Dependencies (httpx, cryptography, Pydantic) should be audited; use Dependabot/Snyk for monitoring |
| **A07: Auth Failures** | Potential | [x] Requires mitigation | Session management must be secure; API key validation required before use |
| **A08: Data Integrity Failures** | Low Risk | [x] Addressed | No software updates or CI/CD pipelines in scope; image generation is stateless |
| **A09: Logging Failures** | Potential | [x] Requires mitigation | Must implement audit logging; must ensure no sensitive data in logs |
| **A10: SSRF** | Low Risk | [ ] N/A | Application makes outbound calls to Gemini API only; no user-controlled URLs in backend requests |

### Checklist Summary
- [x] A01: Broken Access Control - Session validation required on protected endpoints
- [x] A02: Cryptographic Failures - API key encryption and TLS enforcement
- [x] A03: Injection - Input validation and prompt sanitization
- [x] A04: Insecure Design - Rate limiting and secure auth patterns
- [x] A05: Security Misconfiguration - CORS and error handling review
- [ ] A06: Vulnerable Components - Dependency audit recommended
- [x] A07: Auth Failures - Secure session management
- [x] A08: Data Integrity Failures - N/A for this feature
- [x] A09: Logging Failures - Audit logging implementation
- [ ] A10: SSRF - Not applicable (no user-controlled URLs)

---

## 7. RECOMMENDED SECURITY STORIES FOR PRD

The following security-focused user stories should be added to `prd.json`:

```json
[
  {
    "id": "US-SEC-001",
    "title": "Implement Secure API Key Storage",
    "description": "As a user, I want my Gemini API key encrypted at rest so that it cannot be stolen if the server is compromised",
    "acceptanceCriteria": [
      "GIVEN a Gemini API key WHEN stored in session THEN key is encrypted using AES-256 via encryption_service.py",
      "GIVEN any log output WHEN API key is involved THEN only masked version (****xxxx) appears",
      "GIVEN API response WHEN key is included THEN only last 4 characters are visible",
      "Security scan passes with 0 critical findings for credential exposure"
    ],
    "priority": 1,
    "complexity": 2,
    "estimatedMinutes": 20,
    "filesAffected": [
      "backend/src/services/encryption_service.py",
      "backend/src/services/key_storage_service.py",
      "backend/src/api/gemini_routes.py"
    ],
    "securityCategory": "encryption"
  },
  {
    "id": "US-SEC-002",
    "title": "Implement Input Validation for Image Generation",
    "description": "As a system, I want all image generation inputs validated so that injection attacks are prevented",
    "acceptanceCriteria": [
      "GIVEN post content input WHEN exceeds 10KB THEN return 413 error",
      "GIVEN custom prompt WHEN exceeds 2KB THEN return 413 error",
      "GIVEN dimension parameter WHEN not in [1200x627, 1080x1080, 1200x1200] THEN return 400 error",
      "GIVEN malicious prompt patterns WHEN detected THEN sanitize or reject with 400 error",
      "All inputs validated through Pydantic schemas"
    ],
    "priority": 1,
    "complexity": 2,
    "estimatedMinutes": 25,
    "filesAffected": [
      "backend/src/models/image_schemas.py",
      "backend/src/validators/prompt_validator.py",
      "backend/src/api/image_routes.py"
    ],
    "securityCategory": "validation"
  },
  {
    "id": "US-SEC-003",
    "title": "Implement Secure Session Management",
    "description": "As a user, I want my session securely managed so that my credentials cannot be hijacked",
    "acceptanceCriteria": [
      "GIVEN session cookie WHEN created THEN has HttpOnly, Secure, SameSite=Strict flags",
      "GIVEN session WHEN older than 24 hours THEN automatically expired and API key deleted",
      "GIVEN protected endpoint WHEN no valid session THEN return 401 Unauthorized",
      "GIVEN session disconnect WHEN triggered THEN encrypted API key securely deleted"
    ],
    "priority": 1,
    "complexity": 2,
    "estimatedMinutes": 20,
    "filesAffected": [
      "backend/src/middleware/session_middleware.py",
      "backend/src/services/session_service.py",
      "backend/src/api/gemini_routes.py"
    ],
    "securityCategory": "authentication"
  },
  {
    "id": "US-SEC-004",
    "title": "Implement Security Audit Logging",
    "description": "As a compliance officer, I want security events logged so that incidents can be investigated",
    "acceptanceCriteria": [
      "GIVEN API key connect/disconnect WHEN action completes THEN audit log created with timestamp and session ID",
      "GIVEN image generation WHEN completed THEN audit log created with request metadata",
      "GIVEN any audit log WHEN written THEN contains no sensitive data (API keys, prompt content)",
      "GIVEN audit logs WHEN queried THEN support filtering by date and session"
    ],
    "priority": 2,
    "complexity": 2,
    "estimatedMinutes": 25,
    "filesAffected": [
      "backend/src/services/audit_logger.py",
      "backend/src/api/gemini_routes.py",
      "backend/src/api/image_routes.py"
    ],
    "securityCategory": "logging"
  },
  {
    "id": "US-SEC-005",
    "title": "Implement Error Handling Without Data Leakage",
    "description": "As a security system, I want error responses sanitized so that internal details are not exposed",
    "acceptanceCriteria": [
      "GIVEN any API error WHEN response generated THEN no stack traces in response body",
      "GIVEN Gemini API error WHEN occurring THEN no API key in error message",
      "GIVEN internal error WHEN occurring THEN return generic 500 message with correlation ID",
      "GIVEN validation error WHEN occurring THEN return helpful message without internal paths"
    ],
    "priority": 2,
    "complexity": 1,
    "estimatedMinutes": 15,
    "filesAffected": [
      "backend/src/middleware/error_handler.py",
      "backend/src/api/image_routes.py",
      "backend/src/api/gemini_routes.py"
    ],
    "securityCategory": "validation"
  }
]
```

---

## 8. SECURITY NFRs TO ADD

The following Non-Functional Requirements should be added to the PRD:

| ID | Title | Priority | Acceptance Criteria |
|----|-------|----------|---------------------|
| NFR-SEC-001 | Secure Session Cookies | Must | Session cookies must have HttpOnly, Secure, and SameSite=Strict flags; sessions expire within 24 hours |
| NFR-SEC-002 | Audit Logging | Must | All API key operations and image generation requests must be audit logged without sensitive data |
| NFR-SEC-003 | Error Message Security | Must | Error responses must not contain stack traces, internal paths, or sensitive data; correlation IDs for debugging |
| NFR-SEC-004 | Input Size Limits | Must | Post content limited to 10KB; prompts limited to 2KB; enforce at API level with 413 responses |
| NFR-SEC-005 | CORS Configuration | Must | CORS must only allow the configured frontend origin; reject requests from unauthorized origins |
| NFR-SEC-006 | Dependency Security | Should | All Python and Node.js dependencies must be scanned for vulnerabilities; critical CVEs must be addressed within 7 days |

---

## 9. CROSS-BORDER DATA TRANSFER NOTICE

### Recommendation for User Interface

Since LinkedIn post content is transmitted to Google Gemini API servers (located outside Singapore), the following disclosure should be added to the Gemini API connection UI:

> **Data Processing Notice:**
> By connecting your Gemini API key, you acknowledge that your LinkedIn post content will be sent to Google's servers for image generation. This data may be processed outside of Singapore in accordance with Google's privacy policy and data processing terms.

This satisfies PDPA requirements for cross-border data transfer disclosure.

---

## Summary

### Critical (P0) Security Items
1. API key encryption at rest (SEC-001)
2. No API key exposure in logs/responses (SEC-002)
3. Session-based authentication on protected endpoints (SEC-004)
4. Rate limiting on image generation (SEC-005)
5. Secure session management with proper cookie flags (SEC-006)
6. Privilege escalation prevention (SEC-010)

### High Priority (P1) Security Items
1. Input validation and sanitization (SEC-003)
2. Error message security (SEC-007)
3. Audit logging implementation (SEC-008)
4. CORS configuration (SEC-009)
5. Content size limits (SEC-010)
6. Prompt injection prevention (SEC-011)

### Compliance Summary
- **PDPA**: Applicable - requires consent disclosure, encryption, and audit logging
- **OWASP**: 8 of 10 risks require mitigation attention
- **Cross-Border**: Requires user notification for Gemini API data transfer
