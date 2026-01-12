"""Tests for AI prompt generator."""

import pytest
from src.generators.ai_prompt_generator import AIPromptGenerator
from src.models.schemas import AnalysisResult, PostStyle, TechStackItem, Feature


@pytest.fixture
def sample_analysis():
    """Create a sample AnalysisResult for testing."""
    return AnalysisResult(
        repo_name="test-project",
        description="A test project for unit testing",
        stars=500,
        forks=100,
        language="Python",
        tech_stack=[
            TechStackItem(name="FastAPI", category="framework"),
            TechStackItem(name="PostgreSQL", category="database"),
            TechStackItem(name="Redis", category="cache"),
        ],
        features=[
            Feature(name="REST API", description="Full REST API implementation"),
            Feature(name="Auth", description="JWT authentication"),
            Feature(name="Caching", description="Redis caching layer"),
        ],
        readme_summary="A comprehensive project for building scalable web applications.",
        file_structure=["src/", "tests/", "docs/", "README.md"],
    )


@pytest.fixture
def minimal_analysis():
    """Create a minimal AnalysisResult for testing edge cases."""
    return AnalysisResult(
        repo_name="minimal-project",
        description=None,
        stars=0,
        forks=0,
        language=None,
        tech_stack=[],
        features=[],
        readme_summary=None,
        file_structure=[],
    )


class TestAIPromptGenerator:
    """Tests for AIPromptGenerator class."""

    def test_generate_prompt_returns_tuple(self, sample_analysis):
        """Test that generate_prompt returns a tuple of two strings."""
        result = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)  # system prompt
        assert isinstance(result[1], str)  # user prompt

    def test_generate_prompt_system_contains_guidelines(self, sample_analysis):
        """Test that system prompt contains writing guidelines."""
        system_prompt, _ = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert "LinkedIn" in system_prompt
        assert "3000 characters" in system_prompt
        assert "hashtags" in system_prompt

    def test_generate_prompt_problem_solution_style(self, sample_analysis):
        """Test that problem-solution style includes style-specific instructions."""
        system_prompt, _ = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert "Problem-Solution" in system_prompt
        assert "hook" in system_prompt.lower()
        assert "solution" in system_prompt.lower()

    def test_generate_prompt_tips_learnings_style(self, sample_analysis):
        """Test that tips-learnings style includes style-specific instructions."""
        system_prompt, _ = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.TIPS_LEARNINGS
        )

        assert "Tips & Learnings" in system_prompt
        assert "learned" in system_prompt.lower()
        assert "insights" in system_prompt.lower()

    def test_generate_prompt_technical_showcase_style(self, sample_analysis):
        """Test that technical-showcase style includes style-specific instructions."""
        system_prompt, _ = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.TECHNICAL_SHOWCASE
        )

        assert "Technical Showcase" in system_prompt
        assert "architecture" in system_prompt.lower()

    def test_user_prompt_contains_repo_info(self, sample_analysis):
        """Test that user prompt contains repository information."""
        _, user_prompt = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert "test-project" in user_prompt
        assert "A test project for unit testing" in user_prompt
        assert "Python" in user_prompt
        assert "500 stars" in user_prompt
        assert "100 forks" in user_prompt

    def test_user_prompt_contains_tech_stack(self, sample_analysis):
        """Test that user prompt contains tech stack information."""
        _, user_prompt = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert "FastAPI" in user_prompt
        assert "PostgreSQL" in user_prompt
        assert "Redis" in user_prompt

    def test_user_prompt_contains_features(self, sample_analysis):
        """Test that user prompt contains features information."""
        _, user_prompt = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert "REST API" in user_prompt
        assert "JWT authentication" in user_prompt
        assert "Caching" in user_prompt

    def test_user_prompt_contains_readme_summary(self, sample_analysis):
        """Test that user prompt contains README summary."""
        _, user_prompt = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert "comprehensive project for building scalable web applications" in user_prompt

    def test_user_prompt_handles_missing_description(self, minimal_analysis):
        """Test that user prompt handles missing description gracefully."""
        _, user_prompt = AIPromptGenerator.generate_prompt(
            analysis=minimal_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert "Not provided" in user_prompt

    def test_user_prompt_handles_missing_language(self, minimal_analysis):
        """Test that user prompt handles missing language gracefully."""
        _, user_prompt = AIPromptGenerator.generate_prompt(
            analysis=minimal_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert "Not specified" in user_prompt

    def test_user_prompt_handles_empty_tech_stack(self, minimal_analysis):
        """Test that user prompt handles empty tech stack gracefully."""
        _, user_prompt = AIPromptGenerator.generate_prompt(
            analysis=minimal_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        # Should have fallback for empty tech stack
        assert "Tech Stack" in user_prompt  # Section exists
        assert "Not specified" in user_prompt

    def test_user_prompt_handles_empty_features(self, minimal_analysis):
        """Test that user prompt handles empty features gracefully."""
        _, user_prompt = AIPromptGenerator.generate_prompt(
            analysis=minimal_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        # Should have fallback for empty features
        assert "Features" in user_prompt  # Section exists

    def test_user_prompt_handles_missing_readme_summary(self, minimal_analysis):
        """Test that user prompt handles missing README summary gracefully."""
        _, user_prompt = AIPromptGenerator.generate_prompt(
            analysis=minimal_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert "Not available" in user_prompt

    def test_system_prompt_instructs_post_only(self, sample_analysis):
        """Test that system prompt instructs to return only the post."""
        system_prompt, _ = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )

        assert "ONLY the LinkedIn post" in system_prompt

    def test_each_style_produces_different_instructions(self, sample_analysis):
        """Test that each style produces different system prompts."""
        problem_system, _ = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.PROBLEM_SOLUTION
        )
        tips_system, _ = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.TIPS_LEARNINGS
        )
        tech_system, _ = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.TECHNICAL_SHOWCASE
        )

        # All should be different due to style-specific instructions
        assert problem_system != tips_system
        assert tips_system != tech_system
        assert problem_system != tech_system

    def test_user_prompt_includes_style_name(self, sample_analysis):
        """Test that user prompt includes the style name."""
        _, user_prompt = AIPromptGenerator.generate_prompt(
            analysis=sample_analysis,
            style=PostStyle.TIPS_LEARNINGS
        )

        assert "Tips & Learnings" in user_prompt


class TestStyleInstructions:
    """Tests for style-specific instructions."""

    def test_problem_solution_structure(self):
        """Test problem-solution style has required structure elements."""
        instructions = AIPromptGenerator.STYLE_INSTRUCTIONS[PostStyle.PROBLEM_SOLUTION]

        assert "hook" in instructions.lower()
        assert "problem" in instructions.lower()
        assert "solution" in instructions.lower()
        assert "call-to-action" in instructions.lower()

    def test_tips_learnings_structure(self):
        """Test tips-learnings style has required structure elements."""
        instructions = AIPromptGenerator.STYLE_INSTRUCTIONS[PostStyle.TIPS_LEARNINGS]

        assert "learned" in instructions.lower()
        assert "insights" in instructions.lower() or "lessons" in instructions.lower()
        assert "numbered" in instructions.lower() or "bullet" in instructions.lower()

    def test_technical_showcase_structure(self):
        """Test technical-showcase style has required structure elements."""
        instructions = AIPromptGenerator.STYLE_INSTRUCTIONS[PostStyle.TECHNICAL_SHOWCASE]

        assert "architecture" in instructions.lower()
        assert "technical" in instructions.lower()
