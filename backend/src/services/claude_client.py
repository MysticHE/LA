"""Claude API client for AI-powered content generation.

This module provides a wrapper around the Anthropic SDK for generating
LinkedIn post content using Claude AI.
"""

from typing import Optional
from dataclasses import dataclass

import anthropic


@dataclass
class GenerationResult:
    """Result from Claude content generation.

    Attributes:
        success: Whether generation was successful.
        content: The generated content (if successful).
        error: Error message (if failed).
        retry_after: Seconds to wait before retrying (for rate limits).
    """
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    retry_after: Optional[int] = None


class ClaudeClient:
    """Client for interacting with Claude API for content generation."""

    # Default model for content generation
    DEFAULT_MODEL = "claude-3-haiku-20240307"

    # Maximum tokens for generation (LinkedIn posts are max 3000 chars)
    MAX_TOKENS = 1500

    def __init__(self, api_key: str):
        """Initialize the Claude client.

        Args:
            api_key: The Anthropic API key.
        """
        self._client = anthropic.Anthropic(api_key=api_key)

    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> GenerationResult:
        """Generate content using Claude.

        Args:
            system_prompt: The system prompt for Claude.
            user_prompt: The user message/request.
            model: Optional model override. Defaults to claude-3-haiku.
            max_tokens: Optional max tokens override. Defaults to 1500.

        Returns:
            GenerationResult with success status and content or error.
        """
        try:
            response = self._client.messages.create(
                model=model or self.DEFAULT_MODEL,
                max_tokens=max_tokens or self.MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # Extract text content from response
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            return GenerationResult(
                success=True,
                content=content.strip() if content else None,
            )

        except anthropic.AuthenticationError:
            return GenerationResult(
                success=False,
                error="Invalid API key. Please reconnect with a valid Claude API key.",
            )

        except anthropic.PermissionDeniedError:
            return GenerationResult(
                success=False,
                error="API key does not have permission to generate content.",
            )

        except anthropic.RateLimitError as e:
            # Try to extract retry-after from headers if available
            retry_after = 60  # Default to 60 seconds
            if hasattr(e, "response") and e.response is not None:
                retry_header = e.response.headers.get("retry-after")
                if retry_header:
                    try:
                        retry_after = int(retry_header)
                    except (ValueError, TypeError):
                        pass

            return GenerationResult(
                success=False,
                error="Rate limit exceeded. Please try again later.",
                retry_after=retry_after,
            )

        except anthropic.APIConnectionError:
            return GenerationResult(
                success=False,
                error="Could not connect to Claude API. Please check your network connection.",
            )

        except anthropic.BadRequestError as e:
            return GenerationResult(
                success=False,
                error="Invalid request to Claude API. Please try again.",
            )

        except Exception:
            # Don't expose raw error messages
            return GenerationResult(
                success=False,
                error="Failed to generate content. Please try again.",
            )
