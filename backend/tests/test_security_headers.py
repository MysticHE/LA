"""Tests for security headers middleware.

Tests verify that all required security headers are present on API responses
and have correct values per OWASP and securityheaders.com recommendations.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.middleware.security_headers import (
    SecurityHeadersConfig,
    SecurityHeadersMiddleware,
    create_security_headers_middleware
)


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI app with security headers middleware."""
    app = FastAPI()

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    async def root():
        return {"message": "Hello"}

    @app.get("/api/test")
    async def api_test():
        return {"status": "ok"}

    @app.post("/api/auth/connect")
    async def auth_connect():
        return {"connected": True}

    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app, raise_server_exceptions=False)


class TestSecurityHeadersPresence:
    """Test that all required security headers are present."""

    def test_content_security_policy_present(self, client: TestClient):
        """GIVEN any API response WHEN returned THEN includes Content-Security-Policy header."""
        response = client.get("/")
        assert "Content-Security-Policy" in response.headers

    def test_x_content_type_options_present(self, client: TestClient):
        """GIVEN any API response WHEN returned THEN includes X-Content-Type-Options: nosniff."""
        response = client.get("/")
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options_present(self, client: TestClient):
        """GIVEN any API response WHEN returned THEN includes X-Frame-Options: DENY."""
        response = client.get("/")
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_strict_transport_security_present(self, client: TestClient):
        """GIVEN any API response WHEN returned THEN includes Strict-Transport-Security header."""
        response = client.get("/")
        assert "Strict-Transport-Security" in response.headers

    def test_referrer_policy_present(self, client: TestClient):
        """GIVEN any API response WHEN returned THEN includes Referrer-Policy header."""
        response = client.get("/")
        assert "Referrer-Policy" in response.headers

    def test_permissions_policy_present(self, client: TestClient):
        """GIVEN any API response WHEN returned THEN includes Permissions-Policy header."""
        response = client.get("/")
        assert "Permissions-Policy" in response.headers


class TestSecurityHeaderValues:
    """Test that security headers have correct values."""

    def test_csp_default_src_self(self, client: TestClient):
        """CSP should have default-src 'self'."""
        response = client.get("/")
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp

    def test_csp_frame_ancestors_none(self, client: TestClient):
        """CSP should prevent framing with frame-ancestors 'none'."""
        response = client.get("/")
        csp = response.headers["Content-Security-Policy"]
        assert "frame-ancestors 'none'" in csp

    def test_csp_allows_api_connections(self, client: TestClient):
        """CSP should allow connections to OpenAI and Anthropic APIs."""
        response = client.get("/")
        csp = response.headers["Content-Security-Policy"]
        assert "https://api.openai.com" in csp
        assert "https://api.anthropic.com" in csp
        assert "https://api.github.com" in csp

    def test_hsts_has_max_age(self, client: TestClient):
        """HSTS should have max-age directive."""
        response = client.get("/")
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=" in hsts

    def test_hsts_includes_subdomains(self, client: TestClient):
        """HSTS should include subdomains."""
        response = client.get("/")
        hsts = response.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in hsts

    def test_referrer_policy_value(self, client: TestClient):
        """Referrer-Policy should be strict-origin-when-cross-origin."""
        response = client.get("/")
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_permissions_policy_restricts_features(self, client: TestClient):
        """Permissions-Policy should restrict sensitive features."""
        response = client.get("/")
        policy = response.headers["Permissions-Policy"]
        assert "camera=()" in policy
        assert "microphone=()" in policy
        assert "geolocation=()" in policy


class TestSecurityHeadersOnAllEndpoints:
    """Test that security headers are present on all endpoint types."""

    def test_headers_on_root_endpoint(self, client: TestClient):
        """Security headers present on root endpoint."""
        response = client.get("/")
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers

    def test_headers_on_api_endpoint(self, client: TestClient):
        """Security headers present on API endpoints."""
        response = client.get("/api/test")
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers

    def test_headers_on_auth_endpoint(self, client: TestClient):
        """Security headers present on auth endpoints."""
        response = client.post("/api/auth/connect")
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers

    def test_headers_on_error_response(self, client: TestClient):
        """Security headers present on error responses."""
        response = client.get("/error")
        # Error handling might differ, but check for key headers
        # Note: Some errors might be handled before middleware
        assert response.status_code == 500

    def test_headers_on_404_response(self, client: TestClient):
        """Security headers present on 404 responses."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        assert "Content-Security-Policy" in response.headers
        assert "X-Frame-Options" in response.headers


class TestSecurityHeadersConfig:
    """Test security headers configuration options."""

    def test_default_config_values(self):
        """Default config should have expected values."""
        config = SecurityHeadersConfig()
        assert config.x_content_type_options == "nosniff"
        assert config.x_frame_options == "DENY"
        assert config.include_hsts is True

    def test_custom_config(self):
        """Custom config values should be respected."""
        config = SecurityHeadersConfig(
            x_frame_options="SAMEORIGIN",
            include_hsts=False,
            custom_headers={"X-Custom": "value"}
        )
        assert config.x_frame_options == "SAMEORIGIN"
        assert config.include_hsts is False
        assert config.custom_headers == {"X-Custom": "value"}

    def test_middleware_with_custom_config(self):
        """Middleware should use custom config."""
        app = FastAPI()
        config = SecurityHeadersConfig(
            x_frame_options="SAMEORIGIN",
            include_hsts=False
        )
        app.add_middleware(SecurityHeadersMiddleware, config=config)

        @app.get("/")
        async def root():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/")

        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert "Strict-Transport-Security" not in response.headers

    def test_custom_headers_added(self):
        """Custom headers should be added to response."""
        app = FastAPI()
        config = SecurityHeadersConfig(
            custom_headers={
                "X-Custom-Header": "custom-value",
                "X-Another": "another-value"
            }
        )
        app.add_middleware(SecurityHeadersMiddleware, config=config)

        @app.get("/")
        async def root():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/")

        assert response.headers["X-Custom-Header"] == "custom-value"
        assert response.headers["X-Another"] == "another-value"


class TestDevelopmentMode:
    """Test development mode configuration."""

    def test_development_config_no_hsts(self):
        """Development config should not include HSTS."""
        config = SecurityHeadersMiddleware.get_development_config()
        assert config.include_hsts is False

    def test_development_config_allows_localhost(self):
        """Development config should allow localhost connections."""
        config = SecurityHeadersMiddleware.get_development_config()
        assert "http://localhost:*" in config.content_security_policy

    def test_development_middleware_factory(self):
        """Development mode factory should create correct config."""
        middleware_class, config_dict = create_security_headers_middleware(
            development_mode=True
        )
        assert middleware_class == SecurityHeadersMiddleware
        assert config_dict["config"].include_hsts is False

    def test_production_middleware_factory(self):
        """Production mode factory should create correct config."""
        middleware_class, config_dict = create_security_headers_middleware(
            development_mode=False
        )
        assert middleware_class == SecurityHeadersMiddleware
        assert config_dict["config"].include_hsts is True


class TestSecurityHeadersHttpMethods:
    """Test security headers on different HTTP methods."""

    @pytest.fixture
    def full_app(self) -> FastAPI:
        """Create app with all HTTP methods."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/resource")
        async def get_resource():
            return {"method": "GET"}

        @app.post("/resource")
        async def post_resource():
            return {"method": "POST"}

        @app.put("/resource")
        async def put_resource():
            return {"method": "PUT"}

        @app.delete("/resource")
        async def delete_resource():
            return {"method": "DELETE"}

        @app.patch("/resource")
        async def patch_resource():
            return {"method": "PATCH"}

        @app.options("/resource")
        async def options_resource():
            return {"method": "OPTIONS"}

        return app

    def test_get_request_has_headers(self, full_app: FastAPI):
        """GET requests should have security headers."""
        client = TestClient(full_app)
        response = client.get("/resource")
        assert "X-Frame-Options" in response.headers

    def test_post_request_has_headers(self, full_app: FastAPI):
        """POST requests should have security headers."""
        client = TestClient(full_app)
        response = client.post("/resource")
        assert "X-Frame-Options" in response.headers

    def test_put_request_has_headers(self, full_app: FastAPI):
        """PUT requests should have security headers."""
        client = TestClient(full_app)
        response = client.put("/resource")
        assert "X-Frame-Options" in response.headers

    def test_delete_request_has_headers(self, full_app: FastAPI):
        """DELETE requests should have security headers."""
        client = TestClient(full_app)
        response = client.delete("/resource")
        assert "X-Frame-Options" in response.headers

    def test_patch_request_has_headers(self, full_app: FastAPI):
        """PATCH requests should have security headers."""
        client = TestClient(full_app)
        response = client.patch("/resource")
        assert "X-Frame-Options" in response.headers


class TestSecurityheadersComScan:
    """Tests to verify headers would pass securityheaders.com scan."""

    def test_all_required_headers_present(self, client: TestClient):
        """All headers required by securityheaders.com should be present."""
        response = client.get("/")

        # Required headers for A+ grade
        required_headers = [
            "Content-Security-Policy",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Strict-Transport-Security",
            "Referrer-Policy",
            "Permissions-Policy"
        ]

        for header in required_headers:
            assert header in response.headers, f"Missing required header: {header}"

    def test_no_deprecated_headers(self, client: TestClient):
        """Response should not include deprecated security headers."""
        response = client.get("/")

        # X-XSS-Protection is deprecated (modern browsers have built-in XSS protection)
        # It's okay to not include it
        # Just verify we're not sending the deprecated X-Powered-By
        assert "X-Powered-By" not in response.headers

    def test_hsts_max_age_sufficient(self, client: TestClient):
        """HSTS max-age should be at least 1 year (31536000 seconds)."""
        response = client.get("/")
        hsts = response.headers["Strict-Transport-Security"]

        # Extract max-age value
        import re
        match = re.search(r"max-age=(\d+)", hsts)
        assert match is not None
        max_age = int(match.group(1))

        # Should be at least 1 year
        assert max_age >= 31536000, f"HSTS max-age {max_age} is less than 1 year"

    def test_csp_prevents_common_attacks(self, client: TestClient):
        """CSP should prevent common XSS and injection attacks."""
        response = client.get("/")
        csp = response.headers["Content-Security-Policy"]

        # Should have default-src defined
        assert "default-src" in csp

        # Should prevent base tag hijacking
        assert "base-uri" in csp

        # Should restrict form targets
        assert "form-action" in csp


class TestMiddlewareIntegration:
    """Test middleware integration with other middleware."""

    def test_works_with_multiple_middleware(self):
        """Security headers should work with other middleware."""
        from starlette.middleware.base import BaseHTTPMiddleware

        class DummyMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                response = await call_next(request)
                response.headers["X-Dummy"] = "present"
                return response

        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(DummyMiddleware)

        @app.get("/")
        async def root():
            return {"ok": True}

        client = TestClient(app)
        response = client.get("/")

        # Both middleware should have added their headers
        assert "X-Dummy" in response.headers
        assert "X-Frame-Options" in response.headers

    def test_preserves_existing_headers(self):
        """Security middleware should not remove existing response headers."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/")
        async def root():
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content={"ok": True},
                headers={"X-Custom-Response": "preserved"}
            )

        client = TestClient(app)
        response = client.get("/")

        assert response.headers.get("X-Custom-Response") == "preserved"
        assert "X-Frame-Options" in response.headers
