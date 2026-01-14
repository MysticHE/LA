# Ralph Agent Memory

> This file is automatically updated by Ralph during iterations.
> It persists learnings across sessions to prevent repeated mistakes.
> **READ THIS FILE FIRST** before starting any implementation.

## 🧠 Learned Patterns

<!-- Patterns discovered that MUST be followed -->
<!-- Format: [PATTERN-XXX] Description -->

[PATTERN-001] Mock SDK classes at their import location in the module, not at the SDK source
- Example: Use `patch('src.services.openai_client.OpenAI')` NOT `patch('openai.OpenAI')`
- This applies to all SDK mocking (anthropic, openai, etc.)

[PATTERN-002] Follow ClaudeClient pattern for new AI provider clients
- Use dataclass GenerationResult with success, content, error, retry_after fields
- Handle AuthenticationError, RateLimitError, PermissionDeniedError, APIConnectionError, BadRequestError
- Extract retry-after header from RateLimitError response

[PATTERN-003] Pydantic field_validator for input size validation
- Use len(v.encode("utf-8")) for byte-accurate size checking (handles multi-byte unicode)
- Strip whitespace before validation to avoid misleading size counts
- Return None instead of empty string for optional fields

## ⚠️ Known Pitfalls

<!-- Errors encountered and how to avoid them -->
<!-- Format: [PITFALL-XXX] Error | Solution -->

[PITFALL-001] OpenAI SDK mock failing with AuthenticationError | Mock at module import path, not SDK path

[PITFALL-002] Python 3.14 LogRecord constructor KeyError with dict args | Set record.args after construction, not in constructor

## 🔧 Project-Specific Conventions

<!-- Discovered conventions from this codebase -->

- Backend tests are in backend/tests/test_*.py
- Services are in backend/src/services/
- Models/schemas are in backend/src/models/
- TypeScript check: `cd frontend && npx tsc --noEmit`
- Backend tests: `cd backend && python -m pytest tests/ -v`

## 📁 Key Files Map

<!-- Important files discovered during iterations -->

- backend/src/services/claude_client.py - Claude AI client (reference pattern)
- backend/src/services/openai_client.py - OpenAI AI client
- backend/src/models/openai_schemas.py - OpenAI Pydantic schemas
- backend/src/models/schemas.py - Shared schemas (PostStyle, AnalysisResult)
- backend/src/utils/logging.py - Secure logging with API key redaction
- backend/src/middleware/request_logging.py - Request logging middleware
- backend/src/validators/prompt_validator.py - Prompt injection validation
- backend/src/api/image_routes.py - Image generation endpoints

## 🧪 Testing Patterns

<!-- What testing approaches work in this project -->

- Use `patch('src.services.<module>.<Class>')` for SDK mocking
- Create MagicMock response objects with expected attributes
- Test all error types: auth, rate limit, permission, connection, bad request, generic

## 🚫 Do NOT Do

<!-- Explicit anti-patterns that caused failures -->

- Do NOT mock at SDK source path (e.g., `patch('openai.OpenAI')`)
- Do NOT forget to mock the response structure (choices, message, content)

---

*Last Updated: 2026-01-14T17:50:28.001148*
*Patterns Learned: 3 | Pitfalls Documented: 2*
