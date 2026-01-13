"""Secure error handling for the API.

This module provides centralized error handling that:
1. Returns generic messages for 500 errors
2. Never exposes API keys, path traces, or internal details
3. Sanitizes OpenAI API error responses
4. Passes security review for information disclosure
"""

import re
import logging
from typing import Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger(__name__)

# Patterns that should never appear in error responses
SENSITIVE_PATTERNS = [
    # API keys
    r'sk-[A-Za-z0-9]{20,}',
    r'sk-ant-[A-Za-z0-9\-]{20,}',
    # File paths
    r'[A-Za-z]:\\[^"\']+',  # Windows paths
    r'/(?:home|Users|var|tmp|etc)/[^\s"\']+',  # Unix paths
    # Stack trace indicators
    r'File "[^"]+", line \d+',
    r'Traceback \(most recent call last\)',
    # Module paths
    r'(?:site-packages|dist-packages)/[^\s"\']+',
]

# Compiled patterns for performance
_COMPILED_PATTERNS = [re.compile(p) for p in SENSITIVE_PATTERNS]


def sanitize_error_message(message: str) -> str:
    """Remove sensitive information from error messages.

    Args:
        message: The error message to sanitize.

    Returns:
        Sanitized error message with sensitive info redacted.
    """
    if not message:
        return message

    sanitized = message

    # Apply all sensitive pattern redactions
    for pattern in _COMPILED_PATTERNS:
        sanitized = pattern.sub('[REDACTED]', sanitized)

    return sanitized


def is_safe_error_detail(detail: Any) -> bool:
    """Check if error detail is safe to expose.

    Args:
        detail: The error detail to check.

    Returns:
        True if safe to expose, False otherwise.
    """
    if detail is None:
        return True

    detail_str = str(detail)

    # Check for any sensitive patterns
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(detail_str):
            return False

    return True


def create_safe_error_response(
    status_code: int,
    detail: Optional[str] = None,
    default_message: Optional[str] = None
) -> dict:
    """Create a safe error response that doesn't leak sensitive info.

    Args:
        status_code: HTTP status code.
        detail: Original error detail (will be sanitized).
        default_message: Default message if detail is unsafe.

    Returns:
        Safe error response dictionary.
    """
    # Generic messages for server errors
    GENERIC_MESSAGES = {
        500: "An internal server error occurred. Please try again later.",
        502: "Bad gateway. Please try again later.",
        503: "Service temporarily unavailable. Please try again later.",
        504: "Gateway timeout. Please try again later.",
    }

    # For 5xx errors, always use generic message
    if status_code >= 500:
        return {
            "detail": GENERIC_MESSAGES.get(status_code, GENERIC_MESSAGES[500])
        }

    # For client errors, sanitize the detail
    if detail:
        sanitized = sanitize_error_message(str(detail))
        # If sanitization changed the message significantly (redacted content), use default
        if '[REDACTED]' in sanitized:
            return {"detail": default_message or "An error occurred processing your request."}
        return {"detail": sanitized}

    return {"detail": default_message or "An error occurred."}


def register_error_handlers(app: FastAPI) -> None:
    """Register secure error handlers on the FastAPI app.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions with secure responses."""
        response = create_safe_error_response(
            status_code=exc.status_code,
            detail=exc.detail,
            default_message="Request failed."
        )

        # Preserve headers if present (e.g., Retry-After)
        headers = getattr(exc, 'headers', None) or {}

        # Log the original error for debugging (will be redacted by logging filter)
        if exc.status_code >= 500:
            logger.error(f"HTTP {exc.status_code}: {exc.detail}")

        return JSONResponse(
            status_code=exc.status_code,
            content=response,
            headers=headers
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle validation errors with secure, user-friendly responses."""
        # Extract field-level errors without exposing internal structure
        errors = []
        for error in exc.errors():
            loc = error.get("loc", [])
            msg = error.get("msg", "Invalid value")

            # Build a safe location string (just field name, not full path)
            field = loc[-1] if loc else "unknown"

            # Sanitize the error message
            safe_msg = sanitize_error_message(str(msg))

            errors.append({
                "field": str(field),
                "message": safe_msg
            })

        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": errors
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all uncaught exceptions with a generic message.

        NEVER expose the actual exception message to users.
        """
        # Log the actual error for debugging (will be redacted by logging filter)
        logger.exception(f"Unhandled exception: {type(exc).__name__}")

        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred. Please try again later."
            }
        )


def sanitize_openai_error(error_message: str) -> str:
    """Sanitize OpenAI API error messages for safe exposure.

    Only passes through known safe error types.

    Args:
        error_message: The original OpenAI error message.

    Returns:
        Safe error message.
    """
    # Known safe error patterns to pass through
    SAFE_ERROR_PATTERNS = {
        "authentication": "Invalid API key. Please reconnect with a valid OpenAI API key.",
        "rate_limit": "Rate limit exceeded. Please try again later.",
        "quota": "API quota exceeded. Please check your OpenAI billing settings.",
        "invalid_request": "Invalid request to OpenAI API. Please try again.",
        "permission": "API key does not have permission to perform this action.",
        "connection": "Could not connect to OpenAI API. Please check your network connection.",
    }

    error_lower = error_message.lower() if error_message else ""

    # Map to safe messages based on error type keywords
    if "authentication" in error_lower or "invalid api key" in error_lower:
        return SAFE_ERROR_PATTERNS["authentication"]

    if "rate limit" in error_lower or "rate_limit" in error_lower:
        return SAFE_ERROR_PATTERNS["rate_limit"]

    if "quota" in error_lower or "billing" in error_lower or "exceeded" in error_lower:
        return SAFE_ERROR_PATTERNS["quota"]

    if "permission" in error_lower or "forbidden" in error_lower:
        return SAFE_ERROR_PATTERNS["permission"]

    if "connection" in error_lower or "network" in error_lower:
        return SAFE_ERROR_PATTERNS["connection"]

    # Default: generic safe message
    return "Failed to process request. Please try again."


def sanitize_anthropic_error(error_message: str) -> str:
    """Sanitize Anthropic (Claude) API error messages for safe exposure.

    Args:
        error_message: The original Anthropic error message.

    Returns:
        Safe error message.
    """
    # Known safe error patterns to pass through
    SAFE_ERROR_PATTERNS = {
        "authentication": "Invalid API key. Please reconnect with a valid Claude API key.",
        "rate_limit": "Rate limit exceeded. Please try again later.",
        "permission": "API key does not have permission to perform this action.",
        "connection": "Could not connect to Claude API. Please check your network connection.",
    }

    error_lower = error_message.lower() if error_message else ""

    if "authentication" in error_lower or "invalid api key" in error_lower:
        return SAFE_ERROR_PATTERNS["authentication"]

    if "rate limit" in error_lower or "rate_limit" in error_lower:
        return SAFE_ERROR_PATTERNS["rate_limit"]

    if "permission" in error_lower or "forbidden" in error_lower:
        return SAFE_ERROR_PATTERNS["permission"]

    if "connection" in error_lower or "network" in error_lower:
        return SAFE_ERROR_PATTERNS["connection"]

    # Default: generic safe message
    return "Failed to process request. Please try again."
