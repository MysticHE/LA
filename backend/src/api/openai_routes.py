"""OpenAI API authentication routes.

Provides endpoints for connecting, checking status, and disconnecting
OpenAI API keys with secure session-based storage.
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from src.models.openai_schemas import (
    OpenAIAuthRequest,
    OpenAIAuthResponse,
)
from src.services.key_storage_service import KeyStorageService
from src.services.openai_client import OpenAIClient
from src.services.audit_logger import get_audit_logger, AuditStatus

# Create router for OpenAI-related endpoints
router = APIRouter(prefix="/auth/openai", tags=["openai-auth"])

# Global key storage service instance for OpenAI keys
# Note: In production, this should be injected via dependency injection
_openai_key_storage = KeyStorageService()


def get_openai_key_storage() -> KeyStorageService:
    """Get the OpenAI key storage service instance."""
    return _openai_key_storage


async def validate_openai_api_key(api_key: str) -> tuple[bool, Optional[str]]:
    """Validate an OpenAI API key by making a lightweight API call.

    Args:
        api_key: The OpenAI API key to validate.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, returns (True, None).
        If invalid, returns (False, error_message).
    """
    try:
        client = OpenAIClient(api_key=api_key)
        is_valid = client.validate_key()

        if is_valid:
            return True, None
        else:
            return False, "Invalid API key. Please check your OpenAI API key."
    except Exception:
        # Don't expose raw error messages to users
        return False, "Failed to validate API key. Please try again."


@router.get("/status", response_model=OpenAIAuthResponse)
async def get_openai_status(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> OpenAIAuthResponse:
    """Get the OpenAI connection status for a session.

    Args:
        x_session_id: Session ID from header for key lookup.

    Returns:
        OpenAIAuthResponse with connection status and masked key if connected.
    """
    session_id = x_session_id or "default"
    storage = get_openai_key_storage()

    if storage.exists(session_id):
        masked_key = storage.get_masked_key(session_id)
        return OpenAIAuthResponse(
            connected=True,
            masked_key=masked_key
        )
    else:
        return OpenAIAuthResponse(
            connected=False,
            masked_key=None
        )


@router.post("/connect", response_model=OpenAIAuthResponse)
async def connect_openai(
    request: OpenAIAuthRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> OpenAIAuthResponse:
    """Connect and validate an OpenAI API key.

    Validates the API key against the OpenAI API and stores it
    securely if valid.

    Args:
        request: The authentication request containing the API key.
        x_session_id: Session ID from header for key association.

    Returns:
        OpenAIAuthResponse with connection status.
    """
    # Use session ID from header or generate a default one
    session_id = x_session_id or "default"
    audit = get_audit_logger()

    # Validate the API key
    is_valid, error_message = await validate_openai_api_key(request.api_key)

    if not is_valid:
        # Log failed connection attempt
        audit.log_key_connect(
            session_id=session_id,
            provider="openai",
            status=AuditStatus.FAILURE,
            error_message=error_message
        )
        # Return 400 with error message for invalid keys
        raise HTTPException(
            status_code=400,
            detail=error_message or "Invalid API key"
        )

    # Store the encrypted key
    storage = get_openai_key_storage()
    storage.store(session_id, request.api_key)

    # Get masked key for response
    masked_key = storage.get_masked_key(session_id)

    # Log successful connection
    audit.log_key_connect(
        session_id=session_id,
        provider="openai",
        status=AuditStatus.SUCCESS
    )

    return OpenAIAuthResponse(
        connected=True,
        masked_key=masked_key
    )


@router.post("/disconnect", response_model=OpenAIAuthResponse)
async def disconnect_openai(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> OpenAIAuthResponse:
    """Disconnect and remove a stored OpenAI API key.

    Deletes the stored API key for the session.

    Args:
        x_session_id: Session ID from header for key lookup.

    Returns:
        OpenAIAuthResponse with disconnected status.

    Raises:
        HTTPException: 400 if no key is stored for the session.
    """
    session_id = x_session_id or "default"
    storage = get_openai_key_storage()
    audit = get_audit_logger()

    # Check if a key exists for this session
    if not storage.exists(session_id):
        # Log unauthorized disconnect attempt
        audit.log_unauthorized_access(
            session_id=session_id,
            request_path="/auth/openai/disconnect",
            request_method="POST",
            error_message="No OpenAI API key connected for this session"
        )
        raise HTTPException(
            status_code=400,
            detail="No OpenAI API key connected for this session"
        )

    # Delete the stored key
    storage.delete(session_id)

    # Log successful disconnect
    audit.log_key_disconnect(
        session_id=session_id,
        provider="openai",
        status=AuditStatus.SUCCESS
    )

    return OpenAIAuthResponse(
        connected=False,
        masked_key=None
    )
