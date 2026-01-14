"""Tests for Gemini client service."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from src.services.gemini_client import (
    GeminiClient,
    ImageGenerationResult,
    GeminiAPIError,
    RateLimitError,
    ImageDimension
)


class TestGeminiClientGenerateImage:
    """Tests for GeminiClient.generate_image method."""

    @pytest.mark.asyncio
    async def test_generate_image_success(self):
        """Test successful image generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": "base64_encoded_image_data"
                        }
                    }]
                }
            }]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-api-key")
            result = await client.generate_image(
                prompt="A professional business image",
                dimensions="1200x627"
            )

            assert result.success is True
            assert result.image_base64 == "base64_encoded_image_data"
            assert result.error is None
            assert result.retry_after is None

    @pytest.mark.asyncio
    async def test_generate_image_with_square_dimensions(self):
        """Test image generation with square dimensions (1080x1080)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": "square_image_data"
                        }
                    }]
                }
            }]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-api-key")
            result = await client.generate_image(
                prompt="A professional business image",
                dimensions="1080x1080"
            )

            assert result.success is True
            assert result.image_base64 == "square_image_data"

            # Verify the dimensions were included in the request
            call_kwargs = mock_client.post.call_args.kwargs
            payload = call_kwargs["json"]
            prompt_text = payload["contents"][0]["parts"][0]["text"]
            assert "1080x1080" in prompt_text

    @pytest.mark.asyncio
    async def test_generate_image_with_large_square_dimensions(self):
        """Test image generation with large square dimensions (1200x1200)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": "large_square_image_data"
                        }
                    }]
                }
            }]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-api-key")
            result = await client.generate_image(
                prompt="A professional business image",
                dimensions="1200x1200"
            )

            assert result.success is True
            assert result.image_base64 == "large_square_image_data"

    @pytest.mark.asyncio
    async def test_generate_image_invalid_dimensions(self):
        """Test image generation with invalid dimensions returns error."""
        client = GeminiClient(api_key="test-api-key")
        result = await client.generate_image(
            prompt="A professional business image",
            dimensions="800x600"  # Invalid dimension
        )

        assert result.success is False
        assert "Invalid dimensions" in result.error
        assert "800x600" in result.error

    @pytest.mark.asyncio
    async def test_generate_image_authentication_error(self):
        """Test handling of authentication error (401)."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="invalid-key")

            with pytest.raises(GeminiAPIError) as exc_info:
                await client.generate_image(
                    prompt="Test prompt",
                    dimensions="1200x627"
                )

            assert "Invalid API key" in str(exc_info.value)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_generate_image_permission_denied(self):
        """Test handling of permission denied error (403)."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-key")

            with pytest.raises(GeminiAPIError) as exc_info:
                await client.generate_image(
                    prompt="Test prompt",
                    dimensions="1200x627"
                )

            assert "permission" in str(exc_info.value).lower()
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_generate_image_rate_limit_with_retry_after(self):
        """Test handling of rate limit error with retry-after header."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "45"}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-key")

            with pytest.raises(RateLimitError) as exc_info:
                await client.generate_image(
                    prompt="Test prompt",
                    dimensions="1200x627"
                )

            assert "Rate limit" in str(exc_info.value)
            assert exc_info.value.retry_after == 45

    @pytest.mark.asyncio
    async def test_generate_image_rate_limit_default_retry(self):
        """Test rate limit error uses default retry-after when not in headers."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-key")

            with pytest.raises(RateLimitError) as exc_info:
                await client.generate_image(
                    prompt="Test prompt",
                    dimensions="1200x627"
                )

            assert exc_info.value.retry_after == 60  # Default value

    @pytest.mark.asyncio
    async def test_generate_image_bad_request(self):
        """Test handling of bad request error (400)."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-key")

            with pytest.raises(GeminiAPIError) as exc_info:
                await client.generate_image(
                    prompt="Test prompt",
                    dimensions="1200x627"
                )

            assert "Invalid request" in str(exc_info.value)
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_generate_image_server_error(self):
        """Test handling of server error (500)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.headers = {}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-key")

            with pytest.raises(GeminiAPIError) as exc_info:
                await client.generate_image(
                    prompt="Test prompt",
                    dimensions="1200x627"
                )

            assert "Failed to generate" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_image_timeout(self):
        """Test handling of request timeout."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.TimeoutException("Request timed out")

            client = GeminiClient(api_key="test-key")

            with pytest.raises(GeminiAPIError) as exc_info:
                await client.generate_image(
                    prompt="Test prompt",
                    dimensions="1200x627"
                )

            assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generate_image_connection_error(self):
        """Test handling of connection error."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ConnectError("Connection failed")

            client = GeminiClient(api_key="test-key")

            with pytest.raises(GeminiAPIError) as exc_info:
                await client.generate_image(
                    prompt="Test prompt",
                    dimensions="1200x627"
                )

            assert "connect" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generate_image_no_image_in_response(self):
        """Test handling of response with no image data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "I cannot generate that image"
                    }]
                }
            }]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-key")
            result = await client.generate_image(
                prompt="Test prompt",
                dimensions="1200x627"
            )

            assert result.success is False
            assert "No image data" in result.error

    @pytest.mark.asyncio
    async def test_generate_image_empty_candidates(self):
        """Test handling of response with empty candidates."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": []
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-key")
            result = await client.generate_image(
                prompt="Test prompt",
                dimensions="1200x627"
            )

            assert result.success is False
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_generate_image_with_custom_model(self):
        """Test image generation with custom model."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": "custom_model_image"
                        }
                    }]
                }
            }]
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            client = GeminiClient(api_key="test-key")
            result = await client.generate_image(
                prompt="Test prompt",
                dimensions="1200x627",
                model="custom-image-model"
            )

            assert result.success is True

            # Verify custom model was used in URL
            call_args = mock_client.post.call_args
            url = call_args[0][0]
            assert "custom-image-model" in url

    @pytest.mark.asyncio
    async def test_generate_image_generic_exception(self):
        """Test handling of generic exception."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("Unknown error")

            client = GeminiClient(api_key="test-key")

            with pytest.raises(GeminiAPIError) as exc_info:
                await client.generate_image(
                    prompt="Test prompt",
                    dimensions="1200x627"
                )

            # Should not expose raw error message
            assert "Failed to generate" in str(exc_info.value)


class TestGeminiClientValidateKey:
    """Tests for GeminiClient.validate_key method."""

    @pytest.mark.asyncio
    async def test_validate_key_valid(self):
        """Test validate_key returns True for valid API key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            client = GeminiClient(api_key="valid-api-key")
            result = await client.validate_key()

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_key_invalid_401(self):
        """Test validate_key returns False for 401 error."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            client = GeminiClient(api_key="invalid-key")
            result = await client.validate_key()

            assert result is False

    @pytest.mark.asyncio
    async def test_validate_key_permission_denied_403(self):
        """Test validate_key returns False for 403 error."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            client = GeminiClient(api_key="no-perms-key")
            result = await client.validate_key()

            assert result is False

    @pytest.mark.asyncio
    async def test_validate_key_rate_limited_still_valid(self):
        """Test validate_key returns True when rate limited (key is still valid)."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            client = GeminiClient(api_key="rate-limited-key")
            result = await client.validate_key()

            assert result is True  # Key is valid, just rate limited

    @pytest.mark.asyncio
    async def test_validate_key_connection_error(self):
        """Test validate_key returns False on connection error."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.ConnectError("Connection failed")

            client = GeminiClient(api_key="valid-key")
            result = await client.validate_key()

            assert result is False

    @pytest.mark.asyncio
    async def test_validate_key_generic_exception(self):
        """Test validate_key returns False on generic exception."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Unknown error")

            client = GeminiClient(api_key="valid-key")
            result = await client.validate_key()

            assert result is False


class TestImageGenerationResult:
    """Tests for ImageGenerationResult dataclass."""

    def test_success_result(self):
        """Test creating a success result."""
        result = ImageGenerationResult(
            success=True,
            image_base64="base64_image_data"
        )

        assert result.success is True
        assert result.image_base64 == "base64_image_data"
        assert result.error is None
        assert result.retry_after is None

    def test_error_result(self):
        """Test creating an error result."""
        result = ImageGenerationResult(
            success=False,
            error="Something went wrong"
        )

        assert result.success is False
        assert result.image_base64 is None
        assert result.error == "Something went wrong"
        assert result.retry_after is None

    def test_rate_limit_result(self):
        """Test creating a rate limit result."""
        result = ImageGenerationResult(
            success=False,
            error="Rate limited",
            retry_after=60
        )

        assert result.success is False
        assert result.retry_after == 60


class TestGeminiAPIError:
    """Tests for GeminiAPIError exception."""

    def test_error_with_status_code(self):
        """Test GeminiAPIError with status code."""
        error = GeminiAPIError("Invalid API key", status_code=401)

        assert error.message == "Invalid API key"
        assert error.status_code == 401
        assert str(error) == "Invalid API key"

    def test_error_without_status_code(self):
        """Test GeminiAPIError without status code."""
        error = GeminiAPIError("Connection failed")

        assert error.message == "Connection failed"
        assert error.status_code is None


class TestRateLimitError:
    """Tests for RateLimitError exception."""

    def test_rate_limit_error_with_retry_after(self):
        """Test RateLimitError with custom retry_after."""
        error = RateLimitError("Rate limited", retry_after=45)

        assert error.message == "Rate limited"
        assert error.retry_after == 45
        assert error.status_code == 429

    def test_rate_limit_error_default_retry(self):
        """Test RateLimitError with default retry_after."""
        error = RateLimitError("Rate limited")

        assert error.retry_after == 60  # Default


class TestImageDimension:
    """Tests for ImageDimension enum."""

    def test_link_post_dimension(self):
        """Test LINK_POST dimension value."""
        assert ImageDimension.LINK_POST.value == "1200x627"

    def test_square_dimension(self):
        """Test SQUARE dimension value."""
        assert ImageDimension.SQUARE.value == "1080x1080"

    def test_large_square_dimension(self):
        """Test LARGE_SQUARE dimension value."""
        assert ImageDimension.LARGE_SQUARE.value == "1200x1200"
