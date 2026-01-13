"""Request logging middleware with API key redaction.

This module provides FastAPI middleware that logs HTTP requests and responses
while ensuring sensitive data like API keys is redacted.
"""

import time
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.utils.logging import get_secure_logger, redact_api_keys, redact_dict_values


logger = get_secure_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs HTTP requests with redacted sensitive data."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log with redaction.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            The HTTP response.
        """
        start_time = time.time()

        # Log request (with redaction)
        request_info = self._get_request_info(request)
        logger.info("Request: %s %s", request.method, redact_api_keys(str(request.url)))

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            "Response: %s %s - %d (%.3fs)",
            request.method,
            redact_api_keys(str(request.url)),
            response.status_code,
            duration
        )

        return response

    def _get_request_info(self, request: Request) -> dict:
        """Extract request info for logging, with sensitive data redacted.

        Args:
            request: The HTTP request.

        Returns:
            Dictionary with redacted request information.
        """
        info = {
            "method": request.method,
            "url": redact_api_keys(str(request.url)),
            "path": request.url.path,
            "query_params": dict(request.query_params),
        }

        # Redact any sensitive query parameters
        info["query_params"] = redact_dict_values(info["query_params"])

        return info


def log_request_body(body: dict) -> dict:
    """Log a request body with redacted sensitive data.

    Use this function to safely log request bodies that may contain
    API keys or other sensitive information.

    Args:
        body: The request body dictionary.

    Returns:
        The redacted body dictionary.
    """
    return redact_dict_values(body)


def log_message(message: str) -> str:
    """Safely log a message with redacted API keys.

    Args:
        message: The message to log.

    Returns:
        The redacted message.
    """
    return redact_api_keys(message)
