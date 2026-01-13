"""Tests for Provider and Model parameter validation.

These tests ensure that only allowed values are accepted for:
- Provider enum: ['claude', 'openai']
- OpenAIModel enum: ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo']
"""

import pytest
from pydantic import BaseModel, ValidationError

from src.models.schemas import Provider, PostStyle
from src.models.openai_schemas import OpenAIModel


class TestProviderEnum:
    """Tests for Provider enum validation."""

    def test_provider_claude_value(self):
        """Test that claude provider value is correct."""
        assert Provider.CLAUDE.value == "claude"

    def test_provider_openai_value(self):
        """Test that openai provider value is correct."""
        assert Provider.OPENAI.value == "openai"

    def test_provider_only_has_two_values(self):
        """Test that Provider enum only has 'claude' and 'openai' values."""
        allowed_values = {p.value for p in Provider}
        assert allowed_values == {"claude", "openai"}
        assert len(list(Provider)) == 2

    def test_provider_is_string_enum(self):
        """Test that Provider values can be used as strings."""
        assert str(Provider.CLAUDE.value) == "claude"
        assert str(Provider.OPENAI.value) == "openai"


class TestProviderValidationInModel:
    """Tests for Provider validation when used in Pydantic models."""

    def test_valid_provider_claude(self):
        """Test that 'claude' is accepted as provider."""
        class TestModel(BaseModel):
            provider: Provider

        model = TestModel(provider="claude")
        assert model.provider == Provider.CLAUDE

    def test_valid_provider_openai(self):
        """Test that 'openai' is accepted as provider."""
        class TestModel(BaseModel):
            provider: Provider

        model = TestModel(provider="openai")
        assert model.provider == Provider.OPENAI

    def test_invalid_provider_returns_400_style_error(self):
        """Test that invalid provider raises ValidationError with helpful message.

        GIVEN provider parameter
        WHEN not in ['claude', 'openai']
        THEN return 400 Bad Request (Pydantic validation error)
        """
        class TestModel(BaseModel):
            provider: Provider

        with pytest.raises(ValidationError) as exc_info:
            TestModel(provider="invalid_provider")

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert errors[0]["loc"] == ("provider",)
        # Pydantic includes allowed values in error message for enums
        error_msg = str(errors[0]["msg"]).lower()
        assert "claude" in error_msg or "openai" in error_msg or "input should be" in error_msg

    def test_invalid_provider_gpt(self):
        """Test that 'gpt' alone is not a valid provider."""
        class TestModel(BaseModel):
            provider: Provider

        with pytest.raises(ValidationError):
            TestModel(provider="gpt")

    def test_invalid_provider_anthropic(self):
        """Test that 'anthropic' is not a valid provider (must use 'claude')."""
        class TestModel(BaseModel):
            provider: Provider

        with pytest.raises(ValidationError):
            TestModel(provider="anthropic")

    def test_provider_case_sensitive(self):
        """Test that provider values are case-sensitive."""
        class TestModel(BaseModel):
            provider: Provider

        # 'Claude' with capital C should fail
        with pytest.raises(ValidationError):
            TestModel(provider="Claude")

        # 'OPENAI' uppercase should fail
        with pytest.raises(ValidationError):
            TestModel(provider="OPENAI")


class TestOpenAIModelValidationWithAllowedValues:
    """Tests for OpenAI model validation ensuring only allowed values are accepted."""

    def test_model_gpt_4o_is_valid(self):
        """Test that 'gpt-4o' is accepted."""
        assert OpenAIModel("gpt-4o") == OpenAIModel.GPT_4O

    def test_model_gpt_4_is_valid(self):
        """Test that 'gpt-4' is accepted."""
        assert OpenAIModel("gpt-4") == OpenAIModel.GPT_4

    def test_model_gpt_35_turbo_is_valid(self):
        """Test that 'gpt-3.5-turbo' is accepted."""
        assert OpenAIModel("gpt-3.5-turbo") == OpenAIModel.GPT_35_TURBO

    def test_model_only_has_allowed_values(self):
        """Test that OpenAIModel only contains allowed values.

        GIVEN model parameter for OpenAI
        WHEN not in ['gpt-4o', 'gpt-4', 'gpt-3.5-turbo']
        THEN reject with validation error
        """
        allowed_values = {m.value for m in OpenAIModel}
        assert allowed_values == {"gpt-4o", "gpt-4", "gpt-3.5-turbo"}
        assert len(list(OpenAIModel)) == 3

    def test_invalid_model_gpt5_returns_error(self):
        """Test that invalid model 'gpt-5' is rejected with error message."""
        class TestModel(BaseModel):
            model: OpenAIModel

        with pytest.raises(ValidationError) as exc_info:
            TestModel(model="gpt-5")

        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert errors[0]["loc"] == ("model",)

    def test_invalid_model_claude_sonnet_rejected(self):
        """Test that Claude model names are rejected for OpenAI."""
        class TestModel(BaseModel):
            model: OpenAIModel

        with pytest.raises(ValidationError):
            TestModel(model="claude-3-sonnet")

    def test_invalid_model_empty_string_rejected(self):
        """Test that empty string model is rejected."""
        class TestModel(BaseModel):
            model: OpenAIModel

        with pytest.raises(ValidationError):
            TestModel(model="")

    def test_invalid_model_random_string_rejected(self):
        """Test that arbitrary string model is rejected."""
        class TestModel(BaseModel):
            model: OpenAIModel

        with pytest.raises(ValidationError):
            TestModel(model="not-a-real-model")


class TestErrorMessageSpecifiesAllowedValues:
    """Tests that error messages specify the allowed values for invalid inputs."""

    def test_provider_error_message_contains_allowed_values(self):
        """Test that provider validation error specifies allowed values.

        GIVEN invalid parameter
        WHEN rejected
        THEN error message specifies allowed values
        """
        class TestModel(BaseModel):
            provider: Provider

        with pytest.raises(ValidationError) as exc_info:
            TestModel(provider="invalid")

        # Get the full error context
        error = exc_info.value.errors()[0]
        error_ctx = error.get("ctx", {})

        # Pydantic v2 includes expected values in error context
        # Check if error message or context mentions allowed values
        error_msg = str(error)
        has_allowed_info = (
            "claude" in error_msg.lower() or
            "openai" in error_msg.lower() or
            "expected" in error_msg.lower()
        )
        assert has_allowed_info or error_ctx.get("expected"), \
            f"Error should specify allowed values, got: {error}"

    def test_model_error_message_contains_allowed_values(self):
        """Test that model validation error specifies allowed values."""
        class TestModel(BaseModel):
            model: OpenAIModel

        with pytest.raises(ValidationError) as exc_info:
            TestModel(model="invalid-model")

        # Get the full error context
        error = exc_info.value.errors()[0]
        error_msg = str(error)

        # Check that error provides guidance on allowed values
        has_allowed_info = (
            "gpt" in error_msg.lower() or
            "expected" in error_msg.lower()
        )
        assert has_allowed_info, \
            f"Error should specify allowed values, got: {error}"


class TestEnumValidationEnforcesAllowedValues:
    """Tests that Pydantic enum validation enforces allowed values."""

    def test_pydantic_enforces_provider_enum(self):
        """Test that Pydantic enforces Provider enum validation."""
        class StrictModel(BaseModel):
            provider: Provider

        # Valid values work
        valid = StrictModel(provider="claude")
        assert valid.provider == Provider.CLAUDE

        # Invalid values fail
        with pytest.raises(ValidationError):
            StrictModel(provider="gemini")

    def test_pydantic_enforces_model_enum(self):
        """Test that Pydantic enforces OpenAIModel enum validation."""
        class StrictModel(BaseModel):
            model: OpenAIModel

        # Valid values work
        valid = StrictModel(model="gpt-4o")
        assert valid.model == OpenAIModel.GPT_4O

        # Invalid values fail
        with pytest.raises(ValidationError):
            StrictModel(model="gpt-4-turbo-preview")
