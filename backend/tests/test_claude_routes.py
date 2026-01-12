"""Tests for Claude authentication routes."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.claude_routes import get_key_storage, _key_storage


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test."""
    _key_storage.clear_all()
    yield
    _key_storage.clear_all()


class TestConnectEndpoint:
    """Tests for POST /api/auth/claude/connect endpoint."""

    def test_connect_with_valid_key_returns_200(self, client):
        """Test that valid API key returns 200 with connected: true."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            response = client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-valid-key-1234"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["connected"] is True
            assert data["masked_key"] is not None
            assert data["masked_key"].endswith("1234")

    def test_connect_with_invalid_key_returns_400(self, client):
        """Test that invalid API key returns 400 with error message."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (False, "Invalid API key. Please check your Anthropic API key.")

            response = client.post(
                "/api/auth/claude/connect",
                json={"api_key": "invalid-key"}
            )

            assert response.status_code == 400
            data = response.json()
            assert "Invalid API key" in data["detail"]

    def test_connect_stores_encrypted_key(self, client):
        """Test that successful validation stores the encrypted key."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            response = client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-test-key-5678"},
                headers={"X-Session-ID": "test-session-123"}
            )

            assert response.status_code == 200

            # Verify key was stored
            storage = get_key_storage()
            assert storage.exists("test-session-123")
            assert storage.retrieve("test-session-123") == "sk-ant-api03-test-key-5678"

    def test_connect_with_empty_key_returns_422(self, client):
        """Test that empty API key returns 422 validation error."""
        response = client.post(
            "/api/auth/claude/connect",
            json={"api_key": ""}
        )

        assert response.status_code == 422

    def test_connect_with_whitespace_key_returns_422(self, client):
        """Test that whitespace-only API key returns 422 validation error."""
        response = client.post(
            "/api/auth/claude/connect",
            json={"api_key": "   "}
        )

        assert response.status_code == 422

    def test_connect_with_missing_key_returns_422(self, client):
        """Test that missing API key returns 422 validation error."""
        response = client.post(
            "/api/auth/claude/connect",
            json={}
        )

        assert response.status_code == 422

    def test_connect_uses_default_session_id_when_not_provided(self, client):
        """Test that default session ID is used when not provided."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            response = client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-default-1234"}
            )

            assert response.status_code == 200

            # Verify key was stored under default session
            storage = get_key_storage()
            assert storage.exists("default")

    def test_connect_with_permission_denied_error(self, client):
        """Test handling of permission denied error."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (False, "API key does not have permission to access Claude.")

            response = client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-no-perms"}
            )

            assert response.status_code == 400
            assert "permission" in response.json()["detail"].lower()

    def test_connect_with_connection_error(self, client):
        """Test handling of connection error."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (False, "Could not connect to Anthropic API.")

            response = client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-valid"}
            )

            assert response.status_code == 400
            assert "connect" in response.json()["detail"].lower()

    def test_connect_masked_key_format(self, client):
        """Test that masked key shows only last 4 characters."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            response = client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-abcdefghijklmnop"}
            )

            assert response.status_code == 200
            masked_key = response.json()["masked_key"]

            # Should be asterisks followed by last 4 chars
            assert masked_key.endswith("mnop")
            assert "*" in masked_key


class TestValidateClaudeApiKey:
    """Tests for validate_claude_api_key function."""

    @pytest.mark.asyncio
    async def test_valid_key_returns_true(self):
        """Test that valid key returns (True, None)."""
        from src.api.claude_routes import validate_claude_api_key

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = MagicMock()

            is_valid, error = await validate_claude_api_key("sk-ant-valid-key")

            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_invalid_key_returns_false(self):
        """Test that invalid key returns (False, error_message)."""
        import anthropic
        from src.api.claude_routes import validate_claude_api_key

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = anthropic.AuthenticationError(
                message="Invalid API Key",
                response=MagicMock(status_code=401),
                body={}
            )

            is_valid, error = await validate_claude_api_key("invalid-key")

            assert is_valid is False
            assert error is not None
            assert "Invalid API key" in error

    @pytest.mark.asyncio
    async def test_rate_limit_returns_true(self):
        """Test that rate limit error returns (True, None) since key is valid."""
        import anthropic
        from src.api.claude_routes import validate_claude_api_key

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = anthropic.RateLimitError(
                message="Rate limited",
                response=MagicMock(status_code=429),
                body={}
            )

            is_valid, error = await validate_claude_api_key("sk-ant-valid-key")

            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_permission_denied_returns_false(self):
        """Test that permission denied error returns (False, error_message)."""
        import anthropic
        from src.api.claude_routes import validate_claude_api_key

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = anthropic.PermissionDeniedError(
                message="Permission denied",
                response=MagicMock(status_code=403),
                body={}
            )

            is_valid, error = await validate_claude_api_key("sk-ant-no-perms")

            assert is_valid is False
            assert error is not None
            assert "permission" in error.lower()

    @pytest.mark.asyncio
    async def test_connection_error_returns_false(self):
        """Test that connection error returns (False, error_message)."""
        import anthropic
        import httpx
        from src.api.claude_routes import validate_claude_api_key

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            # APIConnectionError requires a request parameter
            mock_request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            mock_client.messages.create.side_effect = anthropic.APIConnectionError(
                request=mock_request
            )

            is_valid, error = await validate_claude_api_key("sk-ant-valid")

            assert is_valid is False
            assert error is not None
            assert "connect" in error.lower()

    @pytest.mark.asyncio
    async def test_generic_exception_returns_false(self):
        """Test that generic exception returns (False, generic_error_message)."""
        from src.api.claude_routes import validate_claude_api_key

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("Unknown error")

            is_valid, error = await validate_claude_api_key("sk-ant-valid")

            assert is_valid is False
            assert error is not None
            # Should not expose raw error message
            assert "Failed to validate API key" in error


class TestIntegration:
    """Integration tests for the Claude authentication flow."""

    def test_full_connect_flow(self, client):
        """Test the full connection flow with valid key."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            # Connect with valid key
            response = client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-integration-test"},
                headers={"X-Session-ID": "integration-test-session"}
            )

            assert response.status_code == 200
            assert response.json()["connected"] is True

            # Verify key is stored and retrievable
            storage = get_key_storage()
            stored_key = storage.retrieve("integration-test-session")
            assert stored_key == "sk-ant-api03-integration-test"

    def test_connect_replaces_existing_key(self, client):
        """Test that connecting again replaces the existing key."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            # First connection
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-first-key"},
                headers={"X-Session-ID": "replace-test"}
            )

            # Second connection with different key
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-second-key"},
                headers={"X-Session-ID": "replace-test"}
            )

            # Verify new key replaced old
            storage = get_key_storage()
            stored_key = storage.retrieve("replace-test")
            assert stored_key == "sk-ant-api03-second-key"


class TestStatusEndpoint:
    """Tests for GET /api/auth/claude/status endpoint."""

    def test_status_when_connected_returns_true_with_masked_key(self, client):
        """Test that status returns connected: true with masked key when connected."""
        # First, connect with a key
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-test-status-1234"},
                headers={"X-Session-ID": "status-test-session"}
            )

        # Then check status
        response = client.get(
            "/api/auth/claude/status",
            headers={"X-Session-ID": "status-test-session"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["masked_key"] is not None
        assert data["masked_key"].endswith("1234")

    def test_status_when_not_connected_returns_false(self, client):
        """Test that status returns connected: false when not connected."""
        response = client.get(
            "/api/auth/claude/status",
            headers={"X-Session-ID": "non-existent-session"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["masked_key"] is None

    def test_status_uses_default_session_when_not_provided(self, client):
        """Test that status uses default session ID when not provided."""
        # First, connect with default session
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-default-key-5678"}
            )

        # Check status without session ID
        response = client.get("/api/auth/claude/status")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["masked_key"].endswith("5678")

    def test_status_masked_key_shows_only_last_4_chars(self, client):
        """Test that masked key shows only last 4 characters."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            # Use a long key to verify masking
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-this-is-a-very-long-api-key-abcd"},
                headers={"X-Session-ID": "mask-test-session"}
            )

        response = client.get(
            "/api/auth/claude/status",
            headers={"X-Session-ID": "mask-test-session"}
        )

        assert response.status_code == 200
        masked_key = response.json()["masked_key"]
        
        # Should end with last 4 chars
        assert masked_key.endswith("abcd")
        # Should have asterisks before
        assert "*" in masked_key
        # The visible part should only be 4 chars
        visible_chars = masked_key.replace("*", "")
        assert visible_chars == "abcd"

    def test_status_returns_different_results_for_different_sessions(self, client):
        """Test that different sessions have independent status."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            # Connect session 1
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-session1-1111"},
                headers={"X-Session-ID": "session-1"}
            )

        # Check session 1 - should be connected
        response1 = client.get(
            "/api/auth/claude/status",
            headers={"X-Session-ID": "session-1"}
        )
        assert response1.json()["connected"] is True
        assert response1.json()["masked_key"].endswith("1111")

        # Check session 2 - should not be connected
        response2 = client.get(
            "/api/auth/claude/status",
            headers={"X-Session-ID": "session-2"}
        )
        assert response2.json()["connected"] is False
        assert response2.json()["masked_key"] is None


class TestDisconnectEndpoint:
    """Tests for POST /api/auth/claude/disconnect endpoint."""

    def test_disconnect_when_connected_deletes_key_and_returns_success(self, client):
        """Test that disconnect deletes the stored key and returns connected: false."""
        # First, connect with a key
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-to-disconnect-1234"},
                headers={"X-Session-ID": "disconnect-test-session"}
            )

        # Verify key was stored
        storage = get_key_storage()
        assert storage.exists("disconnect-test-session")

        # Disconnect
        response = client.post(
            "/api/auth/claude/disconnect",
            headers={"X-Session-ID": "disconnect-test-session"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["masked_key"] is None

        # Verify key was deleted
        assert not storage.exists("disconnect-test-session")

    def test_disconnect_when_not_connected_returns_400(self, client):
        """Test that disconnect returns 400 when no key is stored."""
        response = client.post(
            "/api/auth/claude/disconnect",
            headers={"X-Session-ID": "non-existent-session"}
        )

        assert response.status_code == 400
        assert "No Claude API key connected" in response.json()["detail"]

    def test_disconnect_uses_default_session_when_not_provided(self, client):
        """Test that disconnect uses default session ID when not provided."""
        # First, connect with default session
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-default-disconnect-5678"}
            )

        # Verify key was stored under default session
        storage = get_key_storage()
        assert storage.exists("default")

        # Disconnect without session ID
        response = client.post("/api/auth/claude/disconnect")

        assert response.status_code == 200
        assert response.json()["connected"] is False

        # Verify key was deleted
        assert not storage.exists("default")

    def test_disconnect_subsequent_status_shows_disconnected(self, client):
        """Test that status call shows disconnected after successful disconnect."""
        # First, connect with a key
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-status-after-disconnect"},
                headers={"X-Session-ID": "status-after-disconnect-session"}
            )

        # Verify connected
        status_response1 = client.get(
            "/api/auth/claude/status",
            headers={"X-Session-ID": "status-after-disconnect-session"}
        )
        assert status_response1.json()["connected"] is True

        # Disconnect
        disconnect_response = client.post(
            "/api/auth/claude/disconnect",
            headers={"X-Session-ID": "status-after-disconnect-session"}
        )
        assert disconnect_response.status_code == 200

        # Verify status shows disconnected
        status_response2 = client.get(
            "/api/auth/claude/status",
            headers={"X-Session-ID": "status-after-disconnect-session"}
        )
        assert status_response2.json()["connected"] is False
        assert status_response2.json()["masked_key"] is None

    def test_disconnect_only_affects_specified_session(self, client):
        """Test that disconnect only affects the specified session, not others."""
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            # Connect session 1
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-session-a-key"},
                headers={"X-Session-ID": "session-a"}
            )
            # Connect session 2
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-session-b-key"},
                headers={"X-Session-ID": "session-b"}
            )

        # Disconnect session 1
        client.post(
            "/api/auth/claude/disconnect",
            headers={"X-Session-ID": "session-a"}
        )

        # Session 1 should be disconnected
        storage = get_key_storage()
        assert not storage.exists("session-a")

        # Session 2 should still be connected
        assert storage.exists("session-b")
        assert storage.retrieve("session-b") == "sk-ant-api03-session-b-key"
