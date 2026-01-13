"""Tests for OpenAI authentication routes."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.openai_routes import get_openai_key_storage, _openai_key_storage


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test."""
    _openai_key_storage.clear_all()
    yield
    _openai_key_storage.clear_all()


class TestConnectEndpoint:
    """Tests for POST /api/auth/openai/connect endpoint."""

    def test_connect_with_valid_key_returns_200(self, client):
        """Test that valid API key returns 200 with connected: true."""
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            response = client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-abc123def456ghi789jkl012mno345pqr6789stu"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["connected"] is True
            assert data["masked_key"] is not None
            assert data["masked_key"].endswith("9stu")

    def test_connect_with_invalid_key_returns_400(self, client):
        """Test that invalid API key returns 400 with error message."""
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (False, "Invalid API key. Please check your OpenAI API key.")

            response = client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-invalid-key-that-is-at-least-40-characters-long"}
            )

            assert response.status_code == 400
            data = response.json()
            assert "Invalid API key" in data["detail"]

    def test_connect_stores_encrypted_key(self, client):
        """Test that successful validation stores the encrypted key."""
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            api_key = "sk-proj-test-key-56789012345678901234567890123456"
            response = client.post(
                "/api/auth/openai/connect",
                json={"api_key": api_key},
                headers={"X-Session-ID": "test-session-123"}
            )

            assert response.status_code == 200

            # Verify key was stored
            storage = get_openai_key_storage()
            assert storage.exists("test-session-123")
            assert storage.retrieve("test-session-123") == api_key

    def test_connect_with_empty_key_returns_422(self, client):
        """Test that empty API key returns 422 validation error."""
        response = client.post(
            "/api/auth/openai/connect",
            json={"api_key": ""}
        )

        assert response.status_code == 422

    def test_connect_with_whitespace_key_returns_422(self, client):
        """Test that whitespace-only API key returns 422 validation error."""
        response = client.post(
            "/api/auth/openai/connect",
            json={"api_key": "   "}
        )

        assert response.status_code == 422

    def test_connect_with_missing_key_returns_422(self, client):
        """Test that missing API key returns 422 validation error."""
        response = client.post(
            "/api/auth/openai/connect",
            json={}
        )

        assert response.status_code == 422

    def test_connect_with_key_not_starting_with_sk_returns_422(self, client):
        """Test that API key not starting with sk- returns 422 validation error."""
        response = client.post(
            "/api/auth/openai/connect",
            json={"api_key": "invalid-prefix-key-that-is-at-least-40-characters"}
        )

        assert response.status_code == 422

    def test_connect_with_key_too_short_returns_422(self, client):
        """Test that API key shorter than 40 chars returns 422 validation error."""
        response = client.post(
            "/api/auth/openai/connect",
            json={"api_key": "sk-tooshort"}
        )

        assert response.status_code == 422

    def test_connect_uses_default_session_id_when_not_provided(self, client):
        """Test that default session ID is used when not provided."""
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            response = client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-default-key-1234567890123456789012345"}
            )

            assert response.status_code == 200

            # Verify key was stored under default session
            storage = get_openai_key_storage()
            assert storage.exists("default")

    def test_connect_masked_key_format(self, client):
        """Test that masked key shows only last 4 characters."""
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            response = client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-abcdefghijklmnopqrstuvwxyz0123456789mnop"}
            )

            assert response.status_code == 200
            masked_key = response.json()["masked_key"]

            # Should be asterisks followed by last 4 chars
            assert masked_key.endswith("mnop")
            assert "*" in masked_key


class TestValidateOpenaiApiKey:
    """Tests for validate_openai_api_key function."""

    @pytest.mark.asyncio
    async def test_valid_key_returns_true(self):
        """Test that valid key returns (True, None)."""
        from src.api.openai_routes import validate_openai_api_key

        with patch('src.api.openai_routes.OpenAIClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.validate_key.return_value = True

            is_valid, error = await validate_openai_api_key("sk-valid-key-123456789012345678901234567890")

            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_invalid_key_returns_false(self):
        """Test that invalid key returns (False, error_message)."""
        from src.api.openai_routes import validate_openai_api_key

        with patch('src.api.openai_routes.OpenAIClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.validate_key.return_value = False

            is_valid, error = await validate_openai_api_key("sk-invalid-key-12345678901234567890123456")

            assert is_valid is False
            assert error is not None
            assert "Invalid API key" in error

    @pytest.mark.asyncio
    async def test_exception_returns_false(self):
        """Test that exception returns (False, generic_error_message)."""
        from src.api.openai_routes import validate_openai_api_key

        with patch('src.api.openai_routes.OpenAIClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Network error")

            is_valid, error = await validate_openai_api_key("sk-valid-key-123456789012345678901234567890")

            assert is_valid is False
            assert error is not None
            # Should not expose raw error message
            assert "Failed to validate API key" in error


class TestIntegration:
    """Integration tests for the OpenAI authentication flow."""

    def test_full_connect_flow(self, client):
        """Test the full connection flow with valid key."""
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            api_key = "sk-proj-integration-test-key-12345678901234567"
            # Connect with valid key
            response = client.post(
                "/api/auth/openai/connect",
                json={"api_key": api_key},
                headers={"X-Session-ID": "integration-test-session"}
            )

            assert response.status_code == 200
            assert response.json()["connected"] is True

            # Verify key is stored and retrievable
            storage = get_openai_key_storage()
            stored_key = storage.retrieve("integration-test-session")
            assert stored_key == api_key

    def test_connect_replaces_existing_key(self, client):
        """Test that connecting again replaces the existing key."""
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)

            # First connection
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-first-key-123456789012345678901234567"},
                headers={"X-Session-ID": "replace-test"}
            )

            # Second connection with different key
            second_key = "sk-proj-second-key-12345678901234567890123456"
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": second_key},
                headers={"X-Session-ID": "replace-test"}
            )

            # Verify new key replaced old
            storage = get_openai_key_storage()
            stored_key = storage.retrieve("replace-test")
            assert stored_key == second_key


class TestStatusEndpoint:
    """Tests for GET /api/auth/openai/status endpoint."""

    def test_status_when_connected_returns_true_with_masked_key(self, client):
        """Test that status returns connected: true with masked key when connected."""
        # First, connect with a key
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-test-status-key-12345678901234561234"},
                headers={"X-Session-ID": "status-test-session"}
            )

        # Then check status
        response = client.get(
            "/api/auth/openai/status",
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
            "/api/auth/openai/status",
            headers={"X-Session-ID": "non-existent-session"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False
        assert data["masked_key"] is None

    def test_status_uses_default_session_when_not_provided(self, client):
        """Test that status uses default session ID when not provided."""
        # First, connect with default session
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-default-key-123456789012345678905678"}
            )

        # Check status without session ID
        response = client.get("/api/auth/openai/status")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["masked_key"].endswith("5678")

    def test_status_masked_key_shows_only_last_4_chars(self, client):
        """Test that masked key shows only last 4 characters."""
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            # Use a long key to verify masking
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-this-is-a-very-long-api-key-abcdef"},
                headers={"X-Session-ID": "mask-test-session"}
            )

        response = client.get(
            "/api/auth/openai/status",
            headers={"X-Session-ID": "mask-test-session"}
        )

        assert response.status_code == 200
        masked_key = response.json()["masked_key"]

        # Should end with last 4 chars
        assert masked_key.endswith("cdef")
        # Should have asterisks before
        assert "*" in masked_key
        # The visible part should only be 4 chars
        visible_chars = masked_key.replace("*", "")
        assert visible_chars == "cdef"

    def test_status_returns_different_results_for_different_sessions(self, client):
        """Test that different sessions have independent status."""
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            # Connect session 1
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-session1-key-12345678901234567891111"},
                headers={"X-Session-ID": "session-1"}
            )

        # Check session 1 - should be connected
        response1 = client.get(
            "/api/auth/openai/status",
            headers={"X-Session-ID": "session-1"}
        )
        assert response1.json()["connected"] is True
        assert response1.json()["masked_key"].endswith("1111")

        # Check session 2 - should not be connected
        response2 = client.get(
            "/api/auth/openai/status",
            headers={"X-Session-ID": "session-2"}
        )
        assert response2.json()["connected"] is False
        assert response2.json()["masked_key"] is None


class TestDisconnectEndpoint:
    """Tests for POST /api/auth/openai/disconnect endpoint."""

    def test_disconnect_when_connected_deletes_key_and_returns_success(self, client):
        """Test that disconnect deletes the stored key and returns connected: false."""
        # First, connect with a key
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-to-disconnect-key-12345678901231234"},
                headers={"X-Session-ID": "disconnect-test-session"}
            )

        # Verify key was stored
        storage = get_openai_key_storage()
        assert storage.exists("disconnect-test-session")

        # Disconnect
        response = client.post(
            "/api/auth/openai/disconnect",
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
            "/api/auth/openai/disconnect",
            headers={"X-Session-ID": "non-existent-session"}
        )

        assert response.status_code == 400
        assert "No OpenAI API key connected" in response.json()["detail"]

    def test_disconnect_uses_default_session_when_not_provided(self, client):
        """Test that disconnect uses default session ID when not provided."""
        # First, connect with default session
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-default-disconnect-key-12345678905678"}
            )

        # Verify key was stored under default session
        storage = get_openai_key_storage()
        assert storage.exists("default")

        # Disconnect without session ID
        response = client.post("/api/auth/openai/disconnect")

        assert response.status_code == 200
        assert response.json()["connected"] is False

        # Verify key was deleted
        assert not storage.exists("default")

    def test_disconnect_subsequent_status_shows_disconnected(self, client):
        """Test that status call shows disconnected after successful disconnect."""
        # First, connect with a key
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-status-after-disconnect-key-12345678"},
                headers={"X-Session-ID": "status-after-disconnect-session"}
            )

        # Verify connected
        status_response1 = client.get(
            "/api/auth/openai/status",
            headers={"X-Session-ID": "status-after-disconnect-session"}
        )
        assert status_response1.json()["connected"] is True

        # Disconnect
        disconnect_response = client.post(
            "/api/auth/openai/disconnect",
            headers={"X-Session-ID": "status-after-disconnect-session"}
        )
        assert disconnect_response.status_code == 200

        # Verify status shows disconnected
        status_response2 = client.get(
            "/api/auth/openai/status",
            headers={"X-Session-ID": "status-after-disconnect-session"}
        )
        assert status_response2.json()["connected"] is False
        assert status_response2.json()["masked_key"] is None

    def test_disconnect_only_affects_specified_session(self, client):
        """Test that disconnect only affects the specified session, not others."""
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            # Connect session a
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-session-a-key-12345678901234567890"},
                headers={"X-Session-ID": "session-a"}
            )
            # Connect session b
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-session-b-key-12345678901234567890"},
                headers={"X-Session-ID": "session-b"}
            )

        # Disconnect session a
        client.post(
            "/api/auth/openai/disconnect",
            headers={"X-Session-ID": "session-a"}
        )

        # Session a should be disconnected
        storage = get_openai_key_storage()
        assert not storage.exists("session-a")

        # Session b should still be connected
        assert storage.exists("session-b")
        assert storage.retrieve("session-b") == "sk-proj-session-b-key-12345678901234567890"


class TestOpenAIKeyIsolationFromClaude:
    """Tests to verify OpenAI keys are stored separately from Claude keys."""

    def test_openai_and_claude_keys_are_stored_separately(self, client):
        """Test that OpenAI and Claude keys use separate storage."""
        # Connect OpenAI key
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-openai-key-12345678901234567890abcd"},
                headers={"X-Session-ID": "shared-session"}
            )

        # Connect Claude key (with mocked validation)
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-claude-key-test"},
                headers={"X-Session-ID": "shared-session"}
            )

        # Check OpenAI status - should show OpenAI key
        openai_status = client.get(
            "/api/auth/openai/status",
            headers={"X-Session-ID": "shared-session"}
        )
        assert openai_status.json()["connected"] is True
        assert openai_status.json()["masked_key"].endswith("abcd")

        # Check Claude status - should show Claude key
        claude_status = client.get(
            "/api/auth/claude/status",
            headers={"X-Session-ID": "shared-session"}
        )
        assert claude_status.json()["connected"] is True
        assert claude_status.json()["masked_key"].endswith("test")

    def test_disconnecting_openai_does_not_affect_claude(self, client):
        """Test that disconnecting OpenAI doesn't affect Claude connection."""
        # Connect both
        with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/openai/connect",
                json={"api_key": "sk-proj-openai-key-12345678901234567890abcd"},
                headers={"X-Session-ID": "isolation-test"}
            )

        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-claude-key-test"},
                headers={"X-Session-ID": "isolation-test"}
            )

        # Disconnect OpenAI
        client.post(
            "/api/auth/openai/disconnect",
            headers={"X-Session-ID": "isolation-test"}
        )

        # OpenAI should be disconnected
        openai_status = client.get(
            "/api/auth/openai/status",
            headers={"X-Session-ID": "isolation-test"}
        )
        assert openai_status.json()["connected"] is False

        # Claude should still be connected
        claude_status = client.get(
            "/api/auth/claude/status",
            headers={"X-Session-ID": "isolation-test"}
        )
        assert claude_status.json()["connected"] is True
