"""Claude API authentication and generation routes."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from src.models.claude_schemas import (
    ClaudeAuthRequest,
    ClaudeAuthResponse,
)
from src.services.key_storage_service import KeyStorageService

# Create router for Claude-related endpoints
router = APIRouter(prefix="/auth/claude", tags=["claude-auth"])

# Global key storage service instance
# Note: In production, this should be injected via dependency injection
_key_storage = KeyStorageService()


def get_key_storage() -> KeyStorageService:
    """Get the key storage service instance."""
    return _key_storage


async def validate_claude_api_key(api_key: str) -> tuple[bool, Optional[str]]:
    """Validate a Claude API key by making a minimal API call.

    Args:
        api_key: The Anthropic API key to validate.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, returns (True, None).
        If invalid, returns (False, error_message).
    """
    try:
        import anthropic

        # Create client with the provided API key
        client = anthropic.Anthropic(api_key=api_key)

        # Make a minimal API call to validate the key
        # Using count_tokens is a lightweight way to verify the key
        # without incurring significant costs
        client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1,
            messages=[{"role": "user", "content": "test"}]
        )

        return True, None

    except anthropic.AuthenticationError:
        return False, "Invalid API key. Please check your Anthropic API key."
    except anthropic.PermissionDeniedError:
        return False, "API key does not have permission to access Claude. Please check your API key permissions."
    except anthropic.RateLimitError:
        # If we hit rate limit, the key is actually valid
        return True, None
    except anthropic.APIConnectionError:
        return False, "Could not connect to Anthropic API. Please check your network connection."
    except Exception as e:
        # Don't expose raw error messages to users
        return False, "Failed to validate API key. Please try again."


@router.get("/status", response_model=ClaudeAuthResponse)
async def get_claude_status(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> ClaudeAuthResponse:
    """Get the Claude connection status for a session.

    Args:
        x_session_id: Session ID from header for key lookup.

    Returns:
        ClaudeAuthResponse with connection status and masked key if connected.
    """
    session_id = x_session_id or "default"
    storage = get_key_storage()

    if storage.exists(session_id):
        masked_key = storage.get_masked_key(session_id)
        return ClaudeAuthResponse(
            connected=True,
            masked_key=masked_key
        )
    else:
        return ClaudeAuthResponse(
            connected=False,
            masked_key=None
        )


@router.post("/connect", response_model=ClaudeAuthResponse)
async def connect_claude(
    request: ClaudeAuthRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> ClaudeAuthResponse:
    """Connect and validate a Claude API key.

    Validates the API key against the Anthropic API and stores it
    securely if valid.

    Args:
        request: The authentication request containing the API key.
        x_session_id: Session ID from header for key association.

    Returns:
        ClaudeAuthResponse with connection status.
    """
    # Use session ID from header or generate a default one
    session_id = x_session_id or "default"

    # Validate the API key
    is_valid, error_message = await validate_claude_api_key(request.api_key)

    if not is_valid:
        # Return 400 with error message for invalid keys
        raise HTTPException(
            status_code=400,
            detail=error_message or "Invalid API key"
        )

    # Store the encrypted key
    storage = get_key_storage()
    storage.store(session_id, request.api_key)

    # Get masked key for response
    masked_key = storage.get_masked_key(session_id)

    return ClaudeAuthResponse(
        connected=True,
        masked_key=masked_key
    )


@router.post("/disconnect", response_model=ClaudeAuthResponse)
async def disconnect_claude(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> ClaudeAuthResponse:
    """Disconnect and remove a stored Claude API key.

    Deletes the stored API key for the session.

    Args:
        x_session_id: Session ID from header for key lookup.

    Returns:
        ClaudeAuthResponse with disconnected status.

    Raises:
        HTTPException: 400 if no key is stored for the session.
    """
    session_id = x_session_id or "default"
    storage = get_key_storage()

    # Check if a key exists for this session
    if not storage.exists(session_id):
        raise HTTPException(
            status_code=400,
            detail="No Claude API key connected for this session"
        )

    # Delete the stored key
    storage.delete(session_id)

    return ClaudeAuthResponse(
        connected=False,
        masked_key=None
    )
