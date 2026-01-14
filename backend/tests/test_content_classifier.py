"""Tests for ContentClassifier service."""

import pytest
from src.analyzers.content_classifier import ContentClassifier
from src.analyzers.content_analyzer import ContentAnalyzer
from src.models.image_schemas import ContentAnalysis, ContentType, ClassificationResult, Sentiment


class TestContentClassifier:
    """Tests for ContentClassifier class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = ContentClassifier()
        self.analyzer = ContentAnalyzer()

    # === Acceptance Criteria Tests ===

    def test_classify_returns_classification_result(self):
        """GIVEN ContentAnalysis WHEN classify() is called
        THEN return ClassificationResult with ContentType enum value."""
        text = "Here is a step-by-step tutorial on Python."
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert isinstance(result, ClassificationResult)
        assert isinstance(result.content_type, ContentType)
        assert isinstance(result.confidence, float)

    def test_tutorial_post_classified_with_high_confidence(self):
        """GIVEN tutorial-style post WHEN classified
        THEN return ContentType.TUTORIAL with confidence >= 0.7."""
        # Classic tutorial content
        tutorial_text = """
        How to build a REST API with Python and FastAPI - A Step-by-Step Guide

        Let me show you how to create a production-ready API. This tutorial
        will walk you through everything from getting started to deployment.

        Step 1: Install dependencies
        Step 2: Create your first endpoint
        Step 3: Add authentication
        """
        analysis = self.analyzer.analyze(tutorial_text)
        result = self.classifier.classify(analysis, tutorial_text)

        assert result.content_type == ContentType.TUTORIAL
        assert result.confidence >= 0.7

    def test_ambiguous_content_lower_confidence(self):
        """GIVEN ambiguous content WHEN classified
        THEN return most likely type with lower confidence score."""
        # Content that could be multiple types
        ambiguous_text = "Working on some Python code today."
        analysis = self.analyzer.analyze(ambiguous_text)

        result = self.classifier.classify(analysis, ambiguous_text)

        # Should still return a valid result but with lower confidence
        assert isinstance(result.content_type, ContentType)
        assert result.confidence < 0.7

    def test_all_six_content_types_supported(self):
        """Classification supports all 6 types: TUTORIAL, ANNOUNCEMENT, TIPS, STORY, TECHNICAL, CAREER."""
        # Verify all enum values exist
        assert ContentType.TUTORIAL.value == "tutorial"
        assert ContentType.ANNOUNCEMENT.value == "announcement"
        assert ContentType.TIPS.value == "tips"
        assert ContentType.STORY.value == "story"
        assert ContentType.TECHNICAL.value == "technical"
        assert ContentType.CAREER.value == "career"

        # Verify all six types exist
        all_types = set(ContentType)
        expected_types = {
            ContentType.TUTORIAL,
            ContentType.ANNOUNCEMENT,
            ContentType.TIPS,
            ContentType.STORY,
            ContentType.TECHNICAL,
            ContentType.CAREER,
        }
        assert all_types == expected_types

    # === Tutorial Classification Tests ===

    def test_classify_how_to_post_as_tutorial(self):
        """Test that 'how to' posts are classified as TUTORIAL."""
        text = "How to set up Docker containers for your development environment"
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.TUTORIAL

    def test_classify_step_by_step_as_tutorial(self):
        """Test that step-by-step content is classified as TUTORIAL."""
        text = "Step-by-step walkthrough: Building your first React component"
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.TUTORIAL

    def test_classify_beginner_guide_as_tutorial(self):
        """Test that beginner guides are classified as TUTORIAL."""
        text = "A complete introduction to machine learning for beginners. Getting started with Python."
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.TUTORIAL

    # === Announcement Classification Tests ===

    def test_classify_launch_as_announcement(self):
        """Test that launch announcements are classified as ANNOUNCEMENT."""
        text = "Excited to announce we're launching our new product! Now available for everyone."
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.ANNOUNCEMENT

    def test_classify_new_release_as_announcement(self):
        """Test that new releases are classified as ANNOUNCEMENT."""
        text = "Big news! We've released version 2.0 of our framework. Check it out!"
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.ANNOUNCEMENT

    def test_classify_just_shipped_as_announcement(self):
        """Test that shipping updates are classified as ANNOUNCEMENT."""
        text = "Just shipped a major update! Introducing our new dashboard feature."
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.ANNOUNCEMENT

    # === Tips Classification Tests ===

    def test_classify_tips_post_as_tips(self):
        """Test that tips posts are classified as TIPS."""
        text = "5 tips for writing cleaner Python code. Pro tip: use type hints!"
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.TIPS

    def test_classify_best_practices_as_tips(self):
        """Test that best practices posts are classified as TIPS."""
        text = "Best practices for API design: Do's and don'ts you should know"
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.TIPS

    def test_classify_mistakes_to_avoid_as_tips(self):
        """Test that 'mistakes to avoid' posts are classified as TIPS."""
        text = "Common mistakes to avoid when learning JavaScript. Here are 7 things I wish I knew."
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.TIPS

    # === Story Classification Tests ===

    def test_classify_journey_post_as_story(self):
        """Test that journey posts are classified as STORY."""
        text = "My journey from junior developer to tech lead. When I started 5 years ago, I had no idea where I'd end up."
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.STORY

    def test_classify_personal_experience_as_story(self):
        """Test that personal experience posts are classified as STORY."""
        text = "Looking back on my personal experience with burnout. I struggled for months before I overcame it."
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.STORY

    def test_classify_failure_story_as_story(self):
        """Test that failure stories are classified as STORY."""
        text = "I failed my first startup. Here's what I learned. It transformed how I approach business."
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.STORY

    # === Technical Classification Tests ===

    def test_classify_architecture_post_as_technical(self):
        """Test that architecture posts are classified as TECHNICAL."""
        text = "Deep dive into microservices architecture and system design patterns"
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.TECHNICAL

    def test_classify_performance_post_as_technical(self):
        """Test that performance posts are classified as TECHNICAL."""
        text = "Performance optimization and benchmarking results for our new algorithm"
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.TECHNICAL

    def test_classify_under_the_hood_as_technical(self):
        """Test that 'under the hood' posts are classified as TECHNICAL."""
        text = "Under the hood: How our implementation handles scalability and refactoring"
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.TECHNICAL

    # === Career Classification Tests ===

    def test_classify_hiring_post_as_career(self):
        """Test that hiring posts are classified as CAREER."""
        text = "We're hiring! Looking for senior developers. Great salary and benefits."
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.CAREER

    def test_classify_job_search_as_career(self):
        """Test that job search posts are classified as CAREER."""
        text = "Open to new opportunities! Just updated my resume and looking for my next career move."
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.CAREER

    def test_classify_interview_tips_as_career(self):
        """Test that interview-related posts are classified as CAREER."""
        text = "Interview preparation: How I landed my dream job after months of job search"
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.content_type == ContentType.CAREER

    # === Confidence Score Tests ===

    def test_high_confidence_for_clear_content(self):
        """Test high confidence score for clearly categorized content."""
        # Very clear tutorial content
        text = """
        Tutorial: How to build APIs step-by-step

        Let me show you how to get started. This guide walks you through
        the complete process. Step 1, Step 2, Step 3 - explained in detail.
        """
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        assert result.confidence >= 0.7

    def test_lower_confidence_for_mixed_content(self):
        """Test lower confidence for content with mixed signals."""
        # Mixed signals: could be tips or tutorial
        text = "Quick tips on coding"
        analysis = self.analyzer.analyze(text)

        result = self.classifier.classify(analysis, text)

        # Should have valid confidence but potentially lower
        assert 0.0 <= result.confidence <= 1.0

    def test_confidence_between_0_and_1(self):
        """Test that confidence is always between 0 and 1."""
        texts = [
            "How to learn Python",
            "We're launching a new product",
            "5 tips for developers",
            "My journey as a developer",
            "Architecture deep dive",
            "We're hiring engineers",
            "Random text about nothing specific",
        ]

        for text in texts:
            analysis = self.analyzer.analyze(text)
            result = self.classifier.classify(analysis, text)

            assert 0.0 <= result.confidence <= 1.0

    # === ClassificationResult Model Tests ===

    def test_classification_result_serialization(self):
        """Test that ClassificationResult can be serialized."""
        result = ClassificationResult(
            content_type=ContentType.TUTORIAL,
            confidence=0.85
        )

        data = result.model_dump()

        assert data['content_type'] == 'tutorial'
        assert data['confidence'] == 0.85

    def test_classification_result_validation(self):
        """Test that ClassificationResult validates confidence bounds."""
        # Valid confidence
        result = ClassificationResult(
            content_type=ContentType.TUTORIAL,
            confidence=0.5
        )
        assert result.confidence == 0.5

        # Invalid confidence should raise error
        with pytest.raises(ValueError):
            ClassificationResult(
                content_type=ContentType.TUTORIAL,
                confidence=1.5  # Out of bounds
            )

        with pytest.raises(ValueError):
            ClassificationResult(
                content_type=ContentType.TUTORIAL,
                confidence=-0.1  # Negative
            )

    # === classify_from_text Tests ===

    def test_classify_from_text_tutorial(self):
        """Test classify_from_text method with tutorial content."""
        text = "Step-by-step tutorial on how to build a REST API"

        result = self.classifier.classify_from_text(text)

        assert result.content_type == ContentType.TUTORIAL
        assert result.confidence >= 0.5

    def test_classify_from_text_announcement(self):
        """Test classify_from_text method with announcement content."""
        text = "Excited to announce our new product launch! Now available."

        result = self.classifier.classify_from_text(text)

        assert result.content_type == ContentType.ANNOUNCEMENT

    def test_classify_from_text_empty_raises_error(self):
        """Test that classify_from_text raises error for empty text."""
        with pytest.raises(ValueError) as exc_info:
            self.classifier.classify_from_text("")

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_classify_from_text_none_raises_error(self):
        """Test that classify_from_text raises error for None."""
        with pytest.raises(ValueError) as exc_info:
            self.classifier.classify_from_text(None)

        assert "cannot be empty" in str(exc_info.value).lower()

    # === Edge Cases ===

    def test_classify_empty_analysis(self):
        """Test classification with minimal analysis data."""
        analysis = ContentAnalysis(
            themes=[],
            technologies=[],
            sentiment=Sentiment.NEUTRAL,
            keywords=[],
            suggested_visual_elements=[]
        )

        result = self.classifier.classify(analysis)

        # Should return a valid result with low confidence
        assert isinstance(result.content_type, ContentType)
        assert result.confidence < 0.5

    def test_classify_case_insensitive(self):
        """Test that classification is case-insensitive."""
        text_lower = "how to build an api"
        text_upper = "HOW TO BUILD AN API"

        result_lower = self.classifier.classify_from_text(text_lower)
        result_upper = self.classifier.classify_from_text(text_upper)

        assert result_lower.content_type == result_upper.content_type

    def test_classify_with_special_characters(self):
        """Test classification with special characters."""
        text = "Pro-tip: Here's how to use C# and .NET for #career growth!"

        result = self.classifier.classify_from_text(text)

        # Should handle special characters gracefully
        assert isinstance(result.content_type, ContentType)

    def test_classify_long_content(self):
        """Test classification with long content."""
        long_text = """
        Today I want to share my complete journey in software development.

        When I started 10 years ago, I had no idea what I was doing.
        I remember struggling with basic concepts and feeling overwhelmed.

        Looking back, here are the key lessons from my experience:

        1. Never stop learning
        2. Embrace failure as part of growth
        3. Build a strong network

        My story shows that persistence pays off. I went from knowing
        nothing to becoming a senior architect, overcoming many obstacles.

        I hope this inspires you on your own journey.
        """ * 3  # Repeat to make it long

        result = self.classifier.classify_from_text(long_text)

        assert isinstance(result.content_type, ContentType)
        assert 0.0 <= result.confidence <= 1.0

    def test_multiple_classifications_consistent(self):
        """Test that repeated classifications give consistent results."""
        text = "How to build a REST API with FastAPI - Step by step tutorial"
        analysis = self.analyzer.analyze(text)

        results = [self.classifier.classify(analysis, text) for _ in range(5)]

        # All results should be the same
        first_result = results[0]
        for result in results[1:]:
            assert result.content_type == first_result.content_type
            assert result.confidence == first_result.confidence
