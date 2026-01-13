"""Session validation middleware.

This module provides middleware for:
- Session expiry detection
- Returning 401 for expired sessions
- Automatic session activity tracking

Implements SEC-013 requirements for session security.
"""

import logging
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from src.services.session_manager import get_session_manager, SessionManager


logger = logging.getLogger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware for session validation and expiry handling.

    Checks if the session specified in X-Session-ID header is expired
    and returns 401 if so. Also updates session activity on each request.

    Paths that don't require session validation (public paths) can be
    configured via the exclude_paths parameter.
    """

    def __init__(
        self,
        app,
        session_manager: Optional[SessionManager] = None,
        exclude_paths: Optional[list] = None
    ):
        """Initialize the session middleware.

        Args:
            app: The FastAPI/Starlette app.
            session_manager: Optional SessionManager instance.
            exclude_paths: List of path prefixes to exclude from validation.
        """
        super().__init__(app)
        self._session_manager = session_manager or get_session_manager()
        self._exclude_paths = exclude_paths or [
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/health",
        ]

    def _should_validate_session(self, request: Request) -> bool:
        """Check if the request path requires session validation.

        Args:
            request: The incoming request.

        Returns:
            True if session should be validated.
        """
        path = request.url.path

        # Exclude specific paths
        for excluded in self._exclude_paths:
            if path == excluded or path.startswith(excluded + "/"):
                return True  # Return True but no validation will happen (no session)

        return True

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request with session validation.

        Args:
            request: The incoming request.
            call_next: The next middleware/handler.

        Returns:
            The response, or 401 if session is expired.
        """
        # Check if path is excluded
        path = request.url.path
        for excluded in self._exclude_paths:
            if path == excluded or path.startswith(excluded + "/"):
                return await call_next(request)

        # Get session ID from header
        session_id = request.headers.get("X-Session-ID")

        # If no session ID, let the request through (routes will handle auth)
        if not session_id:
            return await call_next(request)

        # Check if session exists and is expired
        if self._session_manager.session_exists(session_id):
            if self._session_manager.is_session_expired(session_id):
                logger.warning(f"Expired session attempted access: {session_id[:8]}...")
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Session expired. Please reconnect your API key."
                    }
                )

            # Update session activity
            self._session_manager.touch_session(session_id)
        else:
            # Session doesn't exist - create it
            self._session_manager.create_session(session_id)

        return await call_next(request)


def create_session_middleware(
    session_manager: Optional[SessionManager] = None,
    exclude_paths: Optional[list] = None
) -> type:
    """Factory function to create a configured SessionMiddleware class.

    Args:
        session_manager: Optional SessionManager instance.
        exclude_paths: List of paths to exclude from session validation.

    Returns:
        A configured middleware class.
    """
    class ConfiguredSessionMiddleware(SessionMiddleware):
        def __init__(self, app):
            super().__init__(
                app,
                session_manager=session_manager,
                exclude_paths=exclude_paths
            )

    return ConfiguredSessionMiddleware
