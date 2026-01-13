"""OpenAI API client for AI-powered content generation.

This module provides a wrapper around the OpenAI SDK for generating
LinkedIn post content using GPT models, and validating API keys.
"""

from typing import Optional
from dataclasses import dataclass

import openai
from openai import OpenAI


@dataclass
class GenerationResult:
    """Result from OpenAI content generation.

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


class OpenAIClient:
    """Client for interacting with OpenAI API for content generation and key validation."""

    # Default model for content generation
    DEFAULT_MODEL = "gpt-4o"

    # Maximum tokens for generation (LinkedIn posts are max 3000 chars)
    MAX_TOKENS = 1500

    def __init__(self, api_key: str):
        """Initialize the OpenAI client.

        Args:
            api_key: The OpenAI API key.
        """
        self._api_key = api_key
        self._client = OpenAI(api_key=api_key)

    def validate_key(self) -> bool:
        """Validate the OpenAI API key by making a lightweight API call.

        Uses the models.list endpoint which is fast and cheap.

        Returns:
            True if the API key is valid, False otherwise.
        """
        try:
            # Make a lightweight call to list models
            self._client.models.list()
            return True
        except openai.AuthenticationError:
            return False
        except openai.PermissionDeniedError:
            return False
        except openai.RateLimitError:
            # Key is valid but rate limited - still valid
            return True
        except openai.APIConnectionError:
            # Can't verify - treat as invalid for safety
            return False
        except Exception:
            return False

    def generate_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> GenerationResult:
        """Generate content using OpenAI GPT models.

        Args:
            system_prompt: The system prompt for the model.
            user_prompt: The user message/request.
            model: Optional model override. Defaults to gpt-4o.
            max_tokens: Optional max tokens override. Defaults to 1500.

        Returns:
            GenerationResult with success status and content or error.
        """
        try:
            response = self._client.chat.completions.create(
                model=model or self.DEFAULT_MODEL,
                max_tokens=max_tokens or self.MAX_TOKENS,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract text content from response
            content = ""
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content or ""

            return GenerationResult(
                success=True,
                content=content.strip() if content else None,
            )

        except openai.AuthenticationError:
            return GenerationResult(
                success=False,
                error="Invalid API key. Please reconnect with a valid OpenAI API key.",
            )

        except openai.PermissionDeniedError:
            return GenerationResult(
                success=False,
                error="API key does not have permission to generate content.",
            )

        except openai.RateLimitError as e:
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

        except openai.APIConnectionError:
            return GenerationResult(
                success=False,
                error="Could not connect to OpenAI API. Please check your network connection.",
            )

        except openai.BadRequestError:
            return GenerationResult(
                success=False,
                error="Invalid request to OpenAI API. Please try again.",
            )

        except Exception:
            # Don't expose raw error messages
            return GenerationResult(
                success=False,
                error="Failed to generate content. Please try again.",
            )

    def generate_linkedin_post(
        self,
        analysis: dict,
        style: str,
        model: Optional[str] = None,
    ) -> GenerationResult:
        """Generate a LinkedIn post from repository analysis.

        Args:
            analysis: Repository analysis dictionary with repo_name, description, etc.
            style: Post style (problem-solution, tips-learnings, technical-showcase).
            model: Optional model override.

        Returns:
            GenerationResult with success status and generated post content.
        """
        # Build system prompt based on style
        system_prompt = self._build_system_prompt(style)

        # Build user prompt from analysis
        user_prompt = self._build_user_prompt(analysis)

        return self.generate_content(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
        )

    def _build_system_prompt(self, style: str) -> str:
        """Build system prompt based on post style.

        Args:
            style: The post style to use.

        Returns:
            System prompt string.
        """
        base_prompt = """You are an expert LinkedIn content creator who writes engaging technical posts about software projects.
Your posts are professional, authentic, and optimized for LinkedIn's algorithm and audience engagement.
Keep posts concise (under 3000 characters) with clear formatting and appropriate use of line breaks.
Do not use hashtags excessively - 3-5 relevant hashtags maximum at the end."""

        style_instructions = {
            "problem-solution": """Focus on the problem-solution narrative:
- Start with a relatable problem developers face
- Show how this project solves it
- Include specific benefits and outcomes
- End with a call-to-action to check out the project""",

            "tips-learnings": """Focus on tips and learnings:
- Share key insights gained from this project
- Present 3-5 practical takeaways
- Make it educational and valuable
- Encourage engagement by asking about others' experiences""",

            "technical-showcase": """Focus on technical showcase:
- Highlight the technical architecture and design decisions
- Mention specific technologies and why they were chosen
- Share interesting implementation details
- Appeal to fellow developers' curiosity"""
        }

        return f"{base_prompt}\n\n{style_instructions.get(style, style_instructions['problem-solution'])}"

    def _build_user_prompt(self, analysis: dict) -> str:
        """Build user prompt from repository analysis.

        Args:
            analysis: Repository analysis dictionary.

        Returns:
            User prompt string.
        """
        repo_name = analysis.get("repo_name", "Unknown Project")
        description = analysis.get("description", "No description available")
        language = analysis.get("language", "Unknown")
        stars = analysis.get("stars", 0)
        forks = analysis.get("forks", 0)

        tech_stack = analysis.get("tech_stack", [])
        tech_list = ", ".join([t.get("name", "") for t in tech_stack if t.get("name")]) or "Not specified"

        features = analysis.get("features", [])
        feature_list = "\n".join([f"- {f.get('name', '')}: {f.get('description', '')}" for f in features]) or "No features listed"

        readme_summary = analysis.get("readme_summary", "No README summary available")

        return f"""Generate a LinkedIn post about this GitHub project:

**Project:** {repo_name}
**Description:** {description}
**Main Language:** {language}
**Stars:** {stars} | **Forks:** {forks}
**Tech Stack:** {tech_list}

**Key Features:**
{feature_list}

**README Summary:**
{readme_summary}

Write an engaging LinkedIn post that will resonate with the developer community."""
