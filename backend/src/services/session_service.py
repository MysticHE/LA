"""Session service for secure session management.

This module provides session lifecycle management with secure cookies:
- Session creation with HttpOnly, Secure, SameSite=Strict cookie flags
- Session validation and 401 for expired sessions
- Secure key deletion on session disconnect/expiry

Implements SEC-013 (OWASP A07 compliance) for session security.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import Response, Request
from starlette.responses import JSONResponse

from src.services.session_manager import SessionManager, get_session_manager, Session


# Cookie configuration constants
SESSION_COOKIE_NAME = "session_id"
SESSION_COOKIE_MAX_AGE = 24 * 60 * 60  # 24 hours in seconds


@dataclass
class CookieConfig:
    """Configuration for session cookie security attributes.

    Attributes:
        httponly: Prevent JavaScript access to cookie (XSS protection).
        secure: Only send cookie over HTTPS.
        samesite: Control cross-site request behavior (CSRF protection).
        max_age: Cookie expiration time in seconds.
        path: Cookie path scope.
    """
    httponly: bool = True
    secure: bool = True
    samesite: str = "strict"  # Options: "strict", "lax", "none"
    max_age: int = SESSION_COOKIE_MAX_AGE
    path: str = "/"


class SessionService:
    """Service for secure session management with cookie support.

    Provides session lifecycle operations with secure cookie handling:
    - Create sessions with secure cookie flags
    - Validate sessions and handle expiry
    - Delete sessions with secure key cleanup

    Example:
        service = SessionService()

        # Create session with secure cookie
        response = service.create_session_with_cookie(response, session_id)

        # Get session from request cookie
        session = service.get_session_from_request(request)

        # Delete session and clear cookie
        response = service.delete_session_with_cookie(response, session_id)
    """

    def __init__(
        self,
        session_manager: Optional[SessionManager] = None,
        cookie_config: Optional[CookieConfig] = None,
        secure_mode: bool = True
    ):
        """Initialize the session service.

        Args:
            session_manager: SessionManager instance (uses global if None).
            cookie_config: Cookie security configuration.
            secure_mode: If False, disables Secure flag for local dev.
        """
        self._session_manager = session_manager or get_session_manager()
        self._cookie_config = cookie_config or CookieConfig()
        self._secure_mode = secure_mode

        # Override secure flag based on mode
        if not secure_mode:
            self._cookie_config.secure = False

    def create_session(self, session_id: str) -> Session:
        """Create a new session.

        Args:
            session_id: Unique session identifier.

        Returns:
            The created Session object.
        """
        return self._session_manager.create_session(session_id)

    def set_session_cookie(
        self,
        response: Response,
        session_id: str
    ) -> Response:
        """Set a secure session cookie on the response.

        The cookie is configured with:
        - HttpOnly: Prevents JavaScript access (XSS protection)
        - Secure: Only sent over HTTPS
        - SameSite=Strict: Prevents CSRF attacks

        Args:
            response: The FastAPI response object.
            session_id: The session ID to set in the cookie.

        Returns:
            The response with the session cookie set.
        """
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            max_age=self._cookie_config.max_age,
            httponly=self._cookie_config.httponly,
            secure=self._cookie_config.secure,
            samesite=self._cookie_config.samesite,
            path=self._cookie_config.path
        )
        return response

    def create_session_with_cookie(
        self,
        response: Response,
        session_id: str
    ) -> Response:
        """Create a session and set a secure cookie.

        Args:
            response: The FastAPI response object.
            session_id: Unique session identifier.

        Returns:
            The response with the session cookie set.
        """
        self.create_session(session_id)
        return self.set_session_cookie(response, session_id)

    def get_session_id_from_request(self, request: Request) -> Optional[str]:
        """Extract session ID from request cookie.

        Args:
            request: The FastAPI request object.

        Returns:
            The session ID if present, None otherwise.
        """
        return request.cookies.get(SESSION_COOKIE_NAME)

    def get_session_from_request(self, request: Request) -> Optional[Session]:
        """Get session object from request cookie.

        Args:
            request: The FastAPI request object.

        Returns:
            The Session if valid, None if not found or expired.
        """
        session_id = self.get_session_id_from_request(request)
        if not session_id:
            return None

        session = self._session_manager.get_session(session_id)
        if session is None:
            return None

        if session.is_expired():
            return None

        return session

    def validate_session(self, request: Request) -> tuple[bool, Optional[str]]:
        """Validate session from request.

        Args:
            request: The FastAPI request object.

        Returns:
            Tuple of (is_valid, error_message).
            is_valid is True if session is valid, False otherwise.
            error_message is None if valid, descriptive message if not.
        """
        session_id = self.get_session_id_from_request(request)

        if not session_id:
            return False, "No session cookie present"

        session = self._session_manager.get_session(session_id)
        if session is None:
            return False, "Session not found"

        if session.is_expired():
            return False, "Session expired. Please reconnect your API key."

        # Update activity timestamp
        self._session_manager.touch_session(session_id)
        return True, None

    def clear_session_cookie(self, response: Response) -> Response:
        """Clear the session cookie from the response.

        Args:
            response: The FastAPI response object.

        Returns:
            The response with the session cookie cleared.
        """
        response.delete_cookie(
            key=SESSION_COOKIE_NAME,
            path=self._cookie_config.path
        )
        return response

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and trigger cleanup callbacks.

        This will run all registered cleanup callbacks (including
        secure key deletion).

        Args:
            session_id: The session ID to delete.

        Returns:
            True if session was deleted, False if not found.
        """
        return self._session_manager.delete_session(session_id)

    def delete_session_with_cookie(
        self,
        response: Response,
        session_id: str
    ) -> Response:
        """Delete session and clear the cookie.

        This performs:
        1. Runs cleanup callbacks (secure key deletion)
        2. Removes session from manager
        3. Clears the session cookie

        Args:
            response: The FastAPI response object.
            session_id: The session ID to delete.

        Returns:
            The response with cleared session cookie.
        """
        self.delete_session(session_id)
        return self.clear_session_cookie(response)

    def disconnect(self, request: Request, response: Response) -> Response:
        """Handle session disconnect.

        Securely deletes the session and all associated data:
        1. Runs cleanup callbacks (triggers secure key deletion)
        2. Removes session from storage
        3. Clears the session cookie

        Args:
            request: The incoming request.
            response: The response to modify.

        Returns:
            The response with cleared session.
        """
        session_id = self.get_session_id_from_request(request)
        if session_id:
            return self.delete_session_with_cookie(response, session_id)
        return response

    def is_session_valid(self, session_id: str) -> bool:
        """Check if a session is valid (exists and not expired).

        Args:
            session_id: The session ID to check.

        Returns:
            True if session is valid, False otherwise.
        """
        session = self._session_manager.get_session(session_id)
        if session is None:
            return False
        return not session.is_expired()

    def get_cookie_config(self) -> CookieConfig:
        """Get the current cookie configuration.

        Returns:
            The CookieConfig in use.
        """
        return self._cookie_config


# Global singleton instance
_session_service: Optional[SessionService] = None


def get_session_service(secure_mode: bool = True) -> SessionService:
    """Get the global session service instance.

    Args:
        secure_mode: Whether to use secure cookies (default True).

    Returns:
        The singleton SessionService instance.
    """
    global _session_service
    if _session_service is None:
        _session_service = SessionService(secure_mode=secure_mode)
    return _session_service


def set_session_service(service: SessionService) -> None:
    """Set the global session service instance (for testing).

    Args:
        service: The SessionService instance to use.
    """
    global _session_service
    _session_service = service
