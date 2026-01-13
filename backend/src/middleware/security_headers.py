"""Security headers middleware for HTTP response hardening.

This module provides FastAPI middleware that adds security headers to all
HTTP responses, mitigating common web attacks like XSS, clickjacking,
and MIME-type sniffing.

Implements headers recommended by OWASP and securityheaders.com:
- Content-Security-Policy (CSP)
- X-Content-Type-Options
- X-Frame-Options
- Strict-Transport-Security (HSTS)
- Referrer-Policy
- Permissions-Policy
"""

from dataclasses import dataclass, field
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass
class SecurityHeadersConfig:
    """Configuration for security headers.

    Attributes:
        content_security_policy: CSP directives string.
        x_content_type_options: Value for X-Content-Type-Options header.
        x_frame_options: Value for X-Frame-Options header.
        strict_transport_security: HSTS header value.
        referrer_policy: Referrer-Policy header value.
        permissions_policy: Permissions-Policy header value.
        include_hsts: Whether to include HSTS header (disable for HTTP dev).
    """
    # Content Security Policy
    content_security_policy: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://api.openai.com https://api.anthropic.com https://api.github.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    # Prevent MIME type sniffing
    x_content_type_options: str = "nosniff"

    # Prevent clickjacking
    x_frame_options: str = "DENY"

    # HTTP Strict Transport Security (1 year, include subdomains, preload-ready)
    strict_transport_security: str = "max-age=31536000; includeSubDomains; preload"

    # Control referrer information
    referrer_policy: str = "strict-origin-when-cross-origin"

    # Restrict browser features/APIs
    permissions_policy: str = (
        "accelerometer=(), "
        "camera=(), "
        "geolocation=(), "
        "gyroscope=(), "
        "magnetometer=(), "
        "microphone=(), "
        "payment=(), "
        "usb=()"
    )

    # Whether to include HSTS (set False for HTTP-only development)
    include_hsts: bool = True

    # Additional custom headers (key -> value)
    custom_headers: dict = field(default_factory=dict)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that adds security headers to all responses.

    This middleware ensures all HTTP responses include security headers
    to protect against common web vulnerabilities.

    Example:
        >>> from fastapi import FastAPI
        >>> from src.middleware.security_headers import SecurityHeadersMiddleware
        >>>
        >>> app = FastAPI()
        >>> app.add_middleware(SecurityHeadersMiddleware)
    """

    def __init__(
        self,
        app,
        config: Optional[SecurityHeadersConfig] = None
    ):
        """Initialize the security headers middleware.

        Args:
            app: The FastAPI application.
            config: Optional configuration for header values.
        """
        super().__init__(app)
        self.config = config or SecurityHeadersConfig()

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            The HTTP response with security headers added.
        """
        # Process the request
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response)

        return response

    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to a response.

        Args:
            response: The HTTP response to modify.
        """
        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.config.content_security_policy

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = self.config.x_content_type_options

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = self.config.x_frame_options

        # HSTS - only include if enabled (e.g., skip for HTTP dev environments)
        if self.config.include_hsts:
            response.headers["Strict-Transport-Security"] = self.config.strict_transport_security

        # Referrer Policy
        response.headers["Referrer-Policy"] = self.config.referrer_policy

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = self.config.permissions_policy

        # Add any custom headers
        for header_name, header_value in self.config.custom_headers.items():
            response.headers[header_name] = header_value

    @staticmethod
    def get_default_config() -> SecurityHeadersConfig:
        """Get the default security headers configuration.

        Returns:
            The default SecurityHeadersConfig.
        """
        return SecurityHeadersConfig()

    @staticmethod
    def get_development_config() -> SecurityHeadersConfig:
        """Get a development-friendly configuration.

        Disables HSTS for local HTTP development while keeping
        other security headers enabled.

        Returns:
            A development-appropriate SecurityHeadersConfig.
        """
        return SecurityHeadersConfig(
            include_hsts=False,
            # More permissive CSP for development
            content_security_policy=(
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https: http:; "
                "font-src 'self' data:; "
                "connect-src 'self' http://localhost:* https://api.openai.com https://api.anthropic.com https://api.github.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        )


def create_security_headers_middleware(
    development_mode: bool = False
) -> tuple[type, dict]:
    """Create security headers middleware with appropriate configuration.

    Helper function to create middleware with proper config based on
    environment.

    Args:
        development_mode: Whether running in development mode.

    Returns:
        Tuple of (middleware_class, config_dict) for FastAPI add_middleware.

    Example:
        >>> middleware_class, config = create_security_headers_middleware(development_mode=True)
        >>> app.add_middleware(middleware_class, **config)
    """
    if development_mode:
        config = SecurityHeadersMiddleware.get_development_config()
    else:
        config = SecurityHeadersMiddleware.get_default_config()

    return SecurityHeadersMiddleware, {"config": config}
