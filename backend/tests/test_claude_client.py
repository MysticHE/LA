"""Tests for Claude client service."""

import pytest
from unittest.mock import patch, MagicMock
import httpx

from src.services.claude_client import ClaudeClient, GenerationResult


class TestClaudeClient:
    """Tests for ClaudeClient class."""

    def test_generate_content_success(self):
        """Test successful content generation."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            # Mock response with text block
            mock_text_block = MagicMock()
            mock_text_block.text = "Generated LinkedIn post content"
            mock_response = MagicMock()
            mock_response.content = [mock_text_block]
            mock_client.messages.create.return_value = mock_response

            client = ClaudeClient(api_key="sk-ant-test-key")
            result = client.generate_content(
                system_prompt="You are a LinkedIn writer",
                user_prompt="Write a post about my project"
            )

            assert result.success is True
            assert result.content == "Generated LinkedIn post content"
            assert result.error is None
            assert result.retry_after is None

    def test_generate_content_authentication_error(self):
        """Test handling of authentication error."""
        import anthropic

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = anthropic.AuthenticationError(
                message="Invalid API Key",
                response=MagicMock(status_code=401),
                body={}
            )

            client = ClaudeClient(api_key="invalid-key")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert "Invalid API key" in result.error
            assert result.content is None

    def test_generate_content_rate_limit_error(self):
        """Test handling of rate limit error with retry-after."""
        import anthropic

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            # Mock rate limit with retry-after header
            mock_response = MagicMock()
            mock_response.headers = {"retry-after": "45"}
            mock_error = anthropic.RateLimitError(
                message="Rate limited",
                response=mock_response,
                body={}
            )
            mock_client.messages.create.side_effect = mock_error

            client = ClaudeClient(api_key="sk-ant-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert "Rate limit" in result.error
            assert result.retry_after == 45

    def test_generate_content_rate_limit_default_retry(self):
        """Test rate limit error uses default retry-after when not in headers."""
        import anthropic

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            # Mock rate limit without retry-after header
            mock_response = MagicMock()
            mock_response.headers = {}
            mock_error = anthropic.RateLimitError(
                message="Rate limited",
                response=mock_response,
                body={}
            )
            mock_client.messages.create.side_effect = mock_error

            client = ClaudeClient(api_key="sk-ant-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert result.retry_after == 60  # Default value

    def test_generate_content_permission_denied_error(self):
        """Test handling of permission denied error."""
        import anthropic

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = anthropic.PermissionDeniedError(
                message="Permission denied",
                response=MagicMock(status_code=403),
                body={}
            )

            client = ClaudeClient(api_key="sk-ant-no-perms")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert "permission" in result.error.lower()

    def test_generate_content_connection_error(self):
        """Test handling of API connection error."""
        import anthropic

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
            mock_client.messages.create.side_effect = anthropic.APIConnectionError(
                request=mock_request
            )

            client = ClaudeClient(api_key="sk-ant-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert "connect" in result.error.lower()

    def test_generate_content_bad_request_error(self):
        """Test handling of bad request error."""
        import anthropic

        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = anthropic.BadRequestError(
                message="Bad request",
                response=MagicMock(status_code=400),
                body={}
            )

            client = ClaudeClient(api_key="sk-ant-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert "Invalid request" in result.error

    def test_generate_content_generic_exception(self):
        """Test handling of generic exception."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("Unknown error")

            client = ClaudeClient(api_key="sk-ant-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            # Should not expose raw error message
            assert "Failed to generate content" in result.error

    def test_generate_content_with_custom_model(self):
        """Test generation with custom model override."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            mock_text_block = MagicMock()
            mock_text_block.text = "Content"
            mock_response = MagicMock()
            mock_response.content = [mock_text_block]
            mock_client.messages.create.return_value = mock_response

            client = ClaudeClient(api_key="sk-ant-valid")
            client.generate_content(
                system_prompt="System",
                user_prompt="User",
                model="claude-3-sonnet-20240229"
            )

            # Verify custom model was used
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["model"] == "claude-3-sonnet-20240229"

    def test_generate_content_with_custom_max_tokens(self):
        """Test generation with custom max_tokens override."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            mock_text_block = MagicMock()
            mock_text_block.text = "Content"
            mock_response = MagicMock()
            mock_response.content = [mock_text_block]
            mock_client.messages.create.return_value = mock_response

            client = ClaudeClient(api_key="sk-ant-valid")
            client.generate_content(
                system_prompt="System",
                user_prompt="User",
                max_tokens=500
            )

            # Verify custom max_tokens was used
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["max_tokens"] == 500

    def test_generate_content_empty_response(self):
        """Test handling of empty response content."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            # Mock empty content response
            mock_response = MagicMock()
            mock_response.content = []
            mock_client.messages.create.return_value = mock_response

            client = ClaudeClient(api_key="sk-ant-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is True
            assert result.content is None  # Empty string stripped becomes None


class TestGenerationResult:
    """Tests for GenerationResult dataclass."""

    def test_success_result(self):
        """Test creating a success result."""
        result = GenerationResult(
            success=True,
            content="Generated content"
        )

        assert result.success is True
        assert result.content == "Generated content"
        assert result.error is None
        assert result.retry_after is None

    def test_error_result(self):
        """Test creating an error result."""
        result = GenerationResult(
            success=False,
            error="Something went wrong"
        )

        assert result.success is False
        assert result.content is None
        assert result.error == "Something went wrong"

    def test_rate_limit_result(self):
        """Test creating a rate limit result."""
        result = GenerationResult(
            success=False,
            error="Rate limited",
            retry_after=60
        )

        assert result.success is False
        assert result.retry_after == 60
