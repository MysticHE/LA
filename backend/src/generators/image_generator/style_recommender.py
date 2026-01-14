"""Style recommender for LinkedIn post images."""

from typing import Optional
from src.models.image_schemas import (
    ContentType,
    ImageStyle,
    StyleRecommendation,
    ContentAnalysis,
)


class StyleRecommender:
    """Recommend image styles based on content type and tech stack."""

    # Default style recommendations by content type
    # Ordered by most appropriate first
    CONTENT_TYPE_STYLES = {
        ContentType.TUTORIAL: [
            ImageStyle.INFOGRAPHIC,
            ImageStyle.MINIMALIST,
            ImageStyle.CONCEPTUAL,
            ImageStyle.DIAGRAM,
            ImageStyle.ILLUSTRATED,
        ],
        ContentType.ANNOUNCEMENT: [
            ImageStyle.GRADIENT,
            ImageStyle.ABSTRACT,
            ImageStyle.MINIMALIST,
            ImageStyle.PROFESSIONAL,
            ImageStyle.FLAT_DESIGN,
        ],
        ContentType.TIPS: [
            ImageStyle.FLAT_DESIGN,
            ImageStyle.MINIMALIST,
            ImageStyle.INFOGRAPHIC,
            ImageStyle.ILLUSTRATED,
            ImageStyle.CONCEPTUAL,
        ],
        ContentType.STORY: [
            ImageStyle.PHOTOREALISTIC,
            ImageStyle.ILLUSTRATED,
            ImageStyle.ABSTRACT,
            ImageStyle.GRADIENT,
            ImageStyle.CONCEPTUAL,
        ],
        ContentType.TECHNICAL: [
            ImageStyle.DIAGRAM,
            ImageStyle.ISOMETRIC,
            ImageStyle.TECH_THEMED,
            ImageStyle.MINIMALIST,
            ImageStyle.CONCEPTUAL,
        ],
        ContentType.CAREER: [
            ImageStyle.PROFESSIONAL,
            ImageStyle.MINIMALIST,
            ImageStyle.GRADIENT,
            ImageStyle.FLAT_DESIGN,
            ImageStyle.PHOTOREALISTIC,
        ],
    }

    # Technology-specific style influences
    # Technologies mapped to their best visual styles
    TECH_STYLE_MAPPING = {
        # Cloud/DevOps technologies - isometric, diagram
        "aws": [ImageStyle.ISOMETRIC, ImageStyle.DIAGRAM],
        "azure": [ImageStyle.ISOMETRIC, ImageStyle.DIAGRAM],
        "gcp": [ImageStyle.ISOMETRIC, ImageStyle.DIAGRAM],
        "google cloud": [ImageStyle.ISOMETRIC, ImageStyle.DIAGRAM],
        "docker": [ImageStyle.ISOMETRIC, ImageStyle.DIAGRAM],
        "kubernetes": [ImageStyle.ISOMETRIC, ImageStyle.DIAGRAM],
        "terraform": [ImageStyle.ISOMETRIC, ImageStyle.DIAGRAM],

        # Data/ML technologies - abstract, conceptual
        "python": [ImageStyle.TECH_THEMED, ImageStyle.MINIMALIST],
        "machine learning": [ImageStyle.ABSTRACT, ImageStyle.CONCEPTUAL],
        "ai": [ImageStyle.ABSTRACT, ImageStyle.CONCEPTUAL],
        "artificial intelligence": [ImageStyle.ABSTRACT, ImageStyle.CONCEPTUAL],
        "data science": [ImageStyle.ABSTRACT, ImageStyle.INFOGRAPHIC],
        "tensorflow": [ImageStyle.ABSTRACT, ImageStyle.TECH_THEMED],
        "pytorch": [ImageStyle.ABSTRACT, ImageStyle.TECH_THEMED],

        # Web technologies - flat design, modern
        "react": [ImageStyle.FLAT_DESIGN, ImageStyle.TECH_THEMED],
        "vue": [ImageStyle.FLAT_DESIGN, ImageStyle.TECH_THEMED],
        "angular": [ImageStyle.FLAT_DESIGN, ImageStyle.TECH_THEMED],
        "javascript": [ImageStyle.FLAT_DESIGN, ImageStyle.MINIMALIST],
        "typescript": [ImageStyle.FLAT_DESIGN, ImageStyle.MINIMALIST],
        "node.js": [ImageStyle.TECH_THEMED, ImageStyle.MINIMALIST],
        "nodejs": [ImageStyle.TECH_THEMED, ImageStyle.MINIMALIST],

        # Backend technologies
        "java": [ImageStyle.PROFESSIONAL, ImageStyle.DIAGRAM],
        "spring": [ImageStyle.PROFESSIONAL, ImageStyle.DIAGRAM],
        "fastapi": [ImageStyle.TECH_THEMED, ImageStyle.MINIMALIST],
        "django": [ImageStyle.TECH_THEMED, ImageStyle.MINIMALIST],
        "go": [ImageStyle.MINIMALIST, ImageStyle.TECH_THEMED],
        "golang": [ImageStyle.MINIMALIST, ImageStyle.TECH_THEMED],
        "rust": [ImageStyle.MINIMALIST, ImageStyle.TECH_THEMED],

        # Database technologies
        "postgresql": [ImageStyle.DIAGRAM, ImageStyle.ISOMETRIC],
        "mongodb": [ImageStyle.DIAGRAM, ImageStyle.ISOMETRIC],
        "redis": [ImageStyle.DIAGRAM, ImageStyle.ISOMETRIC],
        "sql": [ImageStyle.DIAGRAM, ImageStyle.INFOGRAPHIC],
    }

    def recommend(
        self,
        content_type: ContentType,
        technologies: Optional[list[str]] = None,
        analysis: Optional[ContentAnalysis] = None,
    ) -> StyleRecommendation:
        """
        Recommend image styles based on content type and optional tech stack.

        Args:
            content_type: The classified content type
            technologies: Optional list of technologies detected in content
            analysis: Optional full content analysis (will extract technologies if provided)

        Returns:
            StyleRecommendation with ordered list of style suggestions
        """
        # Get base styles for content type
        base_styles = list(self.CONTENT_TYPE_STYLES.get(
            content_type,
            self.CONTENT_TYPE_STYLES[ContentType.TECHNICAL]  # Default fallback
        ))

        # Extract technologies from analysis if provided
        if analysis and not technologies:
            technologies = analysis.technologies

        # Check if we have technology-influenced recommendations
        tech_influenced = False
        tech_styles: list[ImageStyle] = []

        if technologies:
            for tech in technologies:
                tech_lower = tech.lower()
                if tech_lower in self.TECH_STYLE_MAPPING:
                    tech_styles.extend(self.TECH_STYLE_MAPPING[tech_lower])
                    tech_influenced = True

        # Merge tech styles with base styles (tech styles get priority boost)
        if tech_styles:
            # Remove duplicates while preserving order
            seen = set()
            merged_styles = []

            # First, add tech-influenced styles (top priority)
            for style in tech_styles:
                if style not in seen:
                    seen.add(style)
                    merged_styles.append(style)

            # Then add remaining base styles
            for style in base_styles:
                if style not in seen:
                    seen.add(style)
                    merged_styles.append(style)

            final_styles = merged_styles[:5]  # Return top 5
        else:
            final_styles = base_styles[:5]

        # Ensure we have at least 3 styles
        if len(final_styles) < 3:
            # Add default styles to fill
            for default in [ImageStyle.MINIMALIST, ImageStyle.CONCEPTUAL, ImageStyle.PROFESSIONAL]:
                if default not in final_styles:
                    final_styles.append(default)
                if len(final_styles) >= 3:
                    break

        return StyleRecommendation(
            styles=[style.value for style in final_styles],
            content_type=content_type,
            tech_influenced=tech_influenced,
        )

    def get_available_styles(self) -> list[str]:
        """Get list of all available image styles."""
        return [style.value for style in ImageStyle]

    def get_styles_for_content_type(self, content_type: ContentType) -> list[str]:
        """Get default styles for a content type (without tech influence)."""
        styles = self.CONTENT_TYPE_STYLES.get(
            content_type,
            self.CONTENT_TYPE_STYLES[ContentType.TECHNICAL]
        )
        return [style.value for style in styles]
