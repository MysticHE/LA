"""Prompt validation and sanitization for image generation.

This module provides security-focused validation and sanitization of user prompts
to prevent prompt injection attacks and filter malicious content patterns.

OWASP A03 Compliance: Input validation and sanitization
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class PromptValidationResult:
    """Result of prompt validation."""
    is_valid: bool
    sanitized_prompt: Optional[str]
    error_message: Optional[str]
    detected_patterns: list[str]


class PromptValidator:
    """Validates and sanitizes prompts for image generation.

    Detects and handles:
    - Prompt injection attempts
    - Jailbreak patterns
    - Malicious instruction overrides
    - Harmful content patterns
    """

    # Patterns that attempt to override or manipulate AI behavior
    INJECTION_PATTERNS = [
        # Ignore/override instructions - with or without "previous/prior/above"
        (r"ignore\s+(all\s+)?(previous|prior|above)?\s*(instructions?|prompts?|rules?)", "instruction_override"),
        (r"disregard\s+(all\s+)?(previous|prior|above)?\s*(instructions?|prompts?|rules?)", "instruction_override"),
        (r"forget\s+(all\s+)?(previous|prior|above)?\s*(instructions?|prompts?|rules?)", "instruction_override"),
        # System prompt manipulation
        (r"system\s*:\s*", "system_prompt_injection"),
        (r"\[system\]", "system_prompt_injection"),
        (r"<\s*system\s*>", "system_prompt_injection"),
        (r"<\|system\|>", "system_prompt_injection"),
        # Role manipulation
        (r"you\s+are\s+(now\s+)?(a|an|the)\s+(new|different)", "role_manipulation"),
        (r"act\s+as\s+(if\s+)?you\s+(are|were)\s+(a|an)", "role_manipulation"),
        (r"pretend\s+(to\s+be|you\s+are)", "role_manipulation"),
        # Jailbreak patterns
        (r"do\s+anything\s+now", "jailbreak_attempt"),
        (r"dan\s+mode", "jailbreak_attempt"),
        (r"developer\s+mode", "jailbreak_attempt"),
        (r"god\s+mode", "jailbreak_attempt"),
        (r"unrestricted\s+mode", "jailbreak_attempt"),
        (r"bypass\s+(safety|security|filter|content)", "jailbreak_attempt"),
        (r"remove\s+(safety|security|filter|content)\s*(restrictions?|limits?)?", "jailbreak_attempt"),
        # Output manipulation
        (r"(only|just)\s+output\s*(the)?", "output_manipulation"),
        (r"print\s+(only|just)", "output_manipulation"),
        (r"respond\s+with\s+(only|just)", "output_manipulation"),
    ]

    # Patterns for harmful or inappropriate content requests
    HARMFUL_CONTENT_PATTERNS = [
        # Violence
        (r"\b(gore|violent|bloody|murder|kill|torture)\b", "violent_content"),
        (r"\b(weapon|gun|knife|bomb)\s*(making|tutorial|how\s*to)", "weapon_content"),
        # Explicit content
        (r"\b(nsfw|explicit|pornographic|sexual)\b", "explicit_content"),
        (r"\b(nude|naked|erotic)\b", "explicit_content"),
        # Hate/discrimination
        (r"\b(racist|sexist|homophobic|antisemitic)\b", "hate_content"),
        # Illegal activities
        (r"\b(hack|crack|pirate|steal)\s+(password|account|data|software)", "illegal_activity"),
        (r"\b(drug)\s*(dealer|dealing|making|synthesis)", "illegal_activity"),
        # Misinformation
        (r"\b(fake|forged|counterfeit)\s+(id|passport|document|money)", "forgery_content"),
    ]

    # Characters and sequences that should be escaped or removed
    ESCAPE_PATTERNS = [
        (r"\\n", " "),  # Literal \n
        (r"\\r", " "),  # Literal \r
        (r"\\t", " "),  # Literal \t
        (r"[\x00-\x08\x0b\x0c\x0e-\x1f]", ""),  # Control characters
    ]

    def __init__(self, strict_mode: bool = True):
        """Initialize the prompt validator.

        Args:
            strict_mode: If True, reject prompts with any detected patterns.
                        If False, attempt to sanitize and allow.
        """
        self.strict_mode = strict_mode
        # Compile all patterns for efficiency
        self._compiled_injection = [
            (re.compile(pattern, re.IGNORECASE), label)
            for pattern, label in self.INJECTION_PATTERNS
        ]
        self._compiled_harmful = [
            (re.compile(pattern, re.IGNORECASE), label)
            for pattern, label in self.HARMFUL_CONTENT_PATTERNS
        ]
        self._compiled_escape = [
            (re.compile(pattern), replacement)
            for pattern, replacement in self.ESCAPE_PATTERNS
        ]

    def validate(self, prompt: str) -> PromptValidationResult:
        """Validate and optionally sanitize a prompt.

        Args:
            prompt: The user-provided prompt to validate.

        Returns:
            PromptValidationResult with validation status and sanitized prompt.
        """
        if not prompt or not prompt.strip():
            return PromptValidationResult(
                is_valid=False,
                sanitized_prompt=None,
                error_message="Prompt cannot be empty",
                detected_patterns=[]
            )

        detected_patterns: list[str] = []
        working_prompt = prompt.strip()

        # Check for injection patterns
        for pattern, label in self._compiled_injection:
            if pattern.search(working_prompt):
                detected_patterns.append(label)

        # Check for harmful content patterns
        for pattern, label in self._compiled_harmful:
            if pattern.search(working_prompt):
                detected_patterns.append(label)

        # If patterns detected and strict mode, reject
        if detected_patterns and self.strict_mode:
            return PromptValidationResult(
                is_valid=False,
                sanitized_prompt=None,
                error_message=f"Prompt contains prohibited patterns: {', '.join(set(detected_patterns))}",
                detected_patterns=detected_patterns
            )

        # Sanitize the prompt
        sanitized = self._sanitize(working_prompt)

        # If patterns detected but not strict mode, return sanitized with warning
        if detected_patterns:
            return PromptValidationResult(
                is_valid=True,
                sanitized_prompt=sanitized,
                error_message=None,
                detected_patterns=detected_patterns
            )

        return PromptValidationResult(
            is_valid=True,
            sanitized_prompt=sanitized,
            error_message=None,
            detected_patterns=[]
        )

    def _sanitize(self, prompt: str) -> str:
        """Sanitize a prompt by removing/escaping dangerous sequences.

        Args:
            prompt: The prompt to sanitize.

        Returns:
            Sanitized prompt string.
        """
        result = prompt

        # Apply escape patterns
        for pattern, replacement in self._compiled_escape:
            result = pattern.sub(replacement, result)

        # Normalize whitespace
        result = " ".join(result.split())

        # Trim excessive length (additional safety)
        max_chars = 2000  # Reasonable max for image prompt
        if len(result) > max_chars:
            result = result[:max_chars].rsplit(" ", 1)[0] + "..."

        return result

    def is_safe(self, prompt: str) -> bool:
        """Quick check if a prompt is safe without full validation.

        Args:
            prompt: The prompt to check.

        Returns:
            True if the prompt appears safe, False otherwise.
        """
        result = self.validate(prompt)
        return result.is_valid and not result.detected_patterns
