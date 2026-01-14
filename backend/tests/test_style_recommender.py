"""Tests for StyleRecommender service."""

import pytest
from src.generators.image_generator.style_recommender import StyleRecommender
from src.models.image_schemas import (
    ContentType,
    ImageStyle,
    StyleRecommendation,
    ContentAnalysis,
    Sentiment,
)


class TestStyleRecommender:
    """Tests for StyleRecommender class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.recommender = StyleRecommender()

    def test_tutorial_returns_expected_styles_in_order(self):
        """GIVEN ContentType.TUTORIAL WHEN recommend() is called
        THEN return infographic, minimalist, conceptual in order."""
        result = self.recommender.recommend(ContentType.TUTORIAL)

        assert isinstance(result, StyleRecommendation)
        assert result.styles[0] == "infographic"
        assert result.styles[1] == "minimalist"
        assert result.styles[2] == "conceptual"

    def test_any_content_type_returns_at_least_3_styles(self):
        """GIVEN any content type WHEN recommended THEN return at least 3 style options."""
        for content_type in ContentType:
            result = self.recommender.recommend(content_type)

            assert isinstance(result, StyleRecommendation)
            assert len(result.styles) >= 3

    def test_tech_stack_influences_recommendations(self):
        """GIVEN content type and tech stack WHEN recommended
        THEN styles consider technology themes."""
        result_with_tech = self.recommender.recommend(
            ContentType.TUTORIAL,
            technologies=["kubernetes", "docker"]
        )

        assert result_with_tech.tech_influenced is True
        assert "isometric" in result_with_tech.styles or "diagram" in result_with_tech.styles

    def test_tutorial_styles(self):
        """Test TUTORIAL content type returns appropriate styles."""
        result = self.recommender.recommend(ContentType.TUTORIAL)

        assert "infographic" in result.styles
        assert "minimalist" in result.styles
        assert result.content_type == ContentType.TUTORIAL

    def test_announcement_styles(self):
        """Test ANNOUNCEMENT content type returns appropriate styles."""
        result = self.recommender.recommend(ContentType.ANNOUNCEMENT)

        assert "gradient" in result.styles
        assert "abstract" in result.styles
        assert result.content_type == ContentType.ANNOUNCEMENT

    def test_tips_styles(self):
        """Test TIPS content type returns appropriate styles."""
        result = self.recommender.recommend(ContentType.TIPS)

        assert "flat_design" in result.styles
        assert "minimalist" in result.styles
        assert result.content_type == ContentType.TIPS

    def test_story_styles(self):
        """Test STORY content type returns appropriate styles."""
        result = self.recommender.recommend(ContentType.STORY)

        assert "photorealistic" in result.styles
        assert "illustrated" in result.styles
        assert result.content_type == ContentType.STORY

    def test_technical_styles(self):
        """Test TECHNICAL content type returns appropriate styles."""
        result = self.recommender.recommend(ContentType.TECHNICAL)

        assert "diagram" in result.styles
        assert "isometric" in result.styles
        assert result.content_type == ContentType.TECHNICAL

    def test_career_styles(self):
        """Test CAREER content type returns appropriate styles."""
        result = self.recommender.recommend(ContentType.CAREER)

        assert "professional" in result.styles
        assert "minimalist" in result.styles
        assert result.content_type == ContentType.CAREER

    def test_cloud_tech_influences_styles(self):
        """Test cloud technologies influence style recommendations."""
        result = self.recommender.recommend(
            ContentType.TUTORIAL,
            technologies=["AWS", "Docker"]
        )

        assert result.tech_influenced is True
        top_styles = result.styles[:3]
        assert "isometric" in top_styles or "diagram" in top_styles

    def test_ml_tech_influences_styles(self):
        """Test ML technologies influence style recommendations."""
        result = self.recommender.recommend(
            ContentType.TECHNICAL,
            technologies=["TensorFlow", "Machine Learning"]
        )

        assert result.tech_influenced is True
        assert "abstract" in result.styles or "conceptual" in result.styles

    def test_web_tech_influences_styles(self):
        """Test web technologies influence style recommendations."""
        result = self.recommender.recommend(
            ContentType.TUTORIAL,
            technologies=["React", "TypeScript"]
        )

        assert result.tech_influenced is True
        assert "flat_design" in result.styles or "tech_themed" in result.styles

    def test_unknown_tech_no_influence(self):
        """Test unknown technologies do not affect recommendations."""
        result = self.recommender.recommend(
            ContentType.TUTORIAL,
            technologies=["UnknownTech123", "FakeTech"]
        )

        assert result.tech_influenced is False
        assert result.styles[0] == "infographic"

    def test_tech_case_insensitive(self):
        """Test technology matching is case-insensitive."""
        result_lower = self.recommender.recommend(
            ContentType.TECHNICAL,
            technologies=["aws"]
        )
        result_upper = self.recommender.recommend(
            ContentType.TECHNICAL,
            technologies=["AWS"]
        )

        assert result_lower.tech_influenced == result_upper.tech_influenced
        assert result_lower.styles == result_upper.styles

    def test_accept_content_analysis(self):
        """Test recommend() accepts ContentAnalysis object."""
        analysis = ContentAnalysis(
            themes=["web development"],
            technologies=["Python", "FastAPI"],
            sentiment=Sentiment.INFORMATIVE,
            keywords=["API", "backend"],
            suggested_visual_elements=["code", "server"],
        )

        result = self.recommender.recommend(
            ContentType.TUTORIAL,
            analysis=analysis
        )

        assert isinstance(result, StyleRecommendation)
        assert result.tech_influenced is True

    def test_analysis_technologies_extracted(self):
        """Test technologies are extracted from ContentAnalysis."""
        analysis = ContentAnalysis(
            technologies=["Kubernetes", "Docker"],
        )

        result = self.recommender.recommend(
            ContentType.TECHNICAL,
            analysis=analysis
        )

        assert result.tech_influenced is True

    def test_explicit_tech_overrides_analysis(self):
        """Test explicit technologies parameter takes precedence over analysis."""
        analysis = ContentAnalysis(
            technologies=["Kubernetes"],
        )

        result = self.recommender.recommend(
            ContentType.TUTORIAL,
            technologies=["UnknownTech"],
            analysis=analysis
        )

        assert result.tech_influenced is False

    def test_recommendation_serialization(self):
        """Test StyleRecommendation can be serialized."""
        result = self.recommender.recommend(ContentType.TUTORIAL)

        data = result.model_dump()

        assert "styles" in data
        assert "content_type" in data
        assert "tech_influenced" in data
        assert data["content_type"] == "tutorial"

    def test_recommendation_minimum_styles(self):
        """Test StyleRecommendation always has at least 3 styles."""
        for content_type in ContentType:
            result = self.recommender.recommend(content_type)
            assert len(result.styles) >= 3

    def test_get_available_styles(self):
        """Test get_available_styles returns all ImageStyle values."""
        styles = self.recommender.get_available_styles()

        assert len(styles) == len(ImageStyle)
        assert "infographic" in styles
        assert "minimalist" in styles
        assert "conceptual" in styles

    def test_get_styles_for_content_type(self):
        """Test get_styles_for_content_type returns correct styles."""
        styles = self.recommender.get_styles_for_content_type(ContentType.TUTORIAL)

        assert styles[0] == "infographic"
        assert styles[1] == "minimalist"
        assert styles[2] == "conceptual"

    def test_empty_technologies_list(self):
        """Test empty technologies list does not affect results."""
        result = self.recommender.recommend(
            ContentType.TUTORIAL,
            technologies=[]
        )

        assert result.tech_influenced is False
        assert result.styles[0] == "infographic"

    def test_none_technologies(self):
        """Test None technologies works correctly."""
        result = self.recommender.recommend(
            ContentType.TUTORIAL,
            technologies=None
        )

        assert result.tech_influenced is False
        assert len(result.styles) >= 3

    def test_multiple_techs_same_category(self):
        """Test multiple technologies from same category."""
        result = self.recommender.recommend(
            ContentType.TECHNICAL,
            technologies=["AWS", "Azure", "GCP"]
        )

        assert result.tech_influenced is True
        assert len(result.styles) == len(set(result.styles))

    def test_styles_no_duplicates(self):
        """Test recommended styles have no duplicates."""
        result = self.recommender.recommend(
            ContentType.TECHNICAL,
            technologies=["PostgreSQL"]
        )

        assert len(result.styles) == len(set(result.styles))

    def test_all_content_types_have_mapping(self):
        """Test all ContentType values have style mappings."""
        for content_type in ContentType:
            styles = self.recommender.get_styles_for_content_type(content_type)
            assert len(styles) >= 3

    def test_consistent_results(self):
        """Test repeated calls give consistent results."""
        results = [
            self.recommender.recommend(
                ContentType.TUTORIAL,
                technologies=["Python"]
            )
            for _ in range(5)
        ]

        first = results[0]
        for result in results[1:]:
            assert result.styles == first.styles
            assert result.tech_influenced == first.tech_influenced

    def test_mixed_known_unknown_tech(self):
        """Test mix of known and unknown technologies."""
        result = self.recommender.recommend(
            ContentType.TUTORIAL,
            technologies=["Python", "UnknownTech", "React"]
        )

        assert result.tech_influenced is True
