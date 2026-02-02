"""LinkedIn post repurposing generator.

Uses AI to transform LinkedIn posts into new versions with different
styles, tones, and formats while preserving core value.
"""

from typing import Optional
from src.models.linkedin_models import (
    ContentAnalysisResult,
    RepurposeStyle,
    RepurposeFormat,
    ImageContext,
)


# Shared VALUE_FRAMEWORK from ai_prompt_generator
VALUE_FRAMEWORK = """
ENGAGEMENT RULES (CRITICAL - Apply to EVERY post):

1. FRUSTRATION-FIRST HOOK
   Use the STRONGEST frustration/insight as your opening hook.
   Bad: "Here's something I learned..."
   Good: "Why do 90% of developers still struggle with this?"

2. THE 3-STEP VALUE RULE
   For EVERY key point:
   - Point: The insight or lesson
   - Context: A specific real-world scenario
   - Impact: The outcome (time saved, risk eliminated, capability unlocked)

3. ACTIVE VOICE ONLY
   Replace passive phrases:
   ❌ "It has...", "Included is...", "There is..."
   ✅ "You can now...", "Say goodbye to...", "Finally..."

4. OUTCOME OVER FEATURE
   Lead with what the reader GAINS.
   ❌ "This approach improves productivity"
   ✅ "Save 2 hours every day with this one change"
"""


class RepurposeGenerator:
    """Generates repurposed LinkedIn content using AI."""

    # Style transformation instructions
    STYLE_INSTRUCTIONS = {
        "same": """
Keep the original tone and voice. Focus on:
- Preserving the author's personality
- Maintaining the same level of formality
- Keeping similar emoji usage and formatting
""",
        "professional": """
Transform to a more professional tone:
- Use formal language, avoid slang and casual phrases
- Remove or minimize emojis
- Add industry-relevant terminology
- Structure content with clear sections
- Sound like a thought leader or executive
""",
        "casual": """
Transform to a more conversational tone:
- Use friendly, approachable language
- Add appropriate emojis for personality
- Write like talking to a friend
- Include relatable examples and humor where appropriate
- Keep sentences shorter and punchier
""",
        "storytelling": """
Transform into a narrative/story format:
- Open with a compelling scene or moment
- Build tension or curiosity
- Use "I remember when..." or "Picture this..." structures
- Include sensory details and emotions
- End with a clear lesson or revelation
""",
    }

    # Format transformation instructions
    FORMAT_INSTRUCTIONS = {
        "expanded": """
EXPAND the content:
- Add more context and examples
- Include supporting data or anecdotes
- Elaborate on each key point with use cases
- Aim for 1500-2500 characters
- Add a thought-provoking question at the end
""",
        "condensed": """
CONDENSE the content:
- Keep only the most impactful points
- Remove redundant phrases
- Use bullet points for clarity
- Aim for 500-800 characters
- Make every word count
""",
        "thread": """
FORMAT as a LinkedIn carousel/thread structure:
- Start with a powerful hook (1-2 sentences)
- Number each key point (1., 2., 3., etc.)
- Each point should be 1-2 sentences max
- Add a recap at the end
- Include a CTA to save/share
- Use line breaks generously
""",
    }

    SYSTEM_PROMPT = f"""You are an expert LinkedIn content repurposing specialist.
Your task is to transform existing LinkedIn posts into new versions while:
- Preserving the CORE VALUE and insights
- Adapting the tone/style as requested
- Optimizing for LinkedIn engagement
- NEVER changing facts or making up new information
- NEVER including attribution to original author (clean repurposed content)

{VALUE_FRAMEWORK}

LinkedIn Best Practices:
- Keep posts under 3000 characters
- Use line breaks for mobile readability
- Make the first line attention-grabbing (visible in preview)
- Include 3-5 relevant hashtags at the end
- End with engagement driver (question or CTA)

IMPORTANT: Return ONLY the repurposed post content, no preamble or explanation.
"""

    @classmethod
    def build_prompts(
        cls,
        original_content: str,
        analysis: ContentAnalysisResult,
        target_style: RepurposeStyle = "same",
        target_format: RepurposeFormat = "expanded",
    ) -> tuple[str, str]:
        """Build system and user prompts for AI repurposing.

        Args:
            original_content: The original LinkedIn post.
            analysis: Content analysis results.
            target_style: Target tone/style transformation.
            target_format: Target format transformation.

        Returns:
            Tuple of (system_prompt, user_prompt).
        """
        system_prompt = cls.SYSTEM_PROMPT
        system_prompt += "\n\n--- STYLE TRANSFORMATION ---\n"
        system_prompt += cls.STYLE_INSTRUCTIONS.get(target_style, cls.STYLE_INSTRUCTIONS["same"])
        system_prompt += "\n\n--- FORMAT TRANSFORMATION ---\n"
        system_prompt += cls.FORMAT_INSTRUCTIONS.get(target_format, cls.FORMAT_INSTRUCTIONS["expanded"])

        user_prompt = cls._build_user_prompt(original_content, analysis, target_style, target_format)

        return system_prompt, user_prompt

    @classmethod
    def _build_user_prompt(
        cls,
        original_content: str,
        analysis: ContentAnalysisResult,
        target_style: RepurposeStyle,
        target_format: RepurposeFormat,
    ) -> str:
        """Build the user prompt with content and analysis."""

        themes_str = ", ".join(analysis.themes) if analysis.themes else "General"
        key_points_str = "\n".join(f"- {p}" for p in analysis.key_points) if analysis.key_points else "Not extracted"
        entities_str = ", ".join(analysis.entities) if analysis.entities else "None identified"
        hashtags_str = " ".join(f"#{h}" for h in analysis.hashtags) if analysis.hashtags else "None"

        return f"""Repurpose this LinkedIn post:

---
ORIGINAL POST:
{original_content}
---

ANALYSIS OF ORIGINAL:
- Themes: {themes_str}
- Original Tone: {analysis.tone}
- Content Type: {analysis.content_type}
- Key Points:
{key_points_str}
- Mentioned Entities: {entities_str}
- Original Hashtags: {hashtags_str}

---

TRANSFORMATION REQUEST:
- Target Style: {target_style}
- Target Format: {target_format}

---

INSTRUCTIONS:
1. Preserve all factual information and insights
2. Transform the tone to match "{target_style}" style
3. Restructure to "{target_format}" format
4. Make the hook stronger and more engaging
5. Ensure value is clear for the reader
6. Add 3-5 relevant hashtags at the end (can keep or improve original ones)

Generate the repurposed LinkedIn post now.
"""


def extract_image_context(
    repurposed_content: str,
    analysis: ContentAnalysisResult
) -> ImageContext:
    """Extract context for image generation from repurposed content.

    Args:
        repurposed_content: The repurposed post content.
        analysis: Original content analysis.

    Returns:
        ImageContext for image generation.
    """
    # Extract headline from first line
    lines = repurposed_content.strip().split('\n')
    first_line = lines[0] if lines else ""

    # Clean the headline
    headline = first_line.strip()
    # Remove emojis from start/end
    headline = headline.strip('🔥💡🚀⚡✨📈💪🎯')
    # Truncate if too long
    if len(headline) > 60:
        headline = headline[:57] + "..."

    # Extract subtitle from second meaningful line
    subtitle = None
    for line in lines[1:4]:
        line = line.strip()
        if len(line) > 20 and len(line) < 80:
            subtitle = line
            break

    # Recommend styles based on content type
    style_recommendations = {
        "story": ["conceptual", "illustrated", "photorealistic"],
        "tips": ["infographic", "minimalist", "flat_design"],
        "announcement": ["gradient", "professional", "tech_themed"],
        "opinion": ["abstract", "minimalist", "conceptual"],
        "case-study": ["infographic", "diagram", "professional"],
    }
    recommended_styles = style_recommendations.get(
        analysis.content_type,
        ["minimalist", "professional", "gradient"]
    )

    return ImageContext(
        content_type=analysis.content_type,
        headline=headline,
        subtitle=subtitle,
        recommended_styles=recommended_styles,
        themes=analysis.themes,
    )


def suggest_hashtags(
    analysis: ContentAnalysisResult,
    repurposed_content: str
) -> list[str]:
    """Suggest hashtags for the repurposed content.

    Args:
        analysis: Content analysis results.
        repurposed_content: The repurposed content.

    Returns:
        List of suggested hashtags.
    """
    # Start with original hashtags
    hashtags = set(analysis.hashtags)

    # Add theme-based hashtags
    theme_hashtags = {
        "career growth": ["CareerGrowth", "CareerDevelopment", "ProfessionalGrowth"],
        "leadership": ["Leadership", "Management", "LeadershipDevelopment"],
        "technology": ["Tech", "Technology", "Innovation"],
        "startup": ["Startup", "Entrepreneurship", "StartupLife"],
        "productivity": ["Productivity", "Efficiency", "WorkSmarter"],
        "AI/ML": ["AI", "MachineLearning", "ArtificialIntelligence"],
        "remote work": ["RemoteWork", "WFH", "FutureOfWork"],
        "learning": ["Learning", "ContinuousLearning", "LifelongLearning"],
    }

    for theme in analysis.themes:
        if theme in theme_hashtags:
            hashtags.update(theme_hashtags[theme][:2])

    # Add entity-based hashtags
    for entity in analysis.entities:
        if len(entity) > 2 and entity.isalnum():
            hashtags.add(entity)

    return list(hashtags)[:7]
