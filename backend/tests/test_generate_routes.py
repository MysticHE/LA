"""Tests for AI content generation routes."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.claude_routes import _key_storage
from src.api.openai_routes import _openai_key_storage
from src.services.claude_client import GenerationResult
from src.services.openai_client import GenerationResult as OpenAIGenerationResult


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage():
    """Clear storage before each test."""
    _key_storage.clear_all()
    _openai_key_storage.clear_all()
    yield
    _key_storage.clear_all()
    _openai_key_storage.clear_all()


@pytest.fixture
def connected_session(client):
    """Create a connected session with Claude API key stored."""
    from unittest.mock import AsyncMock
    with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = (True, None)
        client.post(
            "/api/auth/claude/connect",
            json={"api_key": "sk-ant-api03-test-key-1234"},
            headers={"X-Session-ID": "test-session"}
        )
    return "test-session"


@pytest.fixture
def openai_connected_session(client):
    """Create a connected session with OpenAI API key stored."""
    from unittest.mock import AsyncMock
    with patch('src.api.openai_routes.validate_openai_api_key', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = (True, None)
        client.post(
            "/api/auth/openai/connect",
            json={"api_key": "sk-openai-test-key-1234567890abcdef1234567890abcdef"},
            headers={"X-Session-ID": "openai-test-session"}
        )
    return "openai-test-session"


@pytest.fixture
def sample_analysis():
    """Sample analysis data for testing."""
    return {
        "repo_name": "awesome-project",
        "description": "An awesome open source project",
        "stars": 1000,
        "forks": 200,
        "language": "Python",
        "tech_stack": [
            {"name": "FastAPI", "category": "framework"},
            {"name": "PostgreSQL", "category": "database"},
        ],
        "features": [
            {"name": "REST API", "description": "Full REST API implementation"},
            {"name": "Auth", "description": "JWT authentication support"},
        ],
        "readme_summary": "A comprehensive project for building web applications.",
        "file_structure": ["src/", "tests/", "README.md"],
    }


class TestGenerateAIPostEndpoint:
    """Tests for POST /api/generate/ai-post endpoint."""

    def test_generate_when_connected_returns_content(self, client, connected_session, sample_analysis):
        """Test that generation returns content when connected with valid request."""
        with patch('src.api.generate_routes.ClaudeClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = GenerationResult(
                success=True,
                content="This is a generated LinkedIn post about awesome-project!"
            )

            response = client.post(
                "/api/generate/ai-post",
                json={"analysis": sample_analysis, "style": "problem-solution"},
                headers={"X-Session-ID": connected_session}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["content"] is not None
            assert "awesome-project" in data["content"]
            assert data["style"] == "problem-solution"

    def test_generate_when_not_connected_returns_401(self, client, sample_analysis):
        """Test that generation returns 401 when not connected."""
        response = client.post(
            "/api/generate/ai-post",
            json={"analysis": sample_analysis, "style": "problem-solution"},
            headers={"X-Session-ID": "unconnected-session"}
        )

        assert response.status_code == 401
        assert "Not connected" in response.json()["detail"]

    def test_generate_with_tips_learnings_style(self, client, connected_session, sample_analysis):
        """Test generation with tips-learnings style."""
        with patch('src.api.generate_routes.ClaudeClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = GenerationResult(
                success=True,
                content="Here's what I learned building awesome-project..."
            )

            response = client.post(
                "/api/generate/ai-post",
                json={"analysis": sample_analysis, "style": "tips-learnings"},
                headers={"X-Session-ID": connected_session}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["style"] == "tips-learnings"

    def test_generate_with_technical_showcase_style(self, client, connected_session, sample_analysis):
        """Test generation with technical-showcase style."""
        with patch('src.api.generate_routes.ClaudeClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = GenerationResult(
                success=True,
                content="Let me walk you through the architecture of awesome-project..."
            )

            response = client.post(
                "/api/generate/ai-post",
                json={"analysis": sample_analysis, "style": "technical-showcase"},
                headers={"X-Session-ID": connected_session}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["style"] == "technical-showcase"

    def test_generate_rate_limit_returns_429_with_retry_after(self, client, connected_session, sample_analysis):
        """Test that rate limit error returns 429 with retry-after header."""
        with patch('src.api.generate_routes.ClaudeClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = GenerationResult(
                success=False,
                error="Rate limit exceeded. Please try again later.",
                retry_after=60
            )

            response = client.post(
                "/api/generate/ai-post",
                json={"analysis": sample_analysis, "style": "problem-solution"},
                headers={"X-Session-ID": connected_session}
            )

            assert response.status_code == 429
            assert "Retry-After" in response.headers
            assert response.headers["Retry-After"] == "60"

    def test_generate_api_error_returns_error_response(self, client, connected_session, sample_analysis):
        """Test that API errors return error response."""
        with patch('src.api.generate_routes.ClaudeClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = GenerationResult(
                success=False,
                error="Failed to generate content. Please try again."
            )

            response = client.post(
                "/api/generate/ai-post",
                json={"analysis": sample_analysis, "style": "problem-solution"},
                headers={"X-Session-ID": connected_session}
            )

            assert response.status_code == 200  # 200 with success=False in body
            data = response.json()
            assert data["success"] is False
            assert data["error"] is not None

    def test_generate_uses_default_session_when_not_provided(self, client, sample_analysis):
        """Test that default session is used when X-Session-ID not provided."""
        # Connect with default session
        from unittest.mock import AsyncMock
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-default-key"}
            )

        with patch('src.api.generate_routes.ClaudeClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = GenerationResult(
                success=True,
                content="Generated content"
            )

            response = client.post(
                "/api/generate/ai-post",
                json={"analysis": sample_analysis, "style": "problem-solution"}
            )

            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_generate_invalid_style_returns_422(self, client, connected_session, sample_analysis):
        """Test that invalid style returns 422 validation error."""
        response = client.post(
            "/api/generate/ai-post",
            json={"analysis": sample_analysis, "style": "invalid-style"},
            headers={"X-Session-ID": connected_session}
        )

        assert response.status_code == 422

    def test_generate_missing_analysis_returns_422(self, client, connected_session):
        """Test that missing analysis returns 422 validation error."""
        response = client.post(
            "/api/generate/ai-post",
            json={"style": "problem-solution"},
            headers={"X-Session-ID": connected_session}
        )

        assert response.status_code == 422

    def test_generate_verifies_prompt_generator_called_with_correct_params(self, client, connected_session, sample_analysis):
        """Test that AI prompt generator is called with correct parameters."""
        with patch('src.api.generate_routes.ClaudeClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = GenerationResult(
                success=True,
                content="Generated content"
            )

            with patch('src.api.generate_routes.AIPromptGenerator.generate_prompt') as mock_gen:
                mock_gen.return_value = ("system prompt", "user prompt")

                response = client.post(
                    "/api/generate/ai-post",
                    json={"analysis": sample_analysis, "style": "tips-learnings"},
                    headers={"X-Session-ID": connected_session}
                )

                assert response.status_code == 200
                # Verify generate_prompt was called
                mock_gen.assert_called_once()
                call_args = mock_gen.call_args
                assert call_args.kwargs["analysis"].repo_name == "awesome-project"


class TestIntegration:
    """Integration tests for the AI generation flow."""

    def test_full_generation_flow(self, client, sample_analysis):
        """Test the full flow from connect to generate."""
        from unittest.mock import AsyncMock

        # Step 1: Connect with API key
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            connect_response = client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-full-flow-test"},
                headers={"X-Session-ID": "integration-session"}
            )
            assert connect_response.status_code == 200
            assert connect_response.json()["connected"] is True

        # Step 2: Generate content
        with patch('src.api.generate_routes.ClaudeClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = GenerationResult(
                success=True,
                content="This is a complete LinkedIn post about awesome-project!"
            )

            generate_response = client.post(
                "/api/generate/ai-post",
                json={"analysis": sample_analysis, "style": "problem-solution"},
                headers={"X-Session-ID": "integration-session"}
            )

            assert generate_response.status_code == 200
            data = generate_response.json()
            assert data["success"] is True
            assert data["content"] is not None

    def test_disconnect_then_generate_returns_401(self, client, sample_analysis):
        """Test that disconnect then generate returns 401."""
        from unittest.mock import AsyncMock

        # Connect
        with patch('src.api.claude_routes.validate_claude_api_key', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = (True, None)
            client.post(
                "/api/auth/claude/connect",
                json={"api_key": "sk-ant-api03-disconnect-test"},
                headers={"X-Session-ID": "disconnect-gen-session"}
            )

        # Disconnect
        client.post(
            "/api/auth/claude/disconnect",
            headers={"X-Session-ID": "disconnect-gen-session"}
        )

        # Try to generate - should fail
        response = client.post(
            "/api/generate/ai-post",
            json={"analysis": sample_analysis, "style": "problem-solution"},
            headers={"X-Session-ID": "disconnect-gen-session"}
        )

        assert response.status_code == 401


class TestOpenAIProviderRouting:
    """Tests for OpenAI provider routing in /api/generate/ai-post endpoint."""

    def test_generate_with_openai_provider_uses_openai_client(
        self, client, openai_connected_session, sample_analysis
    ):
        """Test that provider='openai' routes to OpenAI client."""
        with patch('src.api.generate_routes.OpenAIClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = OpenAIGenerationResult(
                success=True,
                content="This is a LinkedIn post generated by OpenAI!"
            )

            response = client.post(
                "/api/generate/ai-post",
                json={
                    "analysis": sample_analysis,
                    "style": "problem-solution",
                    "provider": "openai"
                },
                headers={"X-Session-ID": openai_connected_session}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["content"] is not None
            assert "OpenAI" in data["content"]
            # Verify OpenAI client was used
            mock_client_class.assert_called_once()

    def test_generate_with_openai_provider_and_model(
        self, client, openai_connected_session, sample_analysis
    ):
        """Test that model parameter is passed to OpenAI client."""
        with patch('src.api.generate_routes.OpenAIClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = OpenAIGenerationResult(
                success=True,
                content="Generated with GPT-4"
            )

            response = client.post(
                "/api/generate/ai-post",
                json={
                    "analysis": sample_analysis,
                    "style": "tips-learnings",
                    "provider": "openai",
                    "model": "gpt-4"
                },
                headers={"X-Session-ID": openai_connected_session}
            )

            assert response.status_code == 200
            assert response.json()["success"] is True
            # Verify model was passed to generate_content
            call_kwargs = mock_client.generate_content.call_args.kwargs
            assert call_kwargs["model"] == "gpt-4"

    def test_generate_with_openai_no_connection_returns_401(
        self, client, sample_analysis
    ):
        """Test that OpenAI provider without connection returns 401."""
        response = client.post(
            "/api/generate/ai-post",
            json={
                "analysis": sample_analysis,
                "style": "problem-solution",
                "provider": "openai"
            },
            headers={"X-Session-ID": "no-openai-connection"}
        )

        assert response.status_code == 401
        assert "Not connected to OpenAI" in response.json()["detail"]

    def test_default_provider_is_claude(self, client, connected_session, sample_analysis):
        """Test that no provider parameter defaults to Claude."""
        with patch('src.api.generate_routes.ClaudeClient') as mock_claude_class:
            mock_client = MagicMock()
            mock_claude_class.return_value = mock_client
            mock_client.generate_content.return_value = GenerationResult(
                success=True,
                content="Generated by Claude"
            )

            response = client.post(
                "/api/generate/ai-post",
                json={
                    "analysis": sample_analysis,
                    "style": "problem-solution"
                    # No provider - should default to claude
                },
                headers={"X-Session-ID": connected_session}
            )

            assert response.status_code == 200
            assert response.json()["success"] is True
            # Verify Claude client was used, not OpenAI
            mock_claude_class.assert_called_once()

    def test_explicit_claude_provider_uses_claude_client(
        self, client, connected_session, sample_analysis
    ):
        """Test that provider='claude' routes to Claude client."""
        with patch('src.api.generate_routes.ClaudeClient') as mock_claude_class:
            mock_client = MagicMock()
            mock_claude_class.return_value = mock_client
            mock_client.generate_content.return_value = GenerationResult(
                success=True,
                content="Generated by Claude"
            )

            response = client.post(
                "/api/generate/ai-post",
                json={
                    "analysis": sample_analysis,
                    "style": "problem-solution",
                    "provider": "claude"
                },
                headers={"X-Session-ID": connected_session}
            )

            assert response.status_code == 200
            assert response.json()["success"] is True
            mock_claude_class.assert_called_once()

    def test_openai_rate_limit_returns_429(
        self, client, openai_connected_session, sample_analysis
    ):
        """Test that OpenAI rate limit returns 429 with retry-after header."""
        with patch('src.api.generate_routes.OpenAIClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = OpenAIGenerationResult(
                success=False,
                error="Rate limit exceeded. Please try again later.",
                retry_after=30
            )

            response = client.post(
                "/api/generate/ai-post",
                json={
                    "analysis": sample_analysis,
                    "style": "problem-solution",
                    "provider": "openai"
                },
                headers={"X-Session-ID": openai_connected_session}
            )

            assert response.status_code == 429
            assert "Retry-After" in response.headers
            assert response.headers["Retry-After"] == "30"

    def test_openai_error_returns_error_response(
        self, client, openai_connected_session, sample_analysis
    ):
        """Test that OpenAI API errors return error response."""
        with patch('src.api.generate_routes.OpenAIClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.generate_content.return_value = OpenAIGenerationResult(
                success=False,
                error="Failed to generate content. Please try again."
            )

            response = client.post(
                "/api/generate/ai-post",
                json={
                    "analysis": sample_analysis,
                    "style": "problem-solution",
                    "provider": "openai"
                },
                headers={"X-Session-ID": openai_connected_session}
            )

            assert response.status_code == 200  # 200 with success=False in body
            data = response.json()
            assert data["success"] is False
            assert data["error"] is not None
