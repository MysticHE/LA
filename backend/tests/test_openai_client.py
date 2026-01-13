"""Tests for OpenAI client service."""

import pytest
from unittest.mock import patch, MagicMock
import httpx

from src.services.openai_client import OpenAIClient, GenerationResult


class TestOpenAIClientValidateKey:
    """Tests for OpenAIClient.validate_key method."""

    def test_validate_key_valid(self):
        """Test validate_key returns True for valid API key."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            # Mock successful models.list call
            mock_client.models.list.return_value = MagicMock()

            client = OpenAIClient(api_key="sk-test-valid-key-123456789012345678901234567890")
            result = client.validate_key()

            assert result is True
            mock_client.models.list.assert_called_once()

    def test_validate_key_invalid_authentication_error(self):
        """Test validate_key returns False for invalid API key."""
        import openai

        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_client.models.list.side_effect = openai.AuthenticationError(
                message="Invalid API Key",
                response=MagicMock(status_code=401),
                body={}
            )

            client = OpenAIClient(api_key="sk-invalid-key")
            result = client.validate_key()

            assert result is False

    def test_validate_key_permission_denied(self):
        """Test validate_key returns False for permission denied."""
        import openai

        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_client.models.list.side_effect = openai.PermissionDeniedError(
                message="Permission denied",
                response=MagicMock(status_code=403),
                body={}
            )

            client = OpenAIClient(api_key="sk-no-perms-key")
            result = client.validate_key()

            assert result is False

    def test_validate_key_rate_limited_still_valid(self):
        """Test validate_key returns True when rate limited (key is still valid)."""
        import openai

        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_response = MagicMock()
            mock_response.headers = {"retry-after": "60"}
            mock_client.models.list.side_effect = openai.RateLimitError(
                message="Rate limited",
                response=mock_response,
                body={}
            )

            client = OpenAIClient(api_key="sk-rate-limited-key")
            result = client.validate_key()

            assert result is True  # Key is valid, just rate limited

    def test_validate_key_connection_error(self):
        """Test validate_key returns False on connection error."""
        import openai

        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_request = httpx.Request("GET", "https://api.openai.com/v1/models")
            mock_client.models.list.side_effect = openai.APIConnectionError(
                request=mock_request
            )

            client = OpenAIClient(api_key="sk-valid-key")
            result = client.validate_key()

            assert result is False

    def test_validate_key_generic_exception(self):
        """Test validate_key returns False on unknown error."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.models.list.side_effect = Exception("Unknown error")

            client = OpenAIClient(api_key="sk-valid-key")
            result = client.validate_key()

            assert result is False


class TestOpenAIClientGenerateContent:
    """Tests for OpenAIClient.generate_content method."""

    def test_generate_content_success(self):
        """Test successful content generation."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            # Mock response with message content
            mock_message = MagicMock()
            mock_message.content = "Generated LinkedIn post content"
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response

            client = OpenAIClient(api_key="sk-test-key")
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
        import openai

        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
                message="Invalid API Key",
                response=MagicMock(status_code=401),
                body={}
            )

            client = OpenAIClient(api_key="invalid-key")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert "Invalid API key" in result.error
            assert result.content is None

    def test_generate_content_rate_limit_error_with_retry(self):
        """Test handling of rate limit error with retry-after."""
        import openai

        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            # Mock rate limit with retry-after header
            mock_response = MagicMock()
            mock_response.headers = {"retry-after": "45"}
            mock_error = openai.RateLimitError(
                message="Rate limited",
                response=mock_response,
                body={}
            )
            mock_client.chat.completions.create.side_effect = mock_error

            client = OpenAIClient(api_key="sk-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert "Rate limit" in result.error
            assert result.retry_after == 45

    def test_generate_content_rate_limit_default_retry(self):
        """Test rate limit error uses default retry-after when not in headers."""
        import openai

        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            # Mock rate limit without retry-after header
            mock_response = MagicMock()
            mock_response.headers = {}
            mock_error = openai.RateLimitError(
                message="Rate limited",
                response=mock_response,
                body={}
            )
            mock_client.chat.completions.create.side_effect = mock_error

            client = OpenAIClient(api_key="sk-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert result.retry_after == 60  # Default value

    def test_generate_content_permission_denied_error(self):
        """Test handling of permission denied error."""
        import openai

        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = openai.PermissionDeniedError(
                message="Permission denied",
                response=MagicMock(status_code=403),
                body={}
            )

            client = OpenAIClient(api_key="sk-no-perms")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert "permission" in result.error.lower()

    def test_generate_content_connection_error(self):
        """Test handling of API connection error."""
        import openai

        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
            mock_client.chat.completions.create.side_effect = openai.APIConnectionError(
                request=mock_request
            )

            client = OpenAIClient(api_key="sk-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert "connect" in result.error.lower()

    def test_generate_content_bad_request_error(self):
        """Test handling of bad request error."""
        import openai

        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = openai.BadRequestError(
                message="Bad request",
                response=MagicMock(status_code=400),
                body={}
            )

            client = OpenAIClient(api_key="sk-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            assert "Invalid request" in result.error

    def test_generate_content_generic_exception(self):
        """Test handling of generic exception."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("Unknown error")

            client = OpenAIClient(api_key="sk-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is False
            # Should not expose raw error message
            assert "Failed to generate content" in result.error

    def test_generate_content_with_custom_model(self):
        """Test generation with custom model override."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_message = MagicMock()
            mock_message.content = "Content"
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response

            client = OpenAIClient(api_key="sk-valid")
            client.generate_content(
                system_prompt="System",
                user_prompt="User",
                model="gpt-4"
            )

            # Verify custom model was used
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["model"] == "gpt-4"

    def test_generate_content_with_custom_max_tokens(self):
        """Test generation with custom max_tokens override."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_message = MagicMock()
            mock_message.content = "Content"
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response

            client = OpenAIClient(api_key="sk-valid")
            client.generate_content(
                system_prompt="System",
                user_prompt="User",
                max_tokens=500
            )

            # Verify custom max_tokens was used
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["max_tokens"] == 500

    def test_generate_content_empty_response(self):
        """Test handling of empty response content."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            # Mock empty content response
            mock_message = MagicMock()
            mock_message.content = ""
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response

            client = OpenAIClient(api_key="sk-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is True
            assert result.content is None  # Empty string stripped becomes None

    def test_generate_content_no_choices(self):
        """Test handling of response with no choices."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            # Mock response with no choices
            mock_response = MagicMock()
            mock_response.choices = []
            mock_client.chat.completions.create.return_value = mock_response

            client = OpenAIClient(api_key="sk-valid")
            result = client.generate_content(
                system_prompt="System",
                user_prompt="User"
            )

            assert result.success is True
            assert result.content is None


class TestOpenAIClientGenerateLinkedInPost:
    """Tests for OpenAIClient.generate_linkedin_post method."""

    def test_generate_linkedin_post_success(self):
        """Test successful LinkedIn post generation."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_message = MagicMock()
            mock_message.content = "Great LinkedIn post about the project!"
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response

            client = OpenAIClient(api_key="sk-valid")
            analysis = {
                "repo_name": "awesome-project",
                "description": "An awesome project",
                "language": "Python",
                "stars": 100,
                "forks": 20,
                "tech_stack": [{"name": "FastAPI"}, {"name": "PostgreSQL"}],
                "features": [{"name": "Feature 1", "description": "Does something"}],
                "readme_summary": "This is a great project"
            }

            result = client.generate_linkedin_post(
                analysis=analysis,
                style="problem-solution"
            )

            assert result.success is True
            assert result.content == "Great LinkedIn post about the project!"

    def test_generate_linkedin_post_with_custom_model(self):
        """Test LinkedIn post generation with custom model."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_message = MagicMock()
            mock_message.content = "Content"
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response

            client = OpenAIClient(api_key="sk-valid")
            analysis = {"repo_name": "test-repo"}

            client.generate_linkedin_post(
                analysis=analysis,
                style="tips-learnings",
                model="gpt-3.5-turbo"
            )

            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["model"] == "gpt-3.5-turbo"

    def test_generate_linkedin_post_different_styles(self):
        """Test that different styles produce different system prompts."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_message = MagicMock()
            mock_message.content = "Content"
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response

            client = OpenAIClient(api_key="sk-valid")
            analysis = {"repo_name": "test-repo"}

            styles = ["problem-solution", "tips-learnings", "technical-showcase"]
            system_prompts = []

            for style in styles:
                client.generate_linkedin_post(analysis=analysis, style=style)
                call_kwargs = mock_client.chat.completions.create.call_args.kwargs
                system_prompts.append(call_kwargs["messages"][0]["content"])

            # Verify each style produces a different system prompt
            assert len(set(system_prompts)) == 3

    def test_generate_linkedin_post_minimal_analysis(self):
        """Test LinkedIn post generation with minimal analysis data."""
        with patch('src.services.openai_client.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client

            mock_message = MagicMock()
            mock_message.content = "Minimal content post"
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response

            client = OpenAIClient(api_key="sk-valid")
            # Minimal analysis - missing most fields
            analysis = {}

            result = client.generate_linkedin_post(
                analysis=analysis,
                style="problem-solution"
            )

            assert result.success is True
            # Verify defaults are used in the prompt
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            user_prompt = call_kwargs["messages"][1]["content"]
            assert "Unknown Project" in user_prompt


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
