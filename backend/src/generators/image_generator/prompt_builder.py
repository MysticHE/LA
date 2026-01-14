"""Nano Banana optimized prompt builder for LinkedIn image generation.

This module builds prompts optimized for Google's Nano Banana (gemini-2.5-flash-image)
model, following best practices for high-quality professional image generation.

Key optimizations:
- Descriptive paragraphs over keyword lists
- Style-specific visual descriptors
- Tech-specific color palettes
- Composition and camera guidance
- LinkedIn professional context
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum

from src.models.image_schemas import ImageStyle, ContentType, Sentiment


# Style descriptors with rich visual details for Nano Banana
STYLE_DESCRIPTORS = {
    ImageStyle.INFOGRAPHIC: {
        "description": "clean infographic style with organized data visualization",
        "visual_elements": "geometric shapes, icons, clean typography, visual hierarchy",
        "composition": "structured grid layout with clear sections and flow",
        "colors": "vibrant accent colors on clean white or light background",
        "mood": "informative, educational, data-driven",
    },
    ImageStyle.MINIMALIST: {
        "description": "minimalist design with ample negative space and essential elements only",
        "visual_elements": "simple geometric forms, single focal point, refined typography",
        "composition": "centered or asymmetric balance with generous whitespace",
        "colors": "monochromatic or limited palette with subtle accent",
        "mood": "elegant, sophisticated, focused",
    },
    ImageStyle.CONCEPTUAL: {
        "description": "conceptual illustration representing abstract ideas visually",
        "visual_elements": "metaphorical imagery, symbolic objects, creative interpretation",
        "composition": "dynamic arrangement with clear visual metaphor",
        "colors": "harmonious palette supporting the concept",
        "mood": "thought-provoking, creative, insightful",
    },
    ImageStyle.ABSTRACT: {
        "description": "abstract art style with flowing shapes and artistic expression",
        "visual_elements": "organic forms, fluid gradients, artistic patterns",
        "composition": "balanced asymmetry with visual movement",
        "colors": "bold, expressive color combinations with smooth transitions",
        "mood": "innovative, artistic, forward-thinking",
    },
    ImageStyle.PHOTOREALISTIC: {
        "description": "photorealistic rendering with lifelike detail and natural lighting",
        "visual_elements": "realistic textures, natural shadows, depth of field",
        "composition": "rule of thirds with natural focal point",
        "colors": "natural, realistic color grading",
        "mood": "authentic, professional, trustworthy",
    },
    ImageStyle.ILLUSTRATED: {
        "description": "modern illustration style with hand-crafted artistic feel",
        "visual_elements": "stylized characters or objects, artistic line work, texture",
        "composition": "narrative composition with visual storytelling",
        "colors": "cohesive illustrated palette with character",
        "mood": "friendly, approachable, creative",
    },
    ImageStyle.DIAGRAM: {
        "description": "technical diagram style showing systems and connections",
        "visual_elements": "flowcharts, connection lines, nodes, technical icons",
        "composition": "logical flow from top-to-bottom or left-to-right",
        "colors": "clear contrasting colors for different elements",
        "mood": "technical, systematic, educational",
    },
    ImageStyle.GRADIENT: {
        "description": "modern gradient design with smooth color transitions",
        "visual_elements": "flowing gradients, soft shapes, modern typography overlay",
        "composition": "full-bleed gradient with floating elements",
        "colors": "smooth gradient transitions between complementary colors",
        "mood": "modern, dynamic, energetic",
    },
    ImageStyle.FLAT_DESIGN: {
        "description": "flat design style with bold shapes and no shadows",
        "visual_elements": "geometric shapes, solid colors, simple icons, bold outlines",
        "composition": "clean layered arrangement with clear hierarchy",
        "colors": "bright, saturated flat colors with strong contrast",
        "mood": "modern, clean, accessible",
    },
    ImageStyle.ISOMETRIC: {
        "description": "isometric 3D style showing objects from 30-degree angle",
        "visual_elements": "isometric objects, consistent angle, layered depth",
        "composition": "isometric grid with stacked or connected elements",
        "colors": "consistent lighting with subtle shadows for depth",
        "mood": "technical, dimensional, organized",
    },
    ImageStyle.TECH_THEMED: {
        "description": "technology-themed design with digital and futuristic elements",
        "visual_elements": "circuit patterns, code snippets, digital particles, tech icons",
        "composition": "dynamic tech-inspired layout with digital elements",
        "colors": "tech blues, cyans, with electric accents",
        "mood": "innovative, cutting-edge, digital",
    },
    ImageStyle.PROFESSIONAL: {
        "description": "corporate professional design suitable for business context",
        "visual_elements": "clean graphics, business icons, refined imagery",
        "composition": "balanced, formal arrangement with professional polish",
        "colors": "corporate blues, grays, with accent colors",
        "mood": "trustworthy, professional, established",
    },
}

# Technology-specific color palettes
TECH_COLOR_PALETTES = {
    # Cloud providers
    "aws": {"primary": "orange (#FF9900)", "secondary": "dark blue (#232F3E)", "accent": "white"},
    "azure": {"primary": "azure blue (#0078D4)", "secondary": "light blue (#50E6FF)", "accent": "white"},
    "gcp": {"primary": "Google blue (#4285F4)", "secondary": "green (#34A853)", "accent": "yellow (#FBBC05), red (#EA4335)"},
    "google cloud": {"primary": "Google blue (#4285F4)", "secondary": "green (#34A853)", "accent": "yellow (#FBBC05)"},

    # Programming languages
    "python": {"primary": "Python blue (#3776AB)", "secondary": "Python yellow (#FFD43B)", "accent": "white"},
    "javascript": {"primary": "JS yellow (#F7DF1E)", "secondary": "black (#000000)", "accent": "white"},
    "typescript": {"primary": "TypeScript blue (#3178C6)", "secondary": "white", "accent": "dark blue"},
    "java": {"primary": "Java red (#ED8B00)", "secondary": "Java blue (#5382A1)", "accent": "white"},
    "go": {"primary": "Go cyan (#00ADD8)", "secondary": "dark blue (#00758D)", "accent": "white"},
    "golang": {"primary": "Go cyan (#00ADD8)", "secondary": "dark blue (#00758D)", "accent": "white"},
    "rust": {"primary": "Rust orange (#CE422B)", "secondary": "dark brown (#000000)", "accent": "white"},

    # Frameworks
    "react": {"primary": "React cyan (#61DAFB)", "secondary": "dark gray (#282C34)", "accent": "white"},
    "vue": {"primary": "Vue green (#42B883)", "secondary": "dark green (#35495E)", "accent": "white"},
    "angular": {"primary": "Angular red (#DD0031)", "secondary": "dark red (#C3002F)", "accent": "white"},
    "node.js": {"primary": "Node green (#339933)", "secondary": "dark gray (#333333)", "accent": "white"},
    "nodejs": {"primary": "Node green (#339933)", "secondary": "dark gray (#333333)", "accent": "white"},
    "fastapi": {"primary": "FastAPI teal (#009688)", "secondary": "dark teal (#00796B)", "accent": "white"},
    "django": {"primary": "Django green (#092E20)", "secondary": "light green (#44B78B)", "accent": "white"},

    # DevOps
    "docker": {"primary": "Docker blue (#2496ED)", "secondary": "dark blue (#003F8C)", "accent": "white"},
    "kubernetes": {"primary": "K8s blue (#326CE5)", "secondary": "white", "accent": "dark blue"},
    "terraform": {"primary": "Terraform purple (#7B42BC)", "secondary": "dark purple (#5C4EE5)", "accent": "white"},

    # AI/ML
    "machine learning": {"primary": "deep purple (#6B21A8)", "secondary": "gradient blues and purples", "accent": "cyan"},
    "ai": {"primary": "gradient blue to purple", "secondary": "neural network patterns", "accent": "electric cyan"},
    "artificial intelligence": {"primary": "gradient blue to purple", "secondary": "neural patterns", "accent": "electric cyan"},
    "tensorflow": {"primary": "TF orange (#FF6F00)", "secondary": "dark gray", "accent": "white"},
    "pytorch": {"primary": "PyTorch orange (#EE4C2C)", "secondary": "dark gray", "accent": "white"},

    # Databases
    "postgresql": {"primary": "Postgres blue (#336791)", "secondary": "light blue", "accent": "white"},
    "mongodb": {"primary": "Mongo green (#47A248)", "secondary": "dark green", "accent": "white"},
    "redis": {"primary": "Redis red (#DC382D)", "secondary": "dark red", "accent": "white"},
}

# Content type composition templates
CONTENT_TYPE_COMPOSITIONS = {
    ContentType.TUTORIAL: {
        "layout": "step-by-step visual flow with numbered sections",
        "focal_point": "clear learning progression from start to finish",
        "camera": "straight-on educational perspective",
    },
    ContentType.ANNOUNCEMENT: {
        "layout": "bold central message with supporting elements",
        "focal_point": "key announcement text or symbolic representation",
        "camera": "dynamic angle conveying excitement and importance",
    },
    ContentType.TIPS: {
        "layout": "organized tips layout with visual bullet points",
        "focal_point": "key insight or lightbulb moment",
        "camera": "friendly, approachable angle",
    },
    ContentType.STORY: {
        "layout": "narrative composition with journey elements",
        "focal_point": "emotional center representing transformation",
        "camera": "cinematic storytelling perspective",
    },
    ContentType.TECHNICAL: {
        "layout": "technical diagram or architecture visualization",
        "focal_point": "core system or technology component",
        "camera": "technical documentation style, clear and precise",
    },
    ContentType.CAREER: {
        "layout": "professional development visualization",
        "focal_point": "growth and achievement elements",
        "camera": "aspirational upward angle",
    },
}

# Sentiment color modifiers
SENTIMENT_COLORS = {
    Sentiment.POSITIVE: "warm, optimistic colors with uplifting energy",
    Sentiment.NEUTRAL: "balanced, professional color scheme",
    Sentiment.NEGATIVE: "thoughtful, solution-oriented color approach",
    Sentiment.INSPIRATIONAL: "vibrant, motivational colors with dynamic energy",
    Sentiment.INFORMATIVE: "clear, educational colors with good contrast",
}

# LinkedIn dimensions with aspect ratio guidance
DIMENSION_COMPOSITIONS = {
    "1200x627": {
        "aspect": "landscape (1.91:1)",
        "guidance": "horizontal composition optimized for LinkedIn feed, wide cinematic feel",
        "focal_area": "center-weighted with important elements in middle third",
    },
    "1080x1080": {
        "aspect": "square (1:1)",
        "guidance": "balanced square composition, works well for centered subjects",
        "focal_area": "centered focal point with balanced margins",
    },
    "1200x1200": {
        "aspect": "large square (1:1)",
        "guidance": "detailed square composition with more space for complex visuals",
        "focal_area": "centered with room for surrounding context",
    },
}


@dataclass
class PromptComponents:
    """Components assembled into final Nano Banana prompt."""
    context: str
    style_description: str
    visual_elements: str
    composition: str
    color_guidance: str
    content_summary: str
    technical_specs: str


class NanoBananaPromptBuilder:
    """Builds optimized prompts for Nano Banana image generation."""

    def __init__(self):
        self.style_descriptors = STYLE_DESCRIPTORS
        self.tech_palettes = TECH_COLOR_PALETTES
        self.content_compositions = CONTENT_TYPE_COMPOSITIONS
        self.dimension_compositions = DIMENSION_COMPOSITIONS

    def build_prompt(
        self,
        post_content: str,
        style: ImageStyle,
        content_type: ContentType,
        dimensions: str,
        technologies: Optional[list[str]] = None,
        keywords: Optional[list[str]] = None,
        visual_elements: Optional[list[str]] = None,
        sentiment: Optional[Sentiment] = None,
    ) -> str:
        """Build an optimized Nano Banana prompt.

        Args:
            post_content: The LinkedIn post content.
            style: Selected image style.
            content_type: Classified content type.
            dimensions: Image dimensions (e.g., "1200x627").
            technologies: Detected technologies.
            keywords: Extracted keywords.
            visual_elements: Suggested visual elements.
            sentiment: Content sentiment.

        Returns:
            Optimized prompt string for Nano Banana.
        """
        components = self._assemble_components(
            post_content=post_content,
            style=style,
            content_type=content_type,
            dimensions=dimensions,
            technologies=technologies or [],
            keywords=keywords or [],
            visual_elements=visual_elements or [],
            sentiment=sentiment or Sentiment.NEUTRAL,
        )

        return self._format_prompt(components)

    def _assemble_components(
        self,
        post_content: str,
        style: ImageStyle,
        content_type: ContentType,
        dimensions: str,
        technologies: list[str],
        keywords: list[str],
        visual_elements: list[str],
        sentiment: Sentiment,
    ) -> PromptComponents:
        """Assemble all prompt components."""

        # Context: LinkedIn professional purpose
        context = self._build_context(content_type)

        # Style description with rich visual details
        style_description = self._build_style_description(style)

        # Visual elements from analysis
        visual_desc = self._build_visual_elements(visual_elements, keywords)

        # Composition guidance
        composition = self._build_composition(content_type, dimensions)

        # Color guidance based on tech stack
        color_guidance = self._build_color_guidance(technologies, sentiment, style)

        # Content summary (truncated for prompt)
        content_summary = self._build_content_summary(post_content)

        # Technical specs for image
        technical_specs = self._build_technical_specs(dimensions)

        return PromptComponents(
            context=context,
            style_description=style_description,
            visual_elements=visual_desc,
            composition=composition,
            color_guidance=color_guidance,
            content_summary=content_summary,
            technical_specs=technical_specs,
        )

    def _build_context(self, content_type: ContentType) -> str:
        """Build LinkedIn professional context."""
        type_contexts = {
            ContentType.TUTORIAL: "educational content sharing knowledge",
            ContentType.ANNOUNCEMENT: "exciting news or product launch",
            ContentType.TIPS: "practical advice and insights",
            ContentType.STORY: "personal or professional journey",
            ContentType.TECHNICAL: "technical expertise and architecture",
            ContentType.CAREER: "career growth and professional development",
        }
        type_context = type_contexts.get(content_type, "professional content")

        return (
            f"Create a professional image for a LinkedIn post about {type_context}. "
            "The image should be polished, visually striking, and suitable for "
            "a professional networking audience. It should grab attention in a "
            "scrolling feed while maintaining credibility and expertise."
        )

    def _build_style_description(self, style: ImageStyle) -> str:
        """Build rich style description."""
        descriptor = self.style_descriptors.get(style, self.style_descriptors[ImageStyle.MINIMALIST])

        return (
            f"Style: {descriptor['description']}. "
            f"Visual elements should include {descriptor['visual_elements']}. "
            f"The overall mood should be {descriptor['mood']}."
        )

    def _build_visual_elements(
        self,
        visual_elements: list[str],
        keywords: list[str],
    ) -> str:
        """Build visual elements description."""
        parts = []

        if visual_elements:
            elements_str = ", ".join(visual_elements[:4])
            parts.append(f"Incorporate visual elements representing: {elements_str}")

        if keywords:
            keywords_str = ", ".join(keywords[:5])
            parts.append(f"Key themes to visualize: {keywords_str}")

        if not parts:
            return "Focus on clean, professional visual representation of the concept."

        return ". ".join(parts) + "."

    def _build_composition(self, content_type: ContentType, dimensions: str) -> str:
        """Build composition and camera guidance."""
        content_comp = self.content_compositions.get(
            content_type,
            self.content_compositions[ContentType.TECHNICAL]
        )
        dim_comp = self.dimension_compositions.get(
            dimensions,
            self.dimension_compositions["1200x627"]
        )

        return (
            f"Composition: {content_comp['layout']}. "
            f"Focal point: {content_comp['focal_point']}. "
            f"Camera perspective: {content_comp['camera']}. "
            f"Aspect ratio: {dim_comp['aspect']} - {dim_comp['guidance']}. "
            f"Important: {dim_comp['focal_area']}."
        )

    def _build_color_guidance(
        self,
        technologies: list[str],
        sentiment: Sentiment,
        style: ImageStyle,
    ) -> str:
        """Build color palette guidance."""
        parts = []

        # Tech-specific colors
        tech_colors = []
        for tech in technologies[:3]:
            tech_lower = tech.lower()
            if tech_lower in self.tech_palettes:
                palette = self.tech_palettes[tech_lower]
                tech_colors.append(f"{tech}: {palette['primary']} as primary")

        if tech_colors:
            parts.append(f"Technology-inspired colors: {'; '.join(tech_colors)}")

        # Style default colors
        style_desc = self.style_descriptors.get(style, {})
        if "colors" in style_desc:
            parts.append(f"Style palette: {style_desc['colors']}")

        # Sentiment modifier
        sentiment_mod = SENTIMENT_COLORS.get(sentiment, SENTIMENT_COLORS[Sentiment.NEUTRAL])
        parts.append(f"Mood colors: {sentiment_mod}")

        if not parts:
            return "Use a professional, harmonious color palette."

        return " ".join(parts)

    def _build_content_summary(self, post_content: str) -> str:
        """Build content summary for prompt."""
        max_len = 300
        content = post_content.strip()

        if len(content) > max_len:
            content = content[:max_len] + "..."

        return f'The post discusses: "{content}"'

    def _build_technical_specs(self, dimensions: str) -> str:
        """Build technical specifications."""
        dim_info = self.dimension_compositions.get(
            dimensions,
            self.dimension_compositions["1200x627"]
        )

        return (
            f"Generate image at {dimensions} pixels ({dim_info['aspect']}). "
            "Ensure clean edges, no watermarks, no text overlays, no signatures. "
            "The image should be high quality and production-ready for social media."
        )

    def _format_prompt(self, components: PromptComponents) -> str:
        """Format final prompt from components."""
        sections = [
            components.context,
            "",
            components.style_description,
            "",
            components.visual_elements,
            "",
            components.composition,
            "",
            components.color_guidance,
            "",
            components.content_summary,
            "",
            components.technical_specs,
        ]

        return "\n".join(sections)


# Singleton instance
_prompt_builder: Optional[NanoBananaPromptBuilder] = None


def get_prompt_builder() -> NanoBananaPromptBuilder:
    """Get the singleton prompt builder instance."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = NanoBananaPromptBuilder()
    return _prompt_builder
