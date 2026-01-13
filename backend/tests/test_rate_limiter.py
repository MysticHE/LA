"""Tests for rate limiting middleware.

Tests verify:
- Auth endpoints limited to 100 requests/minute
- Generation endpoints limited to 20 requests/minute
- Retry-After header included when rate limited
- Per-session isolation
- Concurrent request handling
- Endpoint classification
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from src.middleware.rate_limiter import (
    RateLimiter,
    RateLimitMiddleware,
    RateLimitConfig,
    EndpointType,
    RequestRecord,
)


# --- Unit Tests for RateLimiter ---


class TestEndpointClassification:
    """Tests for endpoint type classification."""

    def test_auth_endpoint_classification(self):
        """Auth endpoints are correctly classified."""
        assert RateLimiter.classify_endpoint("/api/auth/claude/connect") == EndpointType.AUTH
        assert RateLimiter.classify_endpoint("/api/auth/openai/status") == EndpointType.AUTH
        assert RateLimiter.classify_endpoint("/api/auth/claude/disconnect") == EndpointType.AUTH

    def test_generation_endpoint_classification(self):
        """Generation endpoints are correctly classified."""
        assert RateLimiter.classify_endpoint("/api/generate/ai-post") == EndpointType.GENERATION
        assert RateLimiter.classify_endpoint("/api/generate/test") == EndpointType.GENERATION

    def test_other_endpoint_classification(self):
        """Other endpoints are correctly classified."""
        assert RateLimiter.classify_endpoint("/api/analyze") == EndpointType.OTHER
        assert RateLimiter.classify_endpoint("/api/health") == EndpointType.OTHER
        assert RateLimiter.classify_endpoint("/") == EndpointType.OTHER

    def test_case_insensitive_classification(self):
        """Classification is case-insensitive."""
        assert RateLimiter.classify_endpoint("/API/AUTH/claude") == EndpointType.AUTH
        assert RateLimiter.classify_endpoint("/API/GENERATE/post") == EndpointType.GENERATION


class TestRateLimitConfig:
    """Tests for rate limit configuration."""

    def test_default_config(self):
        """Default config has expected values."""
        config = RateLimitConfig()
        assert config.auth_limit == 100
        assert config.auth_window_seconds == 60
        assert config.generation_limit == 20
        assert config.generation_window_seconds == 60
        assert config.other_limit == 200

    def test_custom_config(self):
        """Custom config values are applied."""
        config = RateLimitConfig(
            auth_limit=50,
            generation_limit=10,
            other_limit=100
        )
        assert config.auth_limit == 50
        assert config.generation_limit == 10
        assert config.other_limit == 100


class TestRateLimiter:
    """Tests for RateLimiter class."""

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self):
        """Requests under the limit are allowed."""
        config = RateLimitConfig(auth_limit=5, auth_window_seconds=60)
        limiter = RateLimiter(config)

        for i in range(5):
            allowed, retry_after, remaining = await limiter.is_allowed(
                "session1", EndpointType.AUTH
            )
            assert allowed is True
            assert retry_after == 0
            assert remaining == 4 - i

    @pytest.mark.asyncio
    async def test_blocks_requests_over_limit(self):
        """Requests over the limit are blocked."""
        config = RateLimitConfig(auth_limit=3, auth_window_seconds=60)
        limiter = RateLimiter(config)

        # Use up the limit
        for _ in range(3):
            await limiter.is_allowed("session1", EndpointType.AUTH)

        # Next request should be blocked
        allowed, retry_after, remaining = await limiter.is_allowed(
            "session1", EndpointType.AUTH
        )
        assert allowed is False
        assert retry_after > 0
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_retry_after_header_value(self):
        """Retry-After value is correctly calculated."""
        config = RateLimitConfig(auth_limit=1, auth_window_seconds=60)
        limiter = RateLimiter(config)

        await limiter.is_allowed("session1", EndpointType.AUTH)

        allowed, retry_after, _ = await limiter.is_allowed(
            "session1", EndpointType.AUTH
        )
        assert allowed is False
        # Retry-after should be approximately 60 seconds (the window)
        assert 55 <= retry_after <= 61

    @pytest.mark.asyncio
    async def test_session_isolation(self):
        """Different sessions have independent limits."""
        config = RateLimitConfig(auth_limit=2, auth_window_seconds=60)
        limiter = RateLimiter(config)

        # Session 1 uses up its limit
        for _ in range(2):
            await limiter.is_allowed("session1", EndpointType.AUTH)

        # Session 1 is blocked
        allowed1, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
        assert allowed1 is False

        # Session 2 should still be allowed
        allowed2, _, _ = await limiter.is_allowed("session2", EndpointType.AUTH)
        assert allowed2 is True

    @pytest.mark.asyncio
    async def test_endpoint_type_isolation(self):
        """Different endpoint types have independent limits."""
        config = RateLimitConfig(
            auth_limit=2,
            generation_limit=2,
            auth_window_seconds=60,
            generation_window_seconds=60
        )
        limiter = RateLimiter(config)

        # Use up auth limit
        for _ in range(2):
            await limiter.is_allowed("session1", EndpointType.AUTH)

        # Auth is blocked
        allowed_auth, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
        assert allowed_auth is False

        # Generation should still be allowed
        allowed_gen, _, _ = await limiter.is_allowed("session1", EndpointType.GENERATION)
        assert allowed_gen is True

    @pytest.mark.asyncio
    async def test_window_expiration(self):
        """Requests are allowed again after window expires."""
        config = RateLimitConfig(auth_limit=1, auth_window_seconds=1)
        limiter = RateLimiter(config)

        await limiter.is_allowed("session1", EndpointType.AUTH)

        # Should be blocked
        allowed1, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
        assert allowed1 is False

        # Wait for window to expire
        await asyncio.sleep(1.1)

        # Should be allowed again
        allowed2, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
        assert allowed2 is True

    @pytest.mark.asyncio
    async def test_reset_specific_session(self):
        """Reset clears limits for a specific session."""
        limiter = RateLimiter(RateLimitConfig(auth_limit=1))

        await limiter.is_allowed("session1", EndpointType.AUTH)
        await limiter.is_allowed("session2", EndpointType.AUTH)

        # Both should be blocked
        blocked1, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
        blocked2, _, _ = await limiter.is_allowed("session2", EndpointType.AUTH)
        assert blocked1 is False
        assert blocked2 is False

        # Reset only session1
        limiter.reset("session1")

        # Session1 allowed, session2 still blocked
        allowed1, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
        still_blocked2, _, _ = await limiter.is_allowed("session2", EndpointType.AUTH)
        assert allowed1 is True
        assert still_blocked2 is False

    @pytest.mark.asyncio
    async def test_reset_all_sessions(self):
        """Reset without session ID clears all limits."""
        limiter = RateLimiter(RateLimitConfig(auth_limit=1))

        await limiter.is_allowed("session1", EndpointType.AUTH)
        await limiter.is_allowed("session2", EndpointType.AUTH)

        limiter.reset()

        # Both should be allowed again
        allowed1, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
        allowed2, _, _ = await limiter.is_allowed("session2", EndpointType.AUTH)
        assert allowed1 is True
        assert allowed2 is True

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Rate limiter handles concurrent requests correctly."""
        config = RateLimitConfig(auth_limit=5, auth_window_seconds=60)
        limiter = RateLimiter(config)

        # Send 10 concurrent requests
        async def make_request():
            return await limiter.is_allowed("session1", EndpointType.AUTH)

        results = await asyncio.gather(*[make_request() for _ in range(10)])

        # Exactly 5 should be allowed
        allowed_count = sum(1 for allowed, _, _ in results if allowed)
        assert allowed_count == 5

    @pytest.mark.asyncio
    async def test_auth_limit_100_per_minute(self):
        """Auth endpoints have 100 requests/minute limit."""
        config = RateLimitConfig()  # Default config
        limiter = RateLimiter(config)

        # Make 100 requests
        for _ in range(100):
            allowed, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
            assert allowed is True

        # 101st request should be blocked
        allowed, retry_after, _ = await limiter.is_allowed(
            "session1", EndpointType.AUTH
        )
        assert allowed is False
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_generation_limit_20_per_minute(self):
        """Generation endpoints have 20 requests/minute limit."""
        config = RateLimitConfig()  # Default config
        limiter = RateLimiter(config)

        # Make 20 requests
        for _ in range(20):
            allowed, _, _ = await limiter.is_allowed("session1", EndpointType.GENERATION)
            assert allowed is True

        # 21st request should be blocked
        allowed, retry_after, _ = await limiter.is_allowed(
            "session1", EndpointType.GENERATION
        )
        assert allowed is False
        assert retry_after > 0


# --- Integration Tests with FastAPI ---


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware integration."""

    @pytest.fixture
    def app_with_rate_limit(self):
        """Create a FastAPI app with rate limiting."""
        app = FastAPI()
        config = RateLimitConfig(auth_limit=3, generation_limit=2)
        app.add_middleware(RateLimitMiddleware, config=config)

        @app.get("/api/auth/test")
        async def auth_test():
            return {"status": "ok"}

        @app.post("/api/generate/test")
        async def generate_test():
            return {"status": "ok"}

        @app.get("/api/health")
        async def health():
            return {"status": "healthy"}

        return app

    @pytest.fixture
    def client(self, app_with_rate_limit):
        """Create test client."""
        return TestClient(app_with_rate_limit)

    def test_allows_requests_under_limit(self, client):
        """Requests under limit return 200."""
        for _ in range(3):
            response = client.get(
                "/api/auth/test",
                headers={"X-Session-ID": "test-session"}
            )
            assert response.status_code == 200

    def test_returns_429_when_exceeded(self, client):
        """Returns 429 when rate limit exceeded."""
        # Use up the limit
        for _ in range(3):
            client.get(
                "/api/auth/test",
                headers={"X-Session-ID": "test-session"}
            )

        # Next request should be 429
        response = client.get(
            "/api/auth/test",
            headers={"X-Session-ID": "test-session"}
        )
        assert response.status_code == 429

    def test_includes_retry_after_header(self, client):
        """429 response includes Retry-After header."""
        # Use up the limit
        for _ in range(3):
            client.get(
                "/api/auth/test",
                headers={"X-Session-ID": "test-session"}
            )

        response = client.get(
            "/api/auth/test",
            headers={"X-Session-ID": "test-session"}
        )

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        retry_after = int(response.headers["Retry-After"])
        assert retry_after > 0

    def test_includes_rate_limit_headers_on_success(self, client):
        """Successful responses include rate limit headers."""
        response = client.get(
            "/api/auth/test",
            headers={"X-Session-ID": "test-session"}
        )

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Window" in response.headers

    def test_generation_endpoint_separate_limit(self, client):
        """Generation endpoints have separate limit from auth."""
        # Use up auth limit
        for _ in range(3):
            client.get(
                "/api/auth/test",
                headers={"X-Session-ID": "test-session"}
            )

        # Auth is blocked
        auth_response = client.get(
            "/api/auth/test",
            headers={"X-Session-ID": "test-session"}
        )
        assert auth_response.status_code == 429

        # Generation should still work
        gen_response = client.post(
            "/api/generate/test",
            headers={"X-Session-ID": "test-session"}
        )
        assert gen_response.status_code == 200

    def test_session_isolation_via_header(self, client):
        """Different X-Session-ID headers have independent limits."""
        # Use up limit for session1
        for _ in range(3):
            client.get(
                "/api/auth/test",
                headers={"X-Session-ID": "session1"}
            )

        # Session1 is blocked
        r1 = client.get(
            "/api/auth/test",
            headers={"X-Session-ID": "session1"}
        )
        assert r1.status_code == 429

        # Session2 should be allowed
        r2 = client.get(
            "/api/auth/test",
            headers={"X-Session-ID": "session2"}
        )
        assert r2.status_code == 200

    def test_uses_ip_when_no_session_header(self, client):
        """Uses IP address when X-Session-ID not provided."""
        # This should work (first request from IP)
        response = client.get("/api/auth/test")
        assert response.status_code == 200

    def test_error_response_format(self, client):
        """429 response has proper error format."""
        # Use up the limit
        for _ in range(3):
            client.get(
                "/api/auth/test",
                headers={"X-Session-ID": "test-session"}
            )

        response = client.get(
            "/api/auth/test",
            headers={"X-Session-ID": "test-session"}
        )

        assert response.status_code == 429
        data = response.json()
        assert "detail" in data
        assert "retry_after" in data
        assert data["retry_after"] > 0


# --- Load/Stress Tests ---


class TestConcurrentLoad:
    """Tests for concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_from_same_session(self):
        """Handles concurrent requests from same session correctly."""
        config = RateLimitConfig(auth_limit=50, auth_window_seconds=60)
        limiter = RateLimiter(config)

        # Send 100 concurrent requests from same session
        async def make_request():
            return await limiter.is_allowed("session1", EndpointType.AUTH)

        results = await asyncio.gather(*[make_request() for _ in range(100)])

        # Exactly 50 should be allowed
        allowed_count = sum(1 for allowed, _, _ in results if allowed)
        assert allowed_count == 50

        # And 50 should be blocked
        blocked_count = sum(1 for allowed, _, _ in results if not allowed)
        assert blocked_count == 50

    @pytest.mark.asyncio
    async def test_concurrent_requests_from_multiple_sessions(self):
        """Handles concurrent requests from multiple sessions correctly."""
        config = RateLimitConfig(auth_limit=5, auth_window_seconds=60)
        limiter = RateLimiter(config)

        async def make_requests_for_session(session_id: str, count: int):
            results = []
            for _ in range(count):
                result = await limiter.is_allowed(session_id, EndpointType.AUTH)
                results.append(result)
            return session_id, results

        # 10 sessions, 10 requests each
        tasks = [
            make_requests_for_session(f"session{i}", 10)
            for i in range(10)
        ]
        all_results = await asyncio.gather(*tasks)

        # Each session should have exactly 5 allowed
        for session_id, results in all_results:
            allowed_count = sum(1 for allowed, _, _ in results if allowed)
            assert allowed_count == 5, f"Session {session_id} had {allowed_count} allowed"


# --- Edge Cases ---


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_session_id(self):
        """Handles empty session ID."""
        limiter = RateLimiter(RateLimitConfig(auth_limit=1))

        # Empty string should work as a valid session
        allowed, _, _ = await limiter.is_allowed("", EndpointType.AUTH)
        assert allowed is True

        # And be rate limited
        allowed2, _, _ = await limiter.is_allowed("", EndpointType.AUTH)
        assert allowed2 is False

    @pytest.mark.asyncio
    async def test_very_long_session_id(self):
        """Handles very long session IDs."""
        limiter = RateLimiter(RateLimitConfig(auth_limit=1))

        long_session = "x" * 10000
        allowed, _, _ = await limiter.is_allowed(long_session, EndpointType.AUTH)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_special_characters_in_session_id(self):
        """Handles special characters in session IDs."""
        limiter = RateLimiter(RateLimitConfig(auth_limit=1))

        special_session = "session/with:special@chars!#$%"
        allowed, _, _ = await limiter.is_allowed(special_session, EndpointType.AUTH)
        assert allowed is True

    def test_endpoint_classification_empty_path(self):
        """Handles empty path classification."""
        endpoint_type = RateLimiter.classify_endpoint("")
        assert endpoint_type == EndpointType.OTHER

    def test_endpoint_classification_partial_match(self):
        """Partial matches are classified correctly."""
        # "auth" in path but not "/auth/"
        assert RateLimiter.classify_endpoint("/api/authenticate") == EndpointType.OTHER
        # Contains "auth/" but different context
        assert RateLimiter.classify_endpoint("/api/auth/something") == EndpointType.AUTH

    @pytest.mark.asyncio
    async def test_limit_of_zero(self):
        """Zero limit blocks all requests."""
        config = RateLimitConfig(auth_limit=0)
        limiter = RateLimiter(config)

        allowed, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
        assert allowed is False

    @pytest.mark.asyncio
    async def test_very_short_window(self):
        """Very short window works correctly."""
        config = RateLimitConfig(auth_limit=1, auth_window_seconds=1)
        limiter = RateLimiter(config)

        await limiter.is_allowed("session1", EndpointType.AUTH)

        # Blocked immediately
        allowed1, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
        assert allowed1 is False

        # Wait for window
        await asyncio.sleep(1.1)

        # Allowed again
        allowed2, _, _ = await limiter.is_allowed("session1", EndpointType.AUTH)
        assert allowed2 is True
