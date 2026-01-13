# Security Analysis: OpenAI API Integration for LinkedIn Post Generation

**Document Version:** 1.0
**Analysis Date:** 2026-01-13
**Feature:** OpenAI API Integration for LinkedIn Content Automation
**Analyst:** Security Agent

---

## 1. COMPLIANCE SCOPE IDENTIFICATION

### Regulatory Assessment

| Question | Answer | Applicable Regulation |
|----------|--------|----------------------|
| Handles personal data of individuals? | **Partial** - API keys are user-owned credentials; user session IDs are generated | **PDPA** - Limited scope (session management) |
| For financial institution (bank, insurer, payment)? | **No** - Content automation tool | MAS TRM - Not applicable |
| Government/public sector project? | **No** - Private SaaS application | IM8 - Not applicable |
| Critical infrastructure (energy, healthcare, transport)? | **No** - Content generation tool | CSA Cybersecurity Act - Not applicable |
| Data stored outside Singapore? | **Possible** - API calls to OpenAI (US servers) | Cross-border assessment needed |

### Applicable Regulations & Standards

| Regulation/Standard | Applicability | Justification |
|--------------------|---------------|---------------|
| **PDPA (Singapore)** | Limited | Session IDs may correlate to user behavior; API key handling involves user credentials |
| **OWASP Top 10 2021** | **Full** | Web application security best practices apply |
| **OWASP API Security Top 10** | **Full** | REST API endpoints require protection |
| **OpenAI Terms of Service** | **Full** | Must comply with OpenAI API usage policies |

### Cross-Border Data Transfer Assessment

**Risk:** User API keys are transmitted to OpenAI's US-based servers for validation and generation.

**Mitigations:**
1. API keys are user-provided (user consents to OpenAI TOS)
2. No persistent storage - session-scoped only
3. Keys encrypted in transit (TLS) and at rest (AES-256-GCM)
4. Generated content returns to Singapore-hosted application

---

## 2. DATA CLASSIFICATION

| Data Type | Classification | Encryption Required | Access Level | Retention | Handling Requirements |
|-----------|---------------|---------------------|--------------|-----------|----------------------|
| **OpenAI API Key** | **SECRET** | TLS 1.3 (transit) + AES-256-GCM (rest) | Session owner only | Session lifetime only | Never log, mask display, secure input |
| **Claude API Key** | **SECRET** | TLS 1.3 (transit) + AES-256-GCM (rest) | Session owner only | Session lifetime only | Never log, mask display, secure input |
| **Session ID** | Internal | TLS 1.3 (transit) | Per-client | Session lifetime | Cryptographically random generation |
| **GitHub Repository URL** | Public | TLS 1.3 (transit) | Session owner | Request-scoped | Validate URL format |
| **Repository Analysis** | Internal | TLS 1.3 (transit) | Session owner | Request-scoped | No sensitive code storage |
| **Generated LinkedIn Post** | Internal | TLS 1.3 (transit) | Session owner | Request-scoped | User-controlled content |
| **Selected AI Provider** | Internal | None | Session owner | Session lifetime | Non-sensitive preference |
| **Selected Model** | Internal | None | Session owner | Request-scoped | Non-sensitive preference |
| **Error Messages** | Internal | TLS 1.3 (transit) | Session owner | Request-scoped | Sanitize - no key exposure |

### Data Flow Diagram

```
[User Browser] --TLS 1.3--> [FastAPI Backend] --TLS 1.3--> [OpenAI API]
                                   |
                                   v
                        [In-Memory Storage]
                        (AES-256-GCM encrypted keys)
```

---

## 3. THREAT MODELING (STRIDE)

### System Components

- **Frontend:** React 19 + TypeScript + Zustand
- **Backend:** Python FastAPI with Pydantic
- **External APIs:** OpenAI API, Claude API, GitHub API
- **Storage:** In-memory session storage with AES-256-GCM

### STRIDE Analysis

| Threat Category | Specific Threat | Assets at Risk | Likelihood | Impact | Mitigation | Priority |
|-----------------|-----------------|----------------|------------|--------|------------|----------|
| **Spoofing** | Session ID impersonation | User session, stored API keys | M | H | Cryptographically random 256-bit session IDs; Session ID validation | P0 |
| **Spoofing** | API key theft via MITM | OpenAI/Claude API keys | L | H | TLS 1.3 enforcement; HSTS headers | P0 |
| **Spoofing** | Cross-site request forgery (CSRF) | User actions, API key operations | M | M | CSRF tokens on state-changing operations; SameSite cookies | P1 |
| **Tampering** | API key modification in transit | API key integrity | L | H | TLS encryption; Input re-validation on backend | P1 |
| **Tampering** | In-memory storage manipulation | Encrypted API keys | L | H | Memory isolation; Process-level access control | P2 |
| **Tampering** | Malicious prompt injection | Generated content quality | M | M | Prompt template hardening; Output sanitization | P1 |
| **Repudiation** | Unauthorized API key usage denied | Audit trail, user accountability | M | M | Comprehensive audit logging with timestamps and session IDs | P1 |
| **Repudiation** | Fraudulent disconnect claims | Session state integrity | L | L | Log all connect/disconnect operations with timestamps | P2 |
| **Info Disclosure** | API key exposure in logs | OpenAI/Claude API keys | H | H | Pattern-based log filtering (sk-*, sk-ant-*); Log sanitization | P0 |
| **Info Disclosure** | API key exposure in error responses | API keys | M | H | Generic error messages; No key reflection in errors | P0 |
| **Info Disclosure** | API key exposure in frontend state | API keys | M | H | Store only masked key (last 4 chars) in frontend | P0 |
| **Info Disclosure** | Session ID enumeration | Active sessions | L | M | Non-sequential, cryptographically random session IDs | P1 |
| **Info Disclosure** | Sensitive data in browser storage | Session data | L | M | No localStorage/sessionStorage for secrets; Memory only | P1 |
| **DoS** | API rate limit exhaustion | Service availability | M | M | Backend rate limiting; User-level quotas | P1 |
| **DoS** | Resource exhaustion via large requests | Backend server | L | M | Request size limits; Timeout enforcement | P2 |
| **DoS** | Session storage exhaustion | In-memory storage | L | M | Session limits; TTL-based cleanup | P2 |
| **Elevation of Privilege** | Cross-session key access | Other users' API keys | L | H | Session isolation; Authorization checks on all key operations | P0 |
| **Elevation of Privilege** | Backend injection via API key input | Backend server | L | H | Strict input validation; No shell/SQL operations with keys | P0 |

### Risk Matrix Summary

```
           IMPACT
           H   M   L
         +---+---+---+
    H    | 2 | 0 | 0 |  HIGH PRIORITY: 2 (P0)
L   -----+---+---+---+
I   M    | 5 | 4 | 0 |  MEDIUM PRIORITY: 9 (P1)
K   -----+---+---+---+
E   L    | 4 | 2 | 1 |  LOW PRIORITY: 7 (P2)
L        +---+---+---+
```

---

## 4. SECURITY REQUIREMENTS MATRIX

| Req ID | Requirement | Regulation/Standard | Priority | Acceptance Criteria |
|--------|-------------|---------------------|----------|---------------------|
| **SEC-001** | Encrypt API keys at rest using AES-256-GCM | OWASP A02 | P0 | GIVEN an API key is stored WHEN retrieved from memory THEN it must be encrypted with AES-256-GCM using a per-session derived key |
| **SEC-002** | Never log API keys or key fragments | OWASP A09 | P0 | GIVEN any log statement WHEN the output contains patterns matching `sk-*` or `sk-ant-*` THEN the pattern is replaced with `[REDACTED]` |
| **SEC-003** | Validate all API key inputs with schemas | OWASP A03 | P0 | GIVEN an API key input WHEN submitted THEN Pydantic validates format (OpenAI: `sk-*`, length 40-200 chars) |
| **SEC-004** | Session-based access control for keys | OWASP A01 | P0 | GIVEN a key retrieval request WHEN session ID doesn't match THEN return 403 Forbidden |
| **SEC-005** | Mask API keys in frontend display | OWASP A02 | P0 | GIVEN a connected key WHEN displaying status THEN only show `sk-...{last 4 chars}` format |
| **SEC-006** | TLS 1.3 for all external communications | OWASP A02 | P0 | GIVEN an API request WHEN connecting to OpenAI/Claude/GitHub THEN TLS 1.3 minimum is enforced |
| **SEC-007** | Secure error handling without key exposure | OWASP A02 | P0 | GIVEN an API error WHEN returning to client THEN never include full API key in error message |
| **SEC-008** | Generate cryptographically random session IDs | OWASP A07 | P1 | GIVEN a new session WHEN ID is generated THEN use CSPRNG with minimum 256 bits entropy |
| **SEC-009** | Implement request rate limiting | OWASP A04 | P1 | GIVEN API endpoints WHEN request rate exceeds 100/min per session THEN return 429 Too Many Requests |
| **SEC-010** | Audit log all key operations | OWASP A09 | P1 | GIVEN a connect/disconnect/validate operation WHEN completed THEN log session ID, timestamp, operation, success/failure |
| **SEC-011** | Implement CSRF protection | OWASP A01 | P1 | GIVEN state-changing requests WHEN submitted THEN validate CSRF token or use SameSite=Strict cookies |
| **SEC-012** | Set secure HTTP headers | OWASP A05 | P1 | GIVEN any HTTP response WHEN returned THEN include CSP, X-Content-Type-Options, X-Frame-Options headers |
| **SEC-013** | Validate provider selection parameter | OWASP A03 | P1 | GIVEN provider parameter WHEN submitted THEN only accept enum values: 'claude', 'openai' |
| **SEC-014** | Validate model selection parameter | OWASP A03 | P1 | GIVEN model parameter WHEN submitted THEN only accept allowlist: 'gpt-4o', 'gpt-4', 'gpt-3.5-turbo' |
| **SEC-015** | Session timeout and cleanup | OWASP A07 | P2 | GIVEN a session WHEN inactive for 24 hours THEN automatically expire and securely delete stored keys |
| **SEC-016** | Request size limits | OWASP A04 | P2 | GIVEN any request WHEN body exceeds 10MB THEN reject with 413 Payload Too Large |
| **SEC-017** | Secure key deletion | OWASP A02 | P2 | GIVEN disconnect request WHEN key is removed THEN overwrite memory before deallocation |

---

## 5. SECURITY USER STORIES

### Feature: API Key Secure Input and Validation

```gherkin
Feature: API Key Secure Input and Validation
  As a user providing my OpenAI API key
  I want my key to be validated securely
  So that only valid keys are accepted and my credentials remain protected

  Background:
    Given I am on the OpenAI connection page
    And I have a valid session ID

  Scenario: Valid API key format is accepted
    Given I enter an API key starting with "sk-" and 51 characters long
    When I submit the key for validation
    Then the system should validate the format
    And call OpenAI models.list endpoint
    And store the key encrypted with AES-256-GCM
    And log "OpenAI key validation: success" with session ID (no key)
    And return masked key "sk-...{last4}"

  Scenario: Invalid API key format is rejected
    Given I enter an API key "invalid-key-format"
    When I submit the key for validation
    Then the system should return validation error
    And NOT make any external API call
    And log "OpenAI key validation: format_error" with session ID
    And NOT store any value

  Scenario: API key fails OpenAI validation
    Given I enter a properly formatted but invalid API key
    When I submit the key for validation
    Then OpenAI API should return 401 Unauthorized
    And system should return "Invalid API key" error
    And log "OpenAI key validation: auth_failed" with session ID
    And NOT store the key

  Scenario: API key is never logged
    Given I enter any API key value
    When the system processes the request
    Then no log output should contain the full key
    And any "sk-" pattern in logs should be redacted
```

### Feature: Session-Based Access Control

```gherkin
Feature: Session-Based Access Control
  As a security-conscious user
  I want my API keys isolated to my session
  So that other users cannot access my credentials

  Background:
    Given user A has session ID "session-A-xyz"
    And user B has session ID "session-B-abc"

  Scenario: User can only access their own keys
    Given user A has connected their OpenAI key
    When user A requests their key status
    Then they receive their masked key information

  Scenario: User cannot access another user's keys
    Given user A has connected their OpenAI key
    When user B attempts to access keys using session ID "session-A-xyz"
    Then the system should return 403 Forbidden
    And log "unauthorized_access_attempt" with both session IDs
    And NOT return any key information

  Scenario: Session ID header is required
    Given a request without X-Session-ID header
    When any key-related endpoint is called
    Then the system should return 401 Unauthorized
    And log "missing_session_id" with request details
```

### Feature: Secure Key Disconnection

```gherkin
Feature: Secure Key Disconnection
  As a user
  I want to securely disconnect my API key
  So that my credentials are properly removed from the system

  Scenario: Key is securely deleted on disconnect
    Given I have a connected OpenAI key
    When I request to disconnect
    Then the system should securely overwrite the encrypted key
    And remove the key from in-memory storage
    And log "openai_key_disconnected" with session ID and timestamp
    And return success confirmation
    And subsequent status checks should show "Not Connected"

  Scenario: Disconnect requires confirmation
    Given I have a connected OpenAI key
    When I click the disconnect button
    Then a confirmation dialog should appear
    And the key should NOT be removed until confirmed
```

### Feature: API Key Error Handling

```gherkin
Feature: Secure Error Handling
  As a user
  I want error messages that help me fix issues
  So that I can troubleshoot without exposing my credentials

  Scenario: Rate limit error displays safely
    Given I have a connected OpenAI key
    When I trigger a rate limit (429) error
    Then the error message should say "Rate limit exceeded. Please retry in X seconds"
    And NOT include my API key
    And log "rate_limit_exceeded" with session ID and retry_after value

  Scenario: Authentication error displays safely
    Given my stored OpenAI key has been revoked externally
    When I attempt to generate a post
    Then the error message should say "API key authentication failed. Please reconnect."
    And NOT include my API key or partial key
    And offer option to disconnect and reconnect

  Scenario: Server errors are sanitized
    Given any 500-level error occurs
    When the error is returned to the client
    Then the response should NOT contain stack traces
    And NOT contain internal paths
    And NOT contain the API key
    And provide a generic "Internal server error" message
```

### Feature: Audit Logging

```gherkin
Feature: Security Audit Logging
  As a security administrator
  I want comprehensive audit logs
  So that I can investigate security incidents

  Scenario: Key connection is logged
    Given a user connects their OpenAI key
    When the operation completes
    Then an audit log entry should contain:
      | field           | value                    |
      | timestamp       | ISO 8601 format          |
      | session_id      | hashed or first 8 chars  |
      | operation       | "openai_key_connect"     |
      | status          | "success" or "failure"   |
      | error_code      | null or error code       |
    And NOT contain the actual API key

  Scenario: Failed access attempts are logged
    Given an unauthorized access attempt
    When the request is rejected
    Then an audit log entry should contain:
      | field           | value                    |
      | timestamp       | ISO 8601 format          |
      | session_id      | attempted session ID     |
      | operation       | "unauthorized_access"    |
      | endpoint        | target endpoint          |
      | source_ip       | request IP (hashed)      |
```

---

## 6. OWASP TOP 10 CHECKLIST

### OWASP Top 10 2021 Analysis

| Category | Vulnerability | Applicable | Mitigated | Notes |
|----------|--------------|------------|-----------|-------|
| **A01: Broken Access Control** | Cross-session key access | Yes | Partially | Requires session ID validation on all key operations |
| | CSRF on disconnect | Yes | No | Need CSRF token implementation |
| **A02: Cryptographic Failures** | Unencrypted key storage | Yes | Yes | AES-256-GCM encryption implemented |
| | Key in error messages | Yes | Requires testing | Ensure error sanitization |
| | Weak session ID generation | Yes | Requires review | Verify CSPRNG usage |
| **A03: Injection** | API key input injection | Yes | Yes | Pydantic validation on backend |
| | Prompt injection | Yes | Partially | Prompt templates need hardening |
| **A04: Insecure Design** | No rate limiting | Yes | No | Need endpoint rate limiting |
| | No session timeout | Yes | No | Need TTL-based session cleanup |
| **A05: Security Misconfiguration** | Missing security headers | Yes | Unknown | Verify CSP, HSTS, X-Frame-Options |
| | Debug mode in production | Yes | Unknown | Verify FastAPI debug=False |
| **A06: Vulnerable Components** | Outdated dependencies | Yes | Unknown | Requires dependency audit |
| **A07: Auth Failures** | Session fixation | Yes | Unknown | Verify session rotation |
| | Weak session IDs | Yes | Requires review | Verify entropy and randomness |
| **A08: Data Integrity Failures** | Untrusted provider param | Yes | Partially | Need enum validation |
| | Untrusted model param | Yes | Partially | Need allowlist validation |
| **A09: Logging Failures** | API keys in logs | Yes | Partially | Pattern filtering needs testing |
| | Insufficient audit logging | Yes | No | Need comprehensive audit logs |
| **A10: SSRF** | GitHub URL manipulation | Yes | Partially | URL validation exists, needs review |

### Checklist Status

- [x] A01: Broken Access Control - **Partially mitigated, needs CSRF**
- [x] A02: Cryptographic Failures - **Mitigated with AES-256-GCM**
- [x] A03: Injection - **Mitigated with Pydantic/Zod**
- [ ] A04: Insecure Design - **Needs rate limiting and session timeout**
- [ ] A05: Security Misconfiguration - **Needs header verification**
- [ ] A06: Vulnerable Components - **Needs dependency audit**
- [x] A07: Auth Failures - **Partially mitigated, needs review**
- [x] A08: Data Integrity Failures - **Needs enum validation**
- [ ] A09: Logging Failures - **Needs comprehensive audit logging**
- [x] A10: SSRF - **Low risk, URL validation exists**

---

## 7. RECOMMENDED SECURITY STORIES FOR PRD

### Security User Stories to Add to prd.json

```json
[
  {
    "id": "US-SEC-001",
    "title": "Implement API Key Log Filtering",
    "description": "As a security engineer, I want API keys filtered from all logs so that credentials are never exposed in log files",
    "acceptanceCriteria": [
      "GIVEN any log statement WHEN output contains 'sk-' pattern THEN replace with '[REDACTED]'",
      "GIVEN any log statement WHEN output contains 'sk-ant-' pattern THEN replace with '[REDACTED]'",
      "GIVEN structured logging WHEN api_key field exists THEN field value is redacted",
      "pytest test_log_filtering passes with 100% coverage on logging module"
    ],
    "priority": 1,
    "complexity": 2,
    "estimatedMinutes": 30,
    "filesAffected": [
      "backend/src/utils/logging.py",
      "backend/src/middleware/request_logging.py"
    ],
    "dependencies": [],
    "testStrategy": "Unit tests that verify redaction with various key patterns and positions",
    "securityCategory": "logging"
  },
  {
    "id": "US-SEC-002",
    "title": "Implement Request Rate Limiting",
    "description": "As a system, I want to rate limit API requests so that abuse and DoS attacks are prevented",
    "acceptanceCriteria": [
      "GIVEN a session WHEN more than 100 requests/minute to auth endpoints THEN return 429",
      "GIVEN a session WHEN more than 20 requests/minute to generation endpoints THEN return 429",
      "GIVEN rate limit exceeded WHEN returning error THEN include Retry-After header",
      "Rate limiting works correctly under concurrent request load"
    ],
    "priority": 2,
    "complexity": 3,
    "estimatedMinutes": 45,
    "filesAffected": [
      "backend/src/middleware/rate_limiter.py",
      "backend/src/api/main.py"
    ],
    "dependencies": [],
    "testStrategy": "Load tests verifying rate limiting behavior under various request patterns",
    "securityCategory": "availability"
  },
  {
    "id": "US-SEC-003",
    "title": "Implement Security Headers Middleware",
    "description": "As a security engineer, I want proper security headers on all responses so that common web attacks are mitigated",
    "acceptanceCriteria": [
      "GIVEN any API response WHEN returned THEN includes Content-Security-Policy header",
      "GIVEN any API response WHEN returned THEN includes X-Content-Type-Options: nosniff",
      "GIVEN any API response WHEN returned THEN includes X-Frame-Options: DENY",
      "GIVEN any API response WHEN returned THEN includes Strict-Transport-Security header",
      "Security headers pass securityheaders.com scan"
    ],
    "priority": 2,
    "complexity": 2,
    "estimatedMinutes": 25,
    "filesAffected": [
      "backend/src/middleware/security_headers.py",
      "backend/src/api/main.py"
    ],
    "dependencies": [],
    "testStrategy": "Integration tests verifying header presence on all response types",
    "securityCategory": "configuration"
  },
  {
    "id": "US-SEC-004",
    "title": "Implement Audit Logging for Key Operations",
    "description": "As a security administrator, I want all key operations logged so that I can investigate security incidents",
    "acceptanceCriteria": [
      "GIVEN key connect operation WHEN completed THEN audit log contains session_id, timestamp, status",
      "GIVEN key disconnect operation WHEN completed THEN audit log contains session_id, timestamp",
      "GIVEN unauthorized access attempt WHEN detected THEN audit log contains full request details",
      "GIVEN audit log entry WHEN written THEN never contains actual API key",
      "Audit logs are queryable by session_id and timestamp range"
    ],
    "priority": 2,
    "complexity": 3,
    "estimatedMinutes": 40,
    "filesAffected": [
      "backend/src/services/audit_logger.py",
      "backend/src/api/openai_routes.py",
      "backend/src/api/claude_routes.py"
    ],
    "dependencies": ["US-SEC-001"],
    "testStrategy": "Unit tests verifying audit log content and redaction",
    "securityCategory": "logging"
  },
  {
    "id": "US-SEC-005",
    "title": "Implement Session Timeout and Cleanup",
    "description": "As a system, I want sessions to timeout automatically so that abandoned credentials are cleaned up",
    "acceptanceCriteria": [
      "GIVEN a session WHEN inactive for 24 hours THEN session is marked expired",
      "GIVEN an expired session WHEN any request is made THEN return 401 with 'session expired' message",
      "GIVEN an expired session WHEN cleaned up THEN encrypted keys are securely deleted",
      "Session cleanup runs as background task every hour"
    ],
    "priority": 3,
    "complexity": 3,
    "estimatedMinutes": 35,
    "filesAffected": [
      "backend/src/services/session_manager.py",
      "backend/src/tasks/cleanup.py"
    ],
    "dependencies": [],
    "testStrategy": "Unit tests for timeout logic, integration tests for cleanup task",
    "securityCategory": "authentication"
  },
  {
    "id": "US-SEC-006",
    "title": "Implement Provider and Model Parameter Validation",
    "description": "As a backend developer, I want provider and model parameters strictly validated so that only allowed values are accepted",
    "acceptanceCriteria": [
      "GIVEN provider parameter WHEN not in ['claude', 'openai'] THEN return 400 Bad Request",
      "GIVEN model parameter for OpenAI WHEN not in ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo'] THEN return 400",
      "GIVEN invalid parameter WHEN rejected THEN error message specifies allowed values",
      "Pydantic enum validation enforces allowed values"
    ],
    "priority": 1,
    "complexity": 1,
    "estimatedMinutes": 15,
    "filesAffected": [
      "backend/src/models/schemas.py",
      "backend/src/models/openai_schemas.py"
    ],
    "dependencies": ["US-001"],
    "testStrategy": "Unit tests for schema validation with valid and invalid enum values",
    "securityCategory": "validation"
  },
  {
    "id": "US-SEC-007",
    "title": "Secure Error Message Handling",
    "description": "As a user, I want error messages that help troubleshoot without exposing sensitive information",
    "acceptanceCriteria": [
      "GIVEN any 500 error WHEN returned THEN response contains generic message only",
      "GIVEN any error WHEN returned THEN never contains API key, path traces, or internal details",
      "GIVEN OpenAI API error WHEN returned THEN only safe error properties are passed through",
      "Error handling passes security review for information disclosure"
    ],
    "priority": 2,
    "complexity": 2,
    "estimatedMinutes": 25,
    "filesAffected": [
      "backend/src/api/error_handlers.py",
      "backend/src/services/openai_client.py"
    ],
    "dependencies": [],
    "testStrategy": "Unit tests triggering various error conditions and verifying sanitized output",
    "securityCategory": "validation"
  }
]
```

### Security NFRs to Add

```json
[
  {
    "id": "NFR-SEC-001",
    "title": "Rate Limiting",
    "priority": "must",
    "acceptanceCriteria": [
      "Auth endpoints limited to 100 requests/minute per session",
      "Generation endpoints limited to 20 requests/minute per session",
      "Rate limit responses include Retry-After header"
    ]
  },
  {
    "id": "NFR-SEC-002",
    "title": "Security Headers",
    "priority": "must",
    "acceptanceCriteria": [
      "All responses include CSP, X-Content-Type-Options, X-Frame-Options, HSTS headers",
      "Pass securityheaders.com basic scan"
    ]
  },
  {
    "id": "NFR-SEC-003",
    "title": "Session Security",
    "priority": "must",
    "acceptanceCriteria": [
      "Session IDs generated with 256-bit CSPRNG entropy",
      "Sessions expire after 24 hours of inactivity",
      "Expired sessions have keys securely deleted"
    ]
  },
  {
    "id": "NFR-SEC-004",
    "title": "Audit Logging",
    "priority": "should",
    "acceptanceCriteria": [
      "All key operations logged with timestamp, session_id, operation, status",
      "Unauthorized access attempts logged with full request context",
      "No API keys appear in any log output"
    ]
  }
]
```

---

## 8. SECURITY TESTING REQUIREMENTS

### Mandatory Security Tests

| Test Category | Test Description | Pass Criteria |
|---------------|-----------------|---------------|
| Log Sanitization | Attempt to log API keys in various formats | No key patterns appear in any log output |
| Session Isolation | Cross-session key access attempt | 403 Forbidden returned |
| Input Validation | Malformed API key injection | Rejected by schema validation |
| Error Disclosure | Trigger 500 errors and inspect response | No sensitive data in error |
| Rate Limiting | Exceed rate limits | 429 returned with Retry-After |
| Encryption Verification | Inspect in-memory key storage | Keys stored in encrypted form only |

### Penetration Testing Scope

1. **Session Management**
   - Session ID prediction/enumeration
   - Session fixation attacks
   - Cross-session data access

2. **API Security**
   - Input fuzzing on all endpoints
   - Parameter tampering
   - Response manipulation

3. **Information Disclosure**
   - Log file analysis
   - Error message analysis
   - Debug information leakage

---

## 9. IMPLEMENTATION CHECKLIST

### Before Launch

- [ ] All SEC-00X requirements implemented
- [ ] Security user stories completed
- [ ] Log filtering tested with real API keys
- [ ] Rate limiting load tested
- [ ] Security headers verified
- [ ] Dependency vulnerability scan (npm audit, pip-audit)
- [ ] OWASP ZAP scan completed
- [ ] Penetration testing completed
- [ ] Security review sign-off

### Monitoring Requirements

- [ ] Alert on multiple failed key validations from same session
- [ ] Alert on rate limit triggers
- [ ] Alert on unauthorized access attempts
- [ ] Weekly audit log review process defined

---

*Document generated by Security Agent - 2026-01-13*
