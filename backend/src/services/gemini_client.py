"""Gemini and Imagen API client for AI-powered image generation.

This module provides a wrapper around the Google AI APIs for generating
images for LinkedIn posts using Gemini or Imagen models.

Supported models:
- Gemini: gemini-3-pro-image, gemini-2.5-flash-image (use generateContent)
- Imagen: imagen-4.0-ultra-generate-001, imagen-4.0-generate-001, imagen-4.0-fast-generate-001 (use generateImages)
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum

import httpx


class ImageDimension(str, Enum):
    """Supported image dimensions for LinkedIn."""
    LINK_POST = "1200x627"  # Standard link post
    SQUARE = "1080x1080"  # Square format
    LARGE_SQUARE = "1200x1200"  # Large square format


# Map dimensions to API aspect ratios
DIMENSION_TO_ASPECT_RATIO = {
    "1200x627": "16:9",    # LinkedIn link post (closest to 1.91:1)
    "1080x1080": "1:1",    # Square
    "1200x1200": "1:1",    # Large square
}

# Models that use the Imagen API (generateImages endpoint)
IMAGEN_MODELS = {
    "imagen-4.0-ultra-generate-001",
    "imagen-4.0-generate-001",
    "imagen-4.0-fast-generate-001",
}


class GeminiAPIError(Exception):
    """Base exception for Gemini API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class RateLimitError(GeminiAPIError):
    """Exception raised when API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


@dataclass
class ImageGenerationResult:
    """Result from Gemini image generation.

    Attributes:
        success: Whether generation was successful.
        image_base64: Base64-encoded image data (if successful).
        error: Error message (if failed).
        retry_after: Seconds to wait before retrying (for rate limits).
    """
    success: bool
    image_base64: Optional[str] = None
    error: Optional[str] = None
    retry_after: Optional[int] = None


class GeminiClient:
    """Client for interacting with Gemini API for image generation."""

    # Base URL for Gemini API
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    # Default model for image generation (Nano Banana Pro)
    DEFAULT_MODEL = "gemini-3-pro-image"

    # Default timeout in seconds
    DEFAULT_TIMEOUT = 60.0

    def __init__(self, api_key: str, timeout: Optional[float] = None):
        """Initialize the Gemini client.

        Args:
            api_key: The Google Gemini API key.
            timeout: Optional timeout in seconds for API requests.
        """
        self._api_key = api_key
        self._timeout = timeout or self.DEFAULT_TIMEOUT

    def _is_imagen_model(self, model: str) -> bool:
        """Check if the model is an Imagen model (uses different API)."""
        return model in IMAGEN_MODELS

    async def generate_image(
        self,
        prompt: str,
        dimensions: str = ImageDimension.LINK_POST.value,
        model: Optional[str] = None,
    ) -> ImageGenerationResult:
        """Generate an image using Gemini or Imagen API.

        Args:
            prompt: The text prompt describing the image to generate.
            dimensions: Image dimensions (1200x627, 1080x1080, or 1200x1200).
            model: Optional model override.

        Returns:
            ImageGenerationResult with success status and image data or error.

        Raises:
            GeminiAPIError: For general API errors.
            RateLimitError: When rate limit is exceeded.
        """
        # Validate dimensions
        valid_dimensions = {d.value for d in ImageDimension}
        if dimensions not in valid_dimensions:
            return ImageGenerationResult(
                success=False,
                error=f"Invalid dimensions '{dimensions}'. Must be one of: {', '.join(valid_dimensions)}"
            )

        model_name = model or self.DEFAULT_MODEL
        aspect_ratio = DIMENSION_TO_ASPECT_RATIO.get(dimensions, "16:9")

        # Use different API based on model type
        if self._is_imagen_model(model_name):
            return await self._generate_with_imagen(prompt, aspect_ratio, model_name)
        else:
            return await self._generate_with_gemini(prompt, aspect_ratio, model_name)

    async def _generate_with_gemini(
        self,
        prompt: str,
        aspect_ratio: str,
        model_name: str,
    ) -> ImageGenerationResult:
        """Generate image using Gemini API (generateContent endpoint)."""
        url = f"{self.BASE_URL}/models/{model_name}:generateContent"

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": aspect_ratio
                }
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self._api_key
                    }
                )

                self._handle_error_response(response)

                data = response.json()
                image_base64 = self._extract_image_from_gemini_response(data)

                if image_base64:
                    return ImageGenerationResult(success=True, image_base64=image_base64)
                else:
                    return ImageGenerationResult(
                        success=False,
                        error="No image data in response. Please try again."
                    )

        except RateLimitError:
            raise
        except GeminiAPIError:
            raise
        except httpx.TimeoutException:
            raise GeminiAPIError("Request timed out. Please try again.", status_code=None)
        except httpx.ConnectError:
            raise GeminiAPIError(
                "Could not connect to API. Please check your network connection.",
                status_code=None
            )
        except Exception:
            raise GeminiAPIError("Failed to generate image. Please try again.", status_code=None)

    async def _generate_with_imagen(
        self,
        prompt: str,
        aspect_ratio: str,
        model_name: str,
    ) -> ImageGenerationResult:
        """Generate image using Imagen API (predict endpoint)."""
        url = f"{self.BASE_URL}/models/{model_name}:predict"

        payload = {
            "instances": [
                {"prompt": prompt}
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": aspect_ratio
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self._api_key
                    }
                )

                self._handle_error_response(response)

                data = response.json()
                image_base64 = self._extract_image_from_imagen_response(data)

                if image_base64:
                    return ImageGenerationResult(success=True, image_base64=image_base64)
                else:
                    return ImageGenerationResult(
                        success=False,
                        error="No image data in response. Please try again."
                    )

        except RateLimitError:
            raise
        except GeminiAPIError:
            raise
        except httpx.TimeoutException:
            raise GeminiAPIError("Request timed out. Please try again.", status_code=None)
        except httpx.ConnectError:
            raise GeminiAPIError(
                "Could not connect to API. Please check your network connection.",
                status_code=None
            )
        except Exception:
            raise GeminiAPIError("Failed to generate image. Please try again.", status_code=None)

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from API."""
        if response.status_code == 429:
            retry_after = 60
            retry_header = response.headers.get("retry-after")
            if retry_header:
                try:
                    retry_after = int(retry_header)
                except (ValueError, TypeError):
                    pass
            raise RateLimitError(
                "Rate limit exceeded. Please try again later.",
                retry_after=retry_after
            )

        if response.status_code == 401:
            raise GeminiAPIError(
                "Invalid API key. Please reconnect with a valid API key.",
                status_code=401
            )

        if response.status_code == 403:
            raise GeminiAPIError(
                "API key does not have permission to generate images.",
                status_code=403
            )

        if response.status_code == 400:
            raise GeminiAPIError(
                "Invalid request. Please try again.",
                status_code=400
            )

        if response.status_code >= 400:
            raise GeminiAPIError(
                "Failed to generate image. Please try again.",
                status_code=response.status_code
            )

    def _extract_image_from_gemini_response(self, data: dict) -> Optional[str]:
        """Extract base64 image data from Gemini API response.

        Args:
            data: The JSON response from the API.

        Returns:
            Base64-encoded image string or None if not found.
        """
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return None

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])

            for part in parts:
                # Look for inline_data with image
                inline_data = part.get("inlineData")
                if inline_data:
                    mime_type = inline_data.get("mimeType", "")
                    if mime_type.startswith("image/"):
                        return inline_data.get("data")

            return None
        except (KeyError, IndexError, TypeError):
            return None

    def _extract_image_from_imagen_response(self, data: dict) -> Optional[str]:
        """Extract base64 image data from Imagen API response.

        Imagen API returns: {"predictions": [{"bytesBase64Encoded": "...", "mimeType": "image/png"}]}

        Args:
            data: The JSON response from the API.

        Returns:
            Base64-encoded image string or None if not found.
        """
        try:
            predictions = data.get("predictions", [])
            if not predictions:
                return None

            first_prediction = predictions[0]
            image_bytes = first_prediction.get("bytesBase64Encoded")

            if image_bytes:
                return image_bytes

            return None
        except (KeyError, IndexError, TypeError):
            return None

    async def validate_key(self) -> bool:
        """Validate the Gemini API key by making a lightweight API call.

        Returns:
            True if the API key is valid, False otherwise.
        """
        url = f"{self.BASE_URL}/models"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers={"x-goog-api-key": self._api_key}
                )

                if response.status_code == 200:
                    return True
                elif response.status_code == 401:
                    return False
                elif response.status_code == 403:
                    return False
                elif response.status_code == 429:
                    # Key is valid but rate limited
                    return True
                else:
                    return False

        except Exception:
            return False
