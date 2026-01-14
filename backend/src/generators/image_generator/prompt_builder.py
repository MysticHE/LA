"""Nano Banana optimized prompt builder for LinkedIn image generation.

This module builds prompts optimized for Google's Nano Banana (gemini-2.5-flash-image)
model, following official best practices from Google and community research.

Key optimizations (based on official Nano Banana Pro tips):
- Structured formula: Subject + Action + Environment + Style + Lighting + Details
- ALL CAPS emphasis for critical constraints (improves adherence)
- Professional quality anchors (Pulitzer Prize, Vanity Fair references)
- Explicit negation clauses with penalty warnings
- Hex color precision for accurate rendering
- Compositional rules (rule of thirds, negative space)
- Camera/lighting specs (f-stop, golden hour, etc.)
- LinkedIn professional context with scroll-stopping hooks

Reference sources:
- https://blog.google/products/gemini/prompting-tips-nano-banana-pro/
- https://minimaxir.com/2025/11/nano-banana-prompts/
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum

from src.models.image_schemas import ImageStyle, ContentType, Sentiment


# Style descriptors with rich visual details for Nano Banana
# Enhanced with camera/lighting specs per official Google tips
STYLE_DESCRIPTORS = {
    ImageStyle.INFOGRAPHIC: {
        "description": "clean infographic style with organized data visualization",
        "visual_elements": "geometric shapes, icons, clean typography, visual hierarchy",
        "composition": "structured grid layout with clear sections and flow, rule of thirds",
        "colors": "vibrant accent colors on clean white (#FFFFFF) or light gray (#F5F5F5) background",
        "mood": "informative, educational, data-driven",
        "camera": "straight-on flat perspective, even studio lighting",
        "quality_anchor": "award-winning editorial infographic",
    },
    ImageStyle.MINIMALIST: {
        "description": "minimalist design with ample negative space and essential elements only",
        "visual_elements": "simple geometric forms, single focal point, refined typography",
        "composition": "centered or asymmetric balance with generous whitespace, negative space utilization",
        "colors": "monochromatic palette with subtle accent, pure white (#FFFFFF) dominant",
        "mood": "elegant, sophisticated, focused",
        "camera": "centered composition with shallow depth of field f/2.8",
        "quality_anchor": "museum-quality minimalist art print",
    },
    ImageStyle.CONCEPTUAL: {
        "description": "conceptual illustration representing abstract ideas visually",
        "visual_elements": "metaphorical imagery, symbolic objects, creative interpretation",
        "composition": "dynamic arrangement with clear visual metaphor, rule of thirds",
        "colors": "harmonious palette supporting the concept with intentional color symbolism",
        "mood": "thought-provoking, creative, insightful",
        "camera": "artistic angle with dramatic lighting contrast",
        "quality_anchor": "New Yorker magazine cover illustration",
    },
    ImageStyle.ABSTRACT: {
        "description": "abstract art style with flowing shapes and artistic expression",
        "visual_elements": "organic forms, fluid gradients, artistic patterns",
        "composition": "balanced asymmetry with visual movement and flow",
        "colors": "bold, expressive color combinations with smooth gradient transitions",
        "mood": "innovative, artistic, forward-thinking",
        "camera": "macro lens perspective with soft focus edges",
        "quality_anchor": "contemporary art gallery exhibition piece",
    },
    ImageStyle.PHOTOREALISTIC: {
        "description": "photorealistic rendering with lifelike detail and natural lighting",
        "visual_elements": "realistic textures, natural shadows, cinematic depth of field",
        "composition": "rule of thirds with natural focal point, leading lines",
        "colors": "natural color grading, realistic skin tones and material properties",
        "mood": "authentic, professional, trustworthy",
        "camera": "shot on Sony A7IV, 85mm f/1.4 lens, golden hour backlighting",
        "quality_anchor": "Pulitzer Prize winning photograph, Vanity Fair profile",
    },
    ImageStyle.ILLUSTRATED: {
        "description": "modern illustration style with hand-crafted artistic feel",
        "visual_elements": "stylized characters or objects, artistic line work, texture overlays",
        "composition": "narrative composition with visual storytelling, clear focal hierarchy",
        "colors": "cohesive illustrated palette with character and warmth",
        "mood": "friendly, approachable, creative",
        "camera": "flat 2D illustration perspective with subtle depth layers",
        "quality_anchor": "Apple marketing illustration style",
    },
    ImageStyle.DIAGRAM: {
        "description": "technical diagram style showing systems and connections",
        "visual_elements": "flowcharts, connection lines, nodes, technical icons, labeled components",
        "composition": "logical flow from top-to-bottom or left-to-right, clear visual hierarchy",
        "colors": "clear contrasting colors (#4285F4 blue, #34A853 green, #EA4335 red) for different elements",
        "mood": "technical, systematic, educational",
        "camera": "orthographic top-down or isometric technical view",
        "quality_anchor": "Google Cloud architecture diagram",
    },
    ImageStyle.GRADIENT: {
        "description": "modern gradient design with smooth color transitions",
        "visual_elements": "flowing gradients, soft shapes, modern typography overlay, glass morphism",
        "composition": "full-bleed gradient with floating elements and depth",
        "colors": "smooth gradient transitions, mesh gradients, complementary color harmony",
        "mood": "modern, dynamic, energetic",
        "camera": "wide angle with depth blur, soft diffused lighting",
        "quality_anchor": "Apple iOS wallpaper design quality",
    },
    ImageStyle.FLAT_DESIGN: {
        "description": "flat design style with bold shapes and no shadows",
        "visual_elements": "geometric shapes, solid colors, simple icons, bold outlines",
        "composition": "clean layered arrangement with clear visual hierarchy",
        "colors": "bright saturated flat colors (#FF6B6B, #4ECDC4, #FFE66D) with strong contrast",
        "mood": "modern, clean, accessible",
        "camera": "flat 2D perspective, no depth or shadows",
        "quality_anchor": "Dribbble trending flat illustration",
    },
    ImageStyle.ISOMETRIC: {
        "description": "isometric 3D style showing objects from precise 30-degree angle",
        "visual_elements": "isometric objects, consistent 30° angle, layered depth, precise geometry",
        "composition": "isometric grid with stacked or connected elements, clear z-axis ordering",
        "colors": "consistent lighting with subtle shadows (#000000 at 10% opacity) for depth",
        "mood": "technical, dimensional, organized",
        "camera": "isometric projection at exact 30-degree angle, soft ambient occlusion",
        "quality_anchor": "Monument Valley game art style",
    },
    ImageStyle.TECH_THEMED: {
        "description": "technology-themed design with digital and futuristic elements",
        "visual_elements": "circuit patterns, code snippets, digital particles, tech icons, HUD elements",
        "composition": "dynamic tech-inspired layout with digital elements, data visualization",
        "colors": "tech blues (#00D4FF), cyans (#00FFFF), electric purple (#8B5CF6) with neon accents",
        "mood": "innovative, cutting-edge, digital",
        "camera": "wide angle with depth of field, neon lighting, lens flares",
        "quality_anchor": "Blade Runner 2049 concept art aesthetic",
    },
    ImageStyle.PROFESSIONAL: {
        "description": "corporate professional design suitable for business context",
        "visual_elements": "clean graphics, business icons, refined imagery, subtle patterns",
        "composition": "balanced formal arrangement with professional polish, golden ratio",
        "colors": "corporate navy (#1E3A5F), slate gray (#64748B), accent blue (#3B82F6)",
        "mood": "trustworthy, professional, established",
        "camera": "straight-on corporate photography style, soft studio lighting",
        "quality_anchor": "McKinsey consulting presentation visual",
    },
}

# Technology-specific color palettes with precise hex codes
# Per Nano Banana best practices: hex codes improve color accuracy
TECH_COLOR_PALETTES = {
    # Cloud providers
    "aws": {"primary": "#FF9900", "secondary": "#232F3E", "accent": "#FFFFFF"},
    "azure": {"primary": "#0078D4", "secondary": "#50E6FF", "accent": "#FFFFFF"},
    "gcp": {"primary": "#4285F4", "secondary": "#34A853", "accent": "#FBBC05"},
    "google cloud": {"primary": "#4285F4", "secondary": "#34A853", "accent": "#FBBC05"},

    # Programming languages
    "python": {"primary": "#3776AB", "secondary": "#FFD43B", "accent": "#FFFFFF"},
    "javascript": {"primary": "#F7DF1E", "secondary": "#323330", "accent": "#FFFFFF"},
    "typescript": {"primary": "#3178C6", "secondary": "#FFFFFF", "accent": "#235A97"},
    "java": {"primary": "#ED8B00", "secondary": "#5382A1", "accent": "#FFFFFF"},
    "go": {"primary": "#00ADD8", "secondary": "#00758D", "accent": "#FFFFFF"},
    "golang": {"primary": "#00ADD8", "secondary": "#00758D", "accent": "#FFFFFF"},
    "rust": {"primary": "#CE422B", "secondary": "#000000", "accent": "#FFFFFF"},

    # Frameworks
    "react": {"primary": "#61DAFB", "secondary": "#282C34", "accent": "#FFFFFF"},
    "vue": {"primary": "#42B883", "secondary": "#35495E", "accent": "#FFFFFF"},
    "angular": {"primary": "#DD0031", "secondary": "#C3002F", "accent": "#FFFFFF"},
    "node.js": {"primary": "#339933", "secondary": "#333333", "accent": "#FFFFFF"},
    "nodejs": {"primary": "#339933", "secondary": "#333333", "accent": "#FFFFFF"},
    "next.js": {"primary": "#000000", "secondary": "#FFFFFF", "accent": "#0070F3"},
    "nextjs": {"primary": "#000000", "secondary": "#FFFFFF", "accent": "#0070F3"},
    "fastapi": {"primary": "#009688", "secondary": "#00796B", "accent": "#FFFFFF"},
    "django": {"primary": "#092E20", "secondary": "#44B78B", "accent": "#FFFFFF"},
    "flask": {"primary": "#000000", "secondary": "#FFFFFF", "accent": "#3CAFCE"},
    "svelte": {"primary": "#FF3E00", "secondary": "#FFFFFF", "accent": "#676778"},

    # DevOps
    "docker": {"primary": "#2496ED", "secondary": "#003F8C", "accent": "#FFFFFF"},
    "kubernetes": {"primary": "#326CE5", "secondary": "#FFFFFF", "accent": "#1D4ED8"},
    "terraform": {"primary": "#7B42BC", "secondary": "#5C4EE5", "accent": "#FFFFFF"},
    "github actions": {"primary": "#2088FF", "secondary": "#24292E", "accent": "#FFFFFF"},
    "jenkins": {"primary": "#D24939", "secondary": "#FFFFFF", "accent": "#335061"},

    # AI/ML - Enhanced with specific hex codes
    "machine learning": {"primary": "#6B21A8", "secondary": "#8B5CF6", "accent": "#00D4FF"},
    "ai": {"primary": "#8B5CF6", "secondary": "#3B82F6", "accent": "#00D4FF"},
    "artificial intelligence": {"primary": "#8B5CF6", "secondary": "#3B82F6", "accent": "#00D4FF"},
    "tensorflow": {"primary": "#FF6F00", "secondary": "#425066", "accent": "#FFFFFF"},
    "pytorch": {"primary": "#EE4C2C", "secondary": "#DE3412", "accent": "#FFFFFF"},
    "langchain": {"primary": "#1C3C3C", "secondary": "#2DD4BF", "accent": "#FFFFFF"},
    "openai": {"primary": "#412991", "secondary": "#10A37F", "accent": "#FFFFFF"},
    "hugging face": {"primary": "#FFD21E", "secondary": "#000000", "accent": "#FF9D00"},

    # Databases
    "postgresql": {"primary": "#336791", "secondary": "#6699CC", "accent": "#FFFFFF"},
    "mongodb": {"primary": "#47A248", "secondary": "#13AA52", "accent": "#FFFFFF"},
    "redis": {"primary": "#DC382D", "secondary": "#A41E11", "accent": "#FFFFFF"},
    "mysql": {"primary": "#4479A1", "secondary": "#00758F", "accent": "#F29111"},
    "elasticsearch": {"primary": "#FEC514", "secondary": "#343741", "accent": "#00BFB3"},
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
    """Components assembled into final Nano Banana prompt.

    Based on official Nano Banana formula:
    Subject + Action + Environment + Style + Lighting + Details
    """
    context: str
    style_description: str
    visual_elements: str
    composition: str
    camera_lighting: str  # NEW: Camera/lighting specs per official tips
    color_guidance: str
    quality_anchor: str  # NEW: Professional quality reference
    content_summary: str
    technical_specs: str
    negation_clauses: str  # NEW: ALL CAPS constraints per Max Woolf research


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
        """Assemble all prompt components using official Nano Banana formula."""

        # Context: LinkedIn professional purpose
        context = self._build_context(content_type)

        # Style description with rich visual details
        style_description = self._build_style_description(style)

        # Visual elements from analysis
        visual_desc = self._build_visual_elements(visual_elements, keywords)

        # Composition guidance
        composition = self._build_composition(content_type, dimensions)

        # Camera and lighting specs (NEW - per official Google tips)
        camera_lighting = self._build_camera_lighting(style)

        # Color guidance based on tech stack
        color_guidance = self._build_color_guidance(technologies, sentiment, style)

        # Quality anchor reference (NEW - improves composition quality)
        quality_anchor = self._build_quality_anchor(style)

        # Content summary (truncated for prompt)
        content_summary = self._build_content_summary(post_content)

        # Technical specs for image
        technical_specs = self._build_technical_specs(dimensions)

        # Negation clauses with ALL CAPS (NEW - per Max Woolf research)
        negation_clauses = self._build_negation_clauses()

        return PromptComponents(
            context=context,
            style_description=style_description,
            visual_elements=visual_desc,
            composition=composition,
            camera_lighting=camera_lighting,
            color_guidance=color_guidance,
            quality_anchor=quality_anchor,
            content_summary=content_summary,
            technical_specs=technical_specs,
            negation_clauses=negation_clauses,
        )

    def _build_context(self, content_type: ContentType) -> str:
        """Build LinkedIn professional context with scroll-stopping hooks.

        Per official Nano Banana tips: Be descriptive and specific about
        the intended outcome, environment, and audience.
        """
        type_contexts = {
            ContentType.TUTORIAL: "educational content teaching a valuable skill",
            ContentType.ANNOUNCEMENT: "exciting professional news or product launch",
            ContentType.TIPS: "actionable advice and expert insights",
            ContentType.STORY: "compelling personal or professional journey",
            ContentType.TECHNICAL: "technical expertise demonstrating deep knowledge",
            ContentType.CAREER: "career growth and professional achievement",
        }
        type_context = type_contexts.get(content_type, "professional content")

        return (
            f"Create a scroll-stopping, visually striking image for a LinkedIn post about {type_context}. "
            "Target audience: tech professionals, software engineers, and business leaders. "
            "The image must immediately grab attention in a fast-scrolling LinkedIn feed, "
            "convey credibility and expertise, and make viewers pause to engage. "
            "Professional quality suitable for a top-tier technology publication."
        )

    def _build_style_description(self, style: ImageStyle) -> str:
        """Build rich style description with visual elements and mood.

        Per official Nano Banana formula: Style is a core component
        that should specify aesthetic clearly.
        """
        descriptor = self.style_descriptors.get(style, self.style_descriptors[ImageStyle.MINIMALIST])

        return (
            f"Art Style: {descriptor['description']}. "
            f"MUST include these visual elements: {descriptor['visual_elements']}. "
            f"Composition approach: {descriptor['composition']}. "
            f"The overall mood and feeling should be: {descriptor['mood']}."
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
        """Build color palette guidance with precise hex codes.

        Per Nano Banana best practices: hex color codes (#FF9900) improve
        color accuracy significantly over color names.
        """
        parts = []

        # Tech-specific colors with hex codes
        tech_colors = []
        for tech in technologies[:3]:
            tech_lower = tech.lower()
            if tech_lower in self.tech_palettes:
                palette = self.tech_palettes[tech_lower]
                tech_colors.append(
                    f"{tech}: primary {palette['primary']}, "
                    f"secondary {palette['secondary']}, "
                    f"accent {palette['accent']}"
                )

        if tech_colors:
            parts.append(f"EXACT COLOR PALETTE: {'; '.join(tech_colors)}")

        # Style default colors
        style_desc = self.style_descriptors.get(style, {})
        if "colors" in style_desc:
            parts.append(f"Style palette: {style_desc['colors']}")

        # Sentiment modifier
        sentiment_mod = SENTIMENT_COLORS.get(sentiment, SENTIMENT_COLORS[Sentiment.NEUTRAL])
        parts.append(f"Mood colors: {sentiment_mod}")

        if not parts:
            return "Use a professional, harmonious color palette with good contrast."

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
            "High resolution, detailed, sharp, production-ready for social media."
        )

    def _build_camera_lighting(self, style: ImageStyle) -> str:
        """Build camera and lighting specifications.

        Based on official Google tips: include camera/lighting details like
        'Low-angle shot with f/1.8 shallow depth of field' or 'Golden hour backlighting'.
        """
        descriptor = self.style_descriptors.get(style, self.style_descriptors[ImageStyle.MINIMALIST])
        camera = descriptor.get("camera", "professional photography lighting")

        return f"Camera and Lighting: {camera}."

    def _build_quality_anchor(self, style: ImageStyle) -> str:
        """Build quality anchor reference.

        Per Max Woolf's research: phrases like 'Pulitzer Prize winning cover photo'
        and 'Vanity Fair profile' noticeably improve compositional quality because
        the model semantically differentiates between professional and amateur aesthetics.
        """
        descriptor = self.style_descriptors.get(style, self.style_descriptors[ImageStyle.MINIMALIST])
        anchor = descriptor.get("quality_anchor", "professional editorial quality")

        return f"Quality benchmark: {anchor}."

    def _build_negation_clauses(self) -> str:
        """Build explicit negation clauses with ALL CAPS emphasis.

        Per Max Woolf's research: ALL CAPS emphasis and 'penalty' phrasing
        significantly improves prompt adherence. Statements like
        'YOU WILL BE PENALIZED FOR USING THEM' improve constraint following.
        """
        return (
            "CRITICAL CONSTRAINTS - YOU MUST FOLLOW THESE EXACTLY:\n"
            "- NEVER include any text, words, letters, or typography in the image\n"
            "- NEVER include watermarks, signatures, logos, or branding\n"
            "- NEVER include human faces unless explicitly requested\n"
            "- NEVER include stock photo artifacts or cheesy corporate imagery\n"
            "- YOU WILL BE PENALIZED for including any of the above elements"
        )

    def _format_prompt(self, components: PromptComponents) -> str:
        """Format final prompt from components.

        Structure follows official Nano Banana formula:
        Subject + Action + Environment + Style + Lighting + Details

        Ends with ALL CAPS negation clauses per Max Woolf's research
        for maximum constraint adherence.
        """
        sections = [
            # Opening context and quality anchor
            components.context,
            components.quality_anchor,
            "",
            # Style and visual details
            components.style_description,
            components.visual_elements,
            "",
            # Composition and camera (per official formula)
            components.composition,
            components.camera_lighting,
            "",
            # Color guidance
            components.color_guidance,
            "",
            # Content summary
            components.content_summary,
            "",
            # Technical specs
            components.technical_specs,
            "",
            # ALL CAPS negation clauses at end (per Max Woolf research)
            components.negation_clauses,
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
