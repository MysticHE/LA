from src.models.schemas import PostStyle, TemplateInfo


class TemplateManager:
    """Manage LinkedIn post templates."""

    TEMPLATES = {
        PostStyle.PROBLEM_SOLUTION: TemplateInfo(
            id=PostStyle.PROBLEM_SOLUTION,
            name="Problem-Solution",
            description="Start with a relatable problem, then present your project as the solution. Best for projects that solve a specific pain point.",
        ),
        PostStyle.TIPS_LEARNINGS: TemplateInfo(
            id=PostStyle.TIPS_LEARNINGS,
            name="Tips & Learnings",
            description="Share key insights and lessons learned while building the project. Great for educational content and thought leadership.",
        ),
        PostStyle.TECHNICAL_SHOWCASE: TemplateInfo(
            id=PostStyle.TECHNICAL_SHOWCASE,
            name="Technical Showcase",
            description="Highlight the architecture, tech stack, and technical decisions. Perfect for developer audiences and technical discussions.",
        ),
    }

    @classmethod
    def get_all(cls) -> list[TemplateInfo]:
        """Get all available templates."""
        return list(cls.TEMPLATES.values())

    @classmethod
    def get_by_style(cls, style: PostStyle) -> TemplateInfo:
        """Get template info by style."""
        return cls.TEMPLATES[style]

    @classmethod
    def validate_content_length(cls, content: str) -> tuple[bool, int]:
        """
        Validate content length for LinkedIn.
        Returns (is_valid, char_count).
        """
        char_count = len(content)
        is_valid = char_count <= 3000
        return is_valid, char_count
