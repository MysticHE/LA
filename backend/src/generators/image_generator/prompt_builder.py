"""Gemini-optimized prompt builder for LinkedIn image generation.

This module builds prompts optimized for Google's Gemini 3 Pro Image
(gemini-3-pro-image-preview) model using a clean, structured format
focused on Scene Composition + Text Rendering + Aesthetic.

Key structure:
- Role: Expert LinkedIn Visual Designer
- Task: High-conversion image for specific dimensions
- Scene Composition: Layout type, background, foreground
- Text Rendering: Headline and subtitle from post content
- Aesthetic & Color: Style, palette with hex codes, mood
- Context: Post summary for visual metaphor alignment
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum
import re

from src.models.image_schemas import ImageStyle, ContentType, Sentiment


# Layout types for scene composition based on content type
# Focus on clean, artistic visuals - NO diagrams, charts, or technical elements
LAYOUT_TYPES = {
    ContentType.TUTORIAL: {
        "layout": "clean centered",
        "background": "Smooth gradient from deep blue to purple",
        "foreground": "Simple abstract shapes with soft glow effects",
    },
    ContentType.ANNOUNCEMENT: {
        "layout": "bold centered",
        "background": "Vibrant gradient with subtle light rays",
        "foreground": "Clean geometric accent shapes",
    },
    ContentType.TIPS: {
        "layout": "balanced asymmetric",
        "background": "Warm gradient with soft bokeh light effects",
        "foreground": "Minimal decorative elements",
    },
    ContentType.STORY: {
        "layout": "cinematic wide",
        "background": "Atmospheric gradient with depth and dimension",
        "foreground": "Subtle light streaks or lens flare accents",
    },
    ContentType.TECHNICAL: {
        "layout": "modern minimal",
        "background": "Deep dark gradient transitioning to rich accent color",
        "foreground": "Simple glowing orbs or soft light elements",
    },
    ContentType.CAREER: {
        "layout": "uplifting diagonal",
        "background": "Inspiring gradient from dark to bright",
        "foreground": "Soft ascending light beams",
    },
}

# Style descriptors with aesthetic details
# Focus on artistic visuals - avoid technical diagrams, charts, flowcharts, nodes
STYLE_AESTHETICS = {
    ImageStyle.INFOGRAPHIC: {
        "style": "Clean modern design with bold typography as the hero element",
        "mood": "Clear, impactful, professional",
    },
    ImageStyle.MINIMALIST: {
        "style": "Ultra-minimal design with generous whitespace and one focal element",
        "mood": "Elegant, sophisticated, premium",
    },
    ImageStyle.CONCEPTUAL: {
        "style": "Artistic composition with dreamlike atmosphere and soft focus",
        "mood": "Thought-provoking, creative, inspiring",
    },
    ImageStyle.ABSTRACT: {
        "style": "Fluid abstract art with organic flowing shapes and rich color blending",
        "mood": "Innovative, artistic, expressive",
    },
    ImageStyle.PHOTOREALISTIC: {
        "style": "Cinematic photography style with dramatic lighting and shallow depth of field",
        "mood": "Authentic, premium, editorial",
    },
    ImageStyle.ILLUSTRATED: {
        "style": "Modern flat illustration with smooth curves and vibrant colors",
        "mood": "Friendly, approachable, engaging",
    },
    ImageStyle.DIAGRAM: {
        "style": "Clean structured layout with clear visual hierarchy and bold text",
        "mood": "Organized, clear, educational",
    },
    ImageStyle.GRADIENT: {
        "style": "Rich gradient meshes with smooth color transitions and glass effects",
        "mood": "Modern, dynamic, vibrant",
    },
    ImageStyle.FLAT_DESIGN: {
        "style": "Bold flat design with solid color blocks and simple shapes",
        "mood": "Modern, clean, bold",
    },
    ImageStyle.ISOMETRIC: {
        "style": "Stylized 3D perspective with clean lines and solid colors",
        "mood": "Modern, dimensional, polished",
    },
    ImageStyle.TECH_THEMED: {
        "style": "Futuristic aesthetic with neon glows and dark moody atmosphere",
        "mood": "Innovative, cutting-edge, bold",
    },
    ImageStyle.PROFESSIONAL: {
        "style": "Corporate elegance with refined gradients and sophisticated typography",
        "mood": "Trustworthy, established, premium",
    },
}

# Technology-specific color palettes with precise hex codes
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
    "github": {"primary": "#24292E", "secondary": "#FFFFFF", "accent": "#2088FF"},
    "jenkins": {"primary": "#D24939", "secondary": "#FFFFFF", "accent": "#335061"},

    # AI/ML
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

# Default palettes by content type when no tech detected
DEFAULT_PALETTES = {
    ContentType.TUTORIAL: {"primary": "#3B82F6", "secondary": "#1E3A5F", "accent": "#00D4FF"},
    ContentType.ANNOUNCEMENT: {"primary": "#8B5CF6", "secondary": "#1E1B4B", "accent": "#F59E0B"},
    ContentType.TIPS: {"primary": "#10B981", "secondary": "#064E3B", "accent": "#FFFFFF"},
    ContentType.STORY: {"primary": "#F59E0B", "secondary": "#1F2937", "accent": "#FFFFFF"},
    ContentType.TECHNICAL: {"primary": "#00D4FF", "secondary": "#0A192F", "accent": "#FFFFFF"},
    ContentType.CAREER: {"primary": "#6366F1", "secondary": "#1E1B4B", "accent": "#F59E0B"},
}

# Dimension info for task description
DIMENSION_INFO = {
    "1200x627": "link post (1200x627)",
    "1080x1080": "square post (1080x1080)",
    "1200x1200": "large square post (1200x1200)",
}


@dataclass
class GeminiPromptComponents:
    """Components for Gemini-optimized prompt structure."""
    dimension_desc: str
    layout_type: str
    background: str
    foreground: str
    headline: str
    subtitle: str
    style: str
    palette: str
    mood: str
    context: str


class GeminiPromptBuilder:
    """Builds optimized prompts for Gemini 3 Pro Image generation."""

    def __init__(self):
        self.layout_types = LAYOUT_TYPES
        self.style_aesthetics = STYLE_AESTHETICS
        self.tech_palettes = TECH_COLOR_PALETTES
        self.default_palettes = DEFAULT_PALETTES
        self.dimension_info = DIMENSION_INFO

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
        """Build a Gemini-optimized prompt.

        Args:
            post_content: The LinkedIn post content.
            style: Selected image style.
            content_type: Classified content type.
            dimensions: Image dimensions (e.g., "1200x627").
            technologies: Detected technologies.
            keywords: Extracted keywords.
            visual_elements: Suggested visual elements.
            sentiment: Content sentiment (unused but kept for API compatibility).

        Returns:
            Optimized prompt string for Gemini 3 Pro Image.
        """
        components = self._assemble_components(
            post_content=post_content,
            style=style,
            content_type=content_type,
            dimensions=dimensions,
            technologies=technologies or [],
            keywords=keywords or [],
            visual_elements=visual_elements or [],
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
    ) -> GeminiPromptComponents:
        """Assemble prompt components for Gemini structure."""

        # Dimension description
        dimension_desc = self.dimension_info.get(dimensions, "link post (1200x627)")

        # Scene composition from content type
        layout = self.layout_types.get(content_type, self.layout_types[ContentType.TECHNICAL])
        layout_type = layout["layout"]
        background = self._enhance_background(layout["background"], technologies, visual_elements)
        foreground = self._enhance_foreground(layout["foreground"], technologies, keywords)

        # Extract headline and subtitle from post content
        headline, subtitle = self._extract_text_elements(post_content, keywords)

        # Aesthetic from style
        aesthetic = self.style_aesthetics.get(style, self.style_aesthetics[ImageStyle.TECH_THEMED])
        style_desc = aesthetic["style"]
        mood = aesthetic["mood"]

        # Color palette
        palette = self._build_palette(technologies, content_type)

        # Context summary
        context = self._build_context_summary(post_content)

        return GeminiPromptComponents(
            dimension_desc=dimension_desc,
            layout_type=layout_type,
            background=background,
            foreground=foreground,
            headline=headline,
            subtitle=subtitle,
            style=style_desc,
            palette=palette,
            mood=mood,
            context=context,
        )

    def _enhance_background(
        self,
        base_background: str,
        technologies: list[str],
        visual_elements: list[str],
    ) -> str:
        """Return base background without adding technical elements."""
        # Don't add tech references - they cause diagram-like outputs
        return base_background

    def _enhance_foreground(
        self,
        base_foreground: str,
        technologies: list[str],
        keywords: list[str],
    ) -> str:
        """Return base foreground without adding technical elements."""
        # Don't add tech/keyword references - they cause diagram-like outputs
        return base_foreground

    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from text.

        Strips asterisks, underscores, and other markdown syntax
        that shouldn't appear in image text.
        """
        # Remove bold/italic markdown: **text**, *text*, __text__, _text_
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)  # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)  # _italic_
        # Remove any remaining stray asterisks
        text = re.sub(r'\*+', '', text)
        return text.strip()

    def _extract_text_elements(
        self,
        post_content: str,
        keywords: list[str],
    ) -> tuple[str, str]:
        """Extract headline and subtitle from post content.

        Attempts to find a compelling headline from the post, falling back
        to keyword-based generation if needed.
        """
        lines = post_content.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]

        headline = ""
        subtitle = ""

        # Try to find a short, impactful first line as headline
        if lines:
            first_line = lines[0]
            # Clean up common LinkedIn post patterns
            first_line = re.sub(r'^[🚀💡🔥✨⚡️🎯]+\s*', '', first_line)  # Remove leading emojis
            first_line = re.sub(r'[🚀💡🔥✨⚡️🎯]+$', '', first_line)  # Remove trailing emojis
            # Clean markdown formatting
            first_line = self._clean_markdown(first_line)

            if len(first_line) <= 60:
                headline = first_line
            else:
                # Truncate to first sentence or phrase
                match = re.match(r'^([^.!?]+[.!?]?)', first_line)
                if match and len(match.group(1)) <= 60:
                    headline = match.group(1)
                else:
                    # Use first few words
                    words = first_line.split()[:6]
                    headline = ' '.join(words)
                    if len(headline) < len(first_line):
                        headline += "..."

        # Generate subtitle from keywords or second line
        if len(lines) > 1:
            second_line = lines[1]
            second_line = re.sub(r'^[🚀💡🔥✨⚡️🎯•\-]+\s*', '', second_line)
            # Clean markdown formatting
            second_line = self._clean_markdown(second_line)
            if len(second_line) <= 50:
                subtitle = second_line
            elif keywords:
                subtitle = ' | '.join(keywords[:3])
        elif keywords:
            subtitle = ' | '.join(keywords[:3])

        # Fallback if no headline extracted
        if not headline and keywords:
            headline = keywords[0].title()
            if len(keywords) > 1:
                subtitle = ' | '.join(keywords[1:4])

        return headline, subtitle

    def _build_palette(
        self,
        technologies: list[str],
        content_type: ContentType,
    ) -> str:
        """Build color palette description without hardcoded hex codes."""
        return "professional colors that complement the content"

    def _build_context_summary(self, post_content: str) -> str:
        """Build one-sentence context summary."""
        content = post_content.strip()

        # Get first meaningful sentence
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]

        if sentences:
            summary = sentences[0]
            # Clean up
            summary = re.sub(r'^[🚀💡🔥✨⚡️🎯]+\s*', '', summary)
            if len(summary) > 150:
                summary = summary[:147] + "..."
            return summary

        # Fallback to truncated content
        if len(content) > 150:
            return content[:147] + "..."
        return content

    def _format_prompt(self, components: GeminiPromptComponents) -> str:
        """Format the final Gemini-optimized prompt.

        Uses narrative description style as recommended by official Gemini docs.
        Focuses on artistic visuals, explicitly avoiding technical diagrams.
        """
        prompt = f"""Create a stunning LinkedIn {components.dimension_desc} image.

VISUAL STYLE: {components.style}. The mood is {components.mood.lower()}.

COMPOSITION: {components.layout_type} layout with {components.background.lower()}. Add {components.foreground.lower()} for visual interest. Use cinematic lighting with soft shadows and subtle depth.

TEXT OVERLAY: Display "{components.headline}" as the main headline in large, bold, modern sans-serif typography. Below it, show "{components.subtitle}" in smaller, lighter text. Ensure text is crisp and highly readable with strong contrast.

COLOR: Use {components.palette.lower()} with rich, harmonious tones.

CONTEXT: This accompanies a LinkedIn post about: {components.context}

CRITICAL - DO NOT INCLUDE:
- No diagrams, flowcharts, or charts
- No neural networks, nodes, or connection lines
- No code, terminals, or IDE screenshots
- No icons, logos, or clip art
- No busy infographics or data visualizations
- No stock photo watermarks

Create an artistic, premium quality image that looks like professional marketing material, not a technical diagram."""

        return prompt


# Backward compatibility alias
NanoBananaPromptBuilder = GeminiPromptBuilder


# Singleton instance
_prompt_builder: Optional[GeminiPromptBuilder] = None


def get_prompt_builder() -> GeminiPromptBuilder:
    """Get the singleton prompt builder instance."""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = GeminiPromptBuilder()
    return _prompt_builder
