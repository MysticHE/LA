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
LAYOUT_TYPES = {
    ContentType.TUTORIAL: {
        "layout": "step-by-step instructional",
        "background": "Clean workspace or IDE interface with subtle code elements",
        "foreground": "Central learning pathway or progression visual with clear hierarchy",
    },
    ContentType.ANNOUNCEMENT: {
        "layout": "bold central hero",
        "background": "Dynamic gradient or abstract tech pattern",
        "foreground": "Prominent 3D icon or symbol representing the announcement",
    },
    ContentType.TIPS: {
        "layout": "modern card grid",
        "background": "Soft gradient with subtle geometric patterns",
        "foreground": "Lightbulb or insight icon with organized tip indicators",
    },
    ContentType.STORY: {
        "layout": "narrative journey",
        "background": "Abstract path or timeline visualization",
        "foreground": "Transformation visual showing before/after or growth arc",
    },
    ContentType.TECHNICAL: {
        "layout": "modern split-screen dashboard",
        "background": "Dark IDE code editor interface or system architecture",
        "foreground": "Glowing tech element, API diagram, or data flow visualization",
    },
    ContentType.CAREER: {
        "layout": "aspirational upward",
        "background": "Professional gradient with subtle corporate elements",
        "foreground": "Rising graph, ladder, or achievement visual",
    },
}

# Style descriptors with aesthetic details
STYLE_AESTHETICS = {
    ImageStyle.INFOGRAPHIC: {
        "style": "Clean infographic design with organized data visualization",
        "mood": "Informative, educational, data-driven",
    },
    ImageStyle.MINIMALIST: {
        "style": "Minimalist design with ample negative space and essential elements only",
        "mood": "Elegant, sophisticated, focused",
    },
    ImageStyle.CONCEPTUAL: {
        "style": "Conceptual illustration with metaphorical imagery and symbolic objects",
        "mood": "Thought-provoking, creative, insightful",
    },
    ImageStyle.ABSTRACT: {
        "style": "Abstract art with flowing shapes, fluid gradients, and artistic patterns",
        "mood": "Innovative, artistic, forward-thinking",
    },
    ImageStyle.PHOTOREALISTIC: {
        "style": "Photorealistic 3D rendering with cinematic lighting and depth",
        "mood": "Authentic, professional, trustworthy",
    },
    ImageStyle.ILLUSTRATED: {
        "style": "Modern illustration with stylized elements and artistic texture",
        "mood": "Friendly, approachable, creative",
    },
    ImageStyle.DIAGRAM: {
        "style": "Technical diagram with flowcharts, connection lines, and system nodes",
        "mood": "Technical, systematic, educational",
    },
    ImageStyle.GRADIENT: {
        "style": "Modern gradient design with smooth color transitions and glassmorphism",
        "mood": "Modern, dynamic, energetic",
    },
    ImageStyle.FLAT_DESIGN: {
        "style": "Flat design with bold geometric shapes, solid colors, and clean icons",
        "mood": "Modern, clean, accessible",
    },
    ImageStyle.ISOMETRIC: {
        "style": "Premium 3D isometric illustration with precise 30-degree angles",
        "mood": "Technical, dimensional, organized",
    },
    ImageStyle.TECH_THEMED: {
        "style": "Premium 3D isometric illustration, glassmorphism UI elements, neon accents",
        "mood": "Innovative, cutting-edge, high-tech",
    },
    ImageStyle.PROFESSIONAL: {
        "style": "Corporate professional design with refined imagery and subtle patterns",
        "mood": "Trustworthy, professional, established",
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
        """Enhance background description with tech context."""
        enhancements = []

        if technologies:
            tech_str = ", ".join(technologies[:2])
            enhancements.append(f"featuring {tech_str} elements")

        if visual_elements:
            elem_str = ", ".join(visual_elements[:2])
            enhancements.append(f"with {elem_str}")

        if enhancements:
            return f"{base_background}, {', '.join(enhancements)}"
        return base_background

    def _enhance_foreground(
        self,
        base_foreground: str,
        technologies: list[str],
        keywords: list[str],
    ) -> str:
        """Enhance foreground description with specific elements."""
        if technologies:
            main_tech = technologies[0]
            return f"{base_foreground} representing {main_tech}"

        if keywords:
            main_keyword = keywords[0]
            return f"{base_foreground} symbolizing {main_keyword}"

        return base_foreground

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
        """Build color palette string with hex codes."""
        palette = None

        # Try to find tech-specific palette
        for tech in technologies[:2]:
            tech_lower = tech.lower()
            if tech_lower in self.tech_palettes:
                palette = self.tech_palettes[tech_lower]
                break

        # Fall back to content type default
        if not palette:
            palette = self.default_palettes.get(
                content_type,
                self.default_palettes[ContentType.TECHNICAL]
            )

        return (
            f"Deep background ({palette['secondary']}) with "
            f"primary accent ({palette['primary']}) and "
            f"highlight ({palette['accent']})"
        )

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
        """Format the final Gemini-optimized prompt."""
        prompt = f"""**Role:** Expert LinkedIn Visual Designer
**Task:** Create a high-conversion image for a {components.dimension_desc}.

**1. SCENE COMPOSITION:**
Create a {components.layout_type} composition.
- **Background:** {components.background}
- **Foreground:** {components.foreground}

**2. TEXT RENDERING (Crucial):**
You MUST render the following text clearly and legibly:
- **Headline:** "{components.headline}" (Large, bold, high contrast)
- **Sub-text:** "{components.subtitle}" (Smaller, secondary color)
*Ensure text has high contrast against the background.*

**3. AESTHETIC & COLOR:**
- **Style:** {components.style}
- **Palette:** {components.palette}
- **Mood:** {components.mood}

**4. CONTEXT:**
The post is about: {components.context}
Ensure the visual metaphors align with this topic.

**CONSTRAINTS:**
- NO watermarks, signatures, or logos
- NO stock photo artifacts or cheesy corporate imagery
- Text must be sharp and readable"""

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
