"""Gemini API authentication routes.

Provides endpoints for connecting, checking status, and disconnecting
Gemini API keys with secure session-based storage.
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from google import genai

from src.models.gemini_schemas import (
    GeminiAuthRequest,
    GeminiAuthResponse,
)
from src.services.key_storage_service import KeyStorageService
from src.services.audit_logger import get_audit_logger, AuditStatus

# Create router for Gemini-related endpoints
router = APIRouter(prefix="/auth/gemini", tags=["gemini-auth"])

# Global key storage service instance for Gemini keys
# Note: In production, this should be injected via dependency injection
_gemini_key_storage = KeyStorageService()


def get_gemini_key_storage() -> KeyStorageService:
    """Get the Gemini key storage service instance."""
    return _gemini_key_storage


async def validate_gemini_api_key(api_key: str) -> tuple[bool, Optional[str]]:
    """Validate a Gemini API key by making a minimal API call.

    Args:
        api_key: The Google Gemini API key to validate.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, returns (True, None).
        If invalid, returns (False, error_message).
    """
    try:
        # Create client with the provided API key
        client = genai.Client(api_key=api_key)

        # Make a minimal API call to validate the key
        client.models.generate_content(
            model="gemini-2.0-flash",
            contents="test",
            config={"max_output_tokens": 1}
        )

        return True, None

    except Exception as e:
        error_str = str(e).lower()

        # Check for authentication errors
        if "api key" in error_str or "invalid" in error_str or "401" in error_str:
            return False, "Invalid API key. Please check your Gemini API key."

        # Check for permission errors
        if "permission" in error_str or "403" in error_str:
            return False, "API key does not have permission to access Gemini. Please check your API key permissions."

        # Check for rate limit errors - key is valid if rate limited
        if "rate" in error_str or "429" in error_str or "quota" in error_str:
            return True, None

        # Check for connection errors
        if "connect" in error_str or "network" in error_str:
            return False, "Could not connect to Gemini API. Please check your network connection."

        # Don't expose raw error messages to users
        return False, "Failed to validate API key. Please try again."


@router.get("/status", response_model=GeminiAuthResponse)
async def get_gemini_status(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> GeminiAuthResponse:
    """Get the Gemini connection status for a session.

    Args:
        x_session_id: Session ID from header for key lookup.

    Returns:
        GeminiAuthResponse with connection status and masked key if connected.
    """
    session_id = x_session_id or "default"
    storage = get_gemini_key_storage()

    if storage.exists(session_id):
        masked_key = storage.get_masked_key(session_id)
        return GeminiAuthResponse(
            connected=True,
            masked_key=masked_key
        )
    else:
        return GeminiAuthResponse(
            connected=False,
            masked_key=None
        )


@router.post("/connect", response_model=GeminiAuthResponse)
async def connect_gemini(
    request: GeminiAuthRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> GeminiAuthResponse:
    """Connect and validate a Gemini API key.

    Validates the API key against the Gemini API and stores it
    securely if valid.

    Args:
        request: The authentication request containing the API key.
        x_session_id: Session ID from header for key association.

    Returns:
        GeminiAuthResponse with connection status.
    """
    # Use session ID from header or generate a default one
    session_id = x_session_id or "default"
    audit = get_audit_logger()

    # Validate the API key
    is_valid, error_message = await validate_gemini_api_key(request.api_key)

    if not is_valid:
        # Log failed connection attempt
        audit.log_key_connect(
            session_id=session_id,
            provider="gemini",
            status=AuditStatus.FAILURE,
            error_message=error_message
        )
        # Return 400 with error message for invalid keys
        raise HTTPException(
            status_code=400,
            detail=error_message or "Invalid API key"
        )

    # Store the encrypted key
    storage = get_gemini_key_storage()
    storage.store(session_id, request.api_key)

    # Get masked key for response
    masked_key = storage.get_masked_key(session_id)

    # Log successful connection
    audit.log_key_connect(
        session_id=session_id,
        provider="gemini",
        status=AuditStatus.SUCCESS
    )

    return GeminiAuthResponse(
        connected=True,
        masked_key=masked_key
    )


@router.post("/disconnect", response_model=GeminiAuthResponse)
async def disconnect_gemini(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> GeminiAuthResponse:
    """Disconnect and remove a stored Gemini API key.

    Deletes the stored API key for the session.

    Args:
        x_session_id: Session ID from header for key lookup.

    Returns:
        GeminiAuthResponse with disconnected status.

    Raises:
        HTTPException: 400 if no key is stored for the session.
    """
    session_id = x_session_id or "default"
    storage = get_gemini_key_storage()
    audit = get_audit_logger()

    # Check if a key exists for this session
    if not storage.exists(session_id):
        # Log unauthorized disconnect attempt
        audit.log_unauthorized_access(
            session_id=session_id,
            request_path="/auth/gemini/disconnect",
            request_method="POST",
            error_message="No Gemini API key connected for this session"
        )
        raise HTTPException(
            status_code=400,
            detail="No Gemini API key connected for this session"
        )

    # Delete the stored key
    storage.delete(session_id)

    # Log successful disconnect
    audit.log_key_disconnect(
        session_id=session_id,
        provider="gemini",
        status=AuditStatus.SUCCESS
    )

    return GeminiAuthResponse(
        connected=False,
        masked_key=None
    )
