"""Tests for ContentAnalyzer service."""

import pytest
from src.analyzers.content_analyzer import ContentAnalyzer
from src.models.image_schemas import ContentAnalysis, Sentiment


class TestContentAnalyzer:
    """Tests for ContentAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ContentAnalyzer()

    # === Acceptance Criteria Tests ===

    def test_analyze_returns_content_analysis_object(self):
        """GIVEN a LinkedIn post text WHEN ContentAnalyzer.analyze() is called
        THEN return ContentAnalysis object with themes, technologies, and sentiment."""
        content = "I just built an amazing web application using Python and React!"

        result = self.analyzer.analyze(content)

        assert isinstance(result, ContentAnalysis)
        assert hasattr(result, 'themes')
        assert hasattr(result, 'technologies')
        assert hasattr(result, 'sentiment')
        assert isinstance(result.themes, list)
        assert isinstance(result.technologies, list)
        assert isinstance(result.sentiment, Sentiment)

    def test_analyze_detects_python_and_fastapi(self):
        """GIVEN post mentioning Python and FastAPI WHEN analyzed
        THEN technologies array includes 'Python' and 'FastAPI'."""
        content = """
        Excited to share my latest project!
        I built a REST API using Python and FastAPI.
        The performance is incredible!
        """

        result = self.analyzer.analyze(content)

        assert 'Python' in result.technologies
        assert 'FastAPI' in result.technologies

    def test_analyze_empty_content_raises_value_error(self):
        """GIVEN empty post WHEN analyzed THEN raise ValueError with descriptive message."""
        with pytest.raises(ValueError) as exc_info:
            self.analyzer.analyze("")

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_analyze_none_content_raises_value_error(self):
        """GIVEN None post WHEN analyzed THEN raise ValueError with descriptive message."""
        with pytest.raises(ValueError) as exc_info:
            self.analyzer.analyze(None)

        assert "cannot be empty" in str(exc_info.value).lower()

    def test_analyze_whitespace_only_raises_value_error(self):
        """GIVEN whitespace-only post WHEN analyzed THEN raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.analyzer.analyze("   \n\t  ")

        assert "cannot be empty" in str(exc_info.value).lower()

    # === Technology Detection Tests ===

    def test_detect_javascript_technologies(self):
        """Test detection of JavaScript ecosystem technologies."""
        content = "Building with JavaScript, React, and Next.js is so productive!"

        result = self.analyzer.analyze(content)

        assert 'JavaScript' in result.technologies
        assert 'React' in result.technologies
        assert 'Next.js' in result.technologies

    def test_detect_backend_technologies(self):
        """Test detection of backend technologies."""
        content = "Deployed my Django app with PostgreSQL and Docker on AWS."

        result = self.analyzer.analyze(content)

        assert 'Django' in result.technologies
        assert 'PostgreSQL' in result.technologies
        assert 'Docker' in result.technologies
        assert 'AWS' in result.technologies

    def test_detect_ai_ml_technologies(self):
        """Test detection of AI/ML technologies."""
        content = "Trained a model using TensorFlow and PyTorch, then deployed with OpenAI's API."

        result = self.analyzer.analyze(content)

        assert 'TensorFlow' in result.technologies
        assert 'PyTorch' in result.technologies
        assert 'OpenAI' in result.technologies

    def test_detect_cloud_technologies(self):
        """Test detection of cloud technologies."""
        content = "Migrated our infrastructure to Kubernetes on Google Cloud with Terraform."

        result = self.analyzer.analyze(content)

        assert 'Kubernetes' in result.technologies
        assert 'Google Cloud' in result.technologies
        assert 'Terraform' in result.technologies

    def test_detect_k8s_abbreviation(self):
        """Test detection of k8s as Kubernetes."""
        content = "Just got my k8s cluster running perfectly!"

        result = self.analyzer.analyze(content)

        assert 'Kubernetes' in result.technologies

    def test_no_duplicate_technologies(self):
        """Test that technologies are not duplicated."""
        content = "Python Python Python! I love Python and python programming."

        result = self.analyzer.analyze(content)

        python_count = result.technologies.count('Python')
        assert python_count == 1

    # === Theme Detection Tests ===

    def test_detect_web_development_theme(self):
        """Test detection of web development theme."""
        content = "Working on full-stack web development is my passion. Frontend and backend!"

        result = self.analyzer.analyze(content)

        assert 'web development' in result.themes

    def test_detect_machine_learning_theme(self):
        """Test detection of machine learning theme."""
        content = "Deep dive into machine learning and AI fundamentals."

        result = self.analyzer.analyze(content)

        assert 'machine learning' in result.themes

    def test_detect_devops_theme(self):
        """Test detection of devops theme."""
        content = "Improving our deployment pipeline and infrastructure automation."

        result = self.analyzer.analyze(content)

        assert 'devops' in result.themes

    def test_detect_career_theme(self):
        """Test detection of career theme."""
        content = "Just passed my job interview at a tech company! Career milestone!"

        result = self.analyzer.analyze(content)

        assert 'career' in result.themes

    def test_detect_multiple_themes(self):
        """Test detection of multiple themes."""
        content = """
        My machine learning journey: from learning tutorials to
        building APIs and testing them properly.
        """

        result = self.analyzer.analyze(content)

        assert len(result.themes) >= 2

    # === Sentiment Analysis Tests ===

    def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        content = "Excited and thrilled to share this amazing achievement! Great success!"

        result = self.analyzer.analyze(content)

        assert result.sentiment == Sentiment.POSITIVE

    def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        content = "Frustrated with this terrible bug. The problem is so annoying and difficult."

        result = self.analyzer.analyze(content)

        assert result.sentiment == Sentiment.NEGATIVE

    def test_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        content = "Here is some code I wrote today."

        result = self.analyzer.analyze(content)

        assert result.sentiment == Sentiment.NEUTRAL

    def test_inspirational_sentiment(self):
        """Test inspirational sentiment detection."""
        content = "My journey of growth and learning. Lessons that transformed my vision for the future."

        result = self.analyzer.analyze(content)

        assert result.sentiment == Sentiment.INSPIRATIONAL

    def test_informative_sentiment(self):
        """Test informative sentiment detection."""
        content = "Here's a step-by-step guide and tutorial to explain how to use this. Overview and comparison included."

        result = self.analyzer.analyze(content)

        assert result.sentiment == Sentiment.INFORMATIVE

    # === Keywords Tests ===

    def test_keywords_include_technologies(self):
        """Test that keywords include detected technologies."""
        content = "Building with Python and React!"

        result = self.analyzer.analyze(content)

        assert 'Python' in result.keywords
        assert 'React' in result.keywords

    def test_keywords_include_themes(self):
        """Test that keywords include detected themes."""
        content = "Machine learning and data science project."

        result = self.analyzer.analyze(content)

        # Keywords should include either the technology or theme
        assert len(result.keywords) > 0

    def test_keywords_no_duplicates(self):
        """Test that keywords have no duplicates."""
        content = "Python machine learning project with Python."

        result = self.analyzer.analyze(content)

        # Check no duplicates
        assert len(result.keywords) == len(set(k.lower() for k in result.keywords))

    # === Visual Elements Tests ===

    def test_visual_elements_for_ml_theme(self):
        """Test visual elements suggestion for machine learning theme."""
        content = "Working on deep learning and machine learning models."

        result = self.analyzer.analyze(content)

        assert len(result.suggested_visual_elements) > 0

    def test_visual_elements_for_web_theme(self):
        """Test visual elements suggestion for web development theme."""
        content = "Full-stack web development project."

        result = self.analyzer.analyze(content)

        assert len(result.suggested_visual_elements) > 0

    def test_visual_elements_default(self):
        """Test default visual elements when no themes match."""
        content = "Just a random thought about programming."

        result = self.analyzer.analyze(content)

        # Should have default elements
        assert len(result.suggested_visual_elements) > 0

    def test_visual_elements_limited_to_five(self):
        """Test that visual elements are limited to 5."""
        content = """
        Machine learning, web development, devops, data science,
        cloud computing, security, API development, and more!
        """

        result = self.analyzer.analyze(content)

        assert len(result.suggested_visual_elements) <= 5

    # === Edge Cases ===

    def test_case_insensitive_detection(self):
        """Test that detection is case-insensitive."""
        content = "PYTHON, Python, and python are all the same!"

        result = self.analyzer.analyze(content)

        assert 'Python' in result.technologies
        assert result.technologies.count('Python') == 1

    def test_mixed_content(self):
        """Test analysis of mixed content."""
        content = """
        Excited to share my journey! Built an amazing API using FastAPI
        and Python. Deployed on AWS with Docker. This machine learning
        project uses TensorFlow for deep learning predictions. Here's my
        step-by-step guide to help you learn.
        """

        result = self.analyzer.analyze(content)

        # Should detect multiple technologies
        assert 'FastAPI' in result.technologies
        assert 'Python' in result.technologies
        assert 'AWS' in result.technologies
        assert 'Docker' in result.technologies
        assert 'TensorFlow' in result.technologies

        # Should detect themes
        assert len(result.themes) > 0

        # Should have keywords
        assert len(result.keywords) > 0

        # Should have visual elements
        assert len(result.suggested_visual_elements) > 0

    def test_special_characters_in_content(self):
        """Test handling of special characters."""
        content = "Using C# and .NET for enterprise development! #dotnet @microsoft"

        result = self.analyzer.analyze(content)

        assert 'C#' in result.technologies
        assert '.NET' in result.technologies

    def test_technology_with_versions(self):
        """Test detection of technologies with version numbers."""
        content = "Upgraded to React 18 and TypeScript 5.0!"

        result = self.analyzer.analyze(content)

        assert 'React' in result.technologies
        assert 'TypeScript' in result.technologies

    def test_go_language_vs_go_verb(self):
        """Test that 'go' as verb is not detected as Go language."""
        content = "Let's go to the meeting now."

        result = self.analyzer.analyze(content)

        # Should not detect Go language from "go to"
        assert 'Go' not in result.technologies

    def test_golang_detected(self):
        """Test that 'golang' is detected as Go."""
        content = "Started learning Golang this week!"

        result = self.analyzer.analyze(content)

        assert 'Go' in result.technologies

    def test_empty_results_for_non_tech_content(self):
        """Test minimal results for non-technical content."""
        content = "Had a nice lunch today."

        result = self.analyzer.analyze(content)

        assert isinstance(result, ContentAnalysis)
        assert len(result.technologies) == 0
        # Still should have default visual elements
        assert len(result.suggested_visual_elements) > 0
