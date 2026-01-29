"""AI prompt generator for Claude-powered LinkedIn post generation.

This module builds system prompts and user prompts for Claude to generate
LinkedIn posts based on repository analysis and selected post style.
"""

from src.models.schemas import AnalysisResult, PostStyle, RepositoryOwnership


class AIPromptGenerator:
    """Generate prompts for Claude AI to create LinkedIn posts."""

    # Ownership-specific instructions for perspective
    OWNERSHIP_INSTRUCTIONS = {
        RepositoryOwnership.OWN: """
IMPORTANT - AUTHOR PERSPECTIVE:
You are the author/creator of this project. Write from first-person author perspective.
- Use phrases like "I built...", "My project...", "I created...", "When I was building..."
- Share personal motivations, decisions, and challenges you faced
- Call-to-action: Star the repo, try it out, contribute, give feedback
""",
        RepositoryOwnership.DISCOVERED: """
IMPORTANT - DISCOVERER PERSPECTIVE:
You discovered this amazing project created by someone else. Write from discoverer perspective.
- Use phrases like "I found...", "I came across...", "Check out this project by..."
- Give credit to the original author(s) and their work
- Explain why this project is worth sharing and what impressed you
- Call-to-action: Follow the creator, give it a star, check out their work
""",
    }

    # Style-specific instructions for Claude
    STYLE_INSTRUCTIONS = {
        PostStyle.PROBLEM_SOLUTION: """
You are writing a LinkedIn post in the Problem-Solution style.
Structure:
1. Start with a hook that identifies a relatable problem developers face
2. Build tension by describing the impact of the problem
3. Introduce the project as the solution
4. Highlight 2-3 key features that address the problem
5. End with a call-to-action (check it out, star on GitHub, etc.)
Tone: Empathetic, professional, solution-focused
""",
        PostStyle.TIPS_LEARNINGS: """
You are writing a LinkedIn post in the Tips & Learnings style.
Structure:
1. Start with "Here's what I learned building [project]..." or similar
2. Share 3-5 specific, actionable insights or lessons
3. Use numbered lists or bullet points for readability
4. Include both technical and non-technical learnings
5. End with encouragement for others on similar journeys
Tone: Reflective, educational, humble
""",
        PostStyle.TECHNICAL_SHOWCASE: """
You are writing a LinkedIn post in the Technical Showcase style.
Structure:
1. Open with an impressive technical achievement or metric
2. Briefly describe the architecture and key technologies
3. Highlight interesting technical decisions and trade-offs
4. Share performance metrics or technical capabilities if available
5. Invite technical discussions or questions
Tone: Technical but accessible, enthusiastic about the tech
""",
    }

    SYSTEM_PROMPT = """You are an expert LinkedIn content writer specializing in developer and tech content.
Your posts are engaging, authentic, and optimized for LinkedIn's algorithm.

Guidelines:
- Keep posts under 3000 characters (LinkedIn's limit)
- Use line breaks generously for mobile readability
- Include relevant hashtags (3-5) at the end
- Write in first person, conversational tone
- Avoid jargon unless appropriate for developer audience
- Include emojis sparingly for visual appeal
- Make the first line attention-grabbing (it appears in the preview)
- End with a clear call-to-action or question to drive engagement

IMPORTANT: Return ONLY the LinkedIn post content, no preamble or explanation.
"""

    @classmethod
    def generate_prompt(
        cls,
        analysis: AnalysisResult,
        style: PostStyle,
        ownership: RepositoryOwnership = RepositoryOwnership.OWN,
    ) -> tuple[str, str]:
        """Generate system and user prompts for Claude.

        Args:
            analysis: The repository analysis result.
            style: The post style to use.
            ownership: Whether user owns or discovered the project.

        Returns:
            Tuple of (system_prompt, user_prompt).
        """
        system_prompt = cls.SYSTEM_PROMPT
        system_prompt += cls.STYLE_INSTRUCTIONS.get(style, "")
        system_prompt += cls.OWNERSHIP_INSTRUCTIONS.get(ownership, "")

        user_prompt = cls._build_user_prompt(analysis, style, ownership)

        return system_prompt, user_prompt

    @classmethod
    def _build_user_prompt(
        cls,
        analysis: AnalysisResult,
        style: PostStyle,
        ownership: RepositoryOwnership = RepositoryOwnership.OWN,
    ) -> str:
        """Build the user prompt with analysis data.

        Args:
            analysis: The repository analysis result.
            style: The post style to use.
            ownership: Whether user owns or discovered the project.

        Returns:
            The user prompt string.
        """
        # Format tech stack
        tech_stack_str = ", ".join(
            [f"{t.name}" for t in analysis.tech_stack]
        ) if analysis.tech_stack else "Not specified"

        # Format features
        features_str = "\n".join(
            [f"- {f.name}: {f.description}" for f in analysis.features]
        ) if analysis.features else "Not specified"

        style_name = {
            PostStyle.PROBLEM_SOLUTION: "Problem-Solution",
            PostStyle.TIPS_LEARNINGS: "Tips & Learnings",
            PostStyle.TECHNICAL_SHOWCASE: "Technical Showcase",
        }.get(style, style.value)

        ownership_context = (
            "You are the AUTHOR of this project."
            if ownership == RepositoryOwnership.OWN
            else "You DISCOVERED this project (you did NOT create it)."
        )

        prompt = f"""Write a LinkedIn post about this GitHub project:

**Ownership**: {ownership_context}
**Project Name**: {analysis.repo_name}
**Description**: {analysis.description or 'Not provided'}
**Primary Language**: {analysis.language or 'Not specified'}
**Tech Stack**: {tech_stack_str}
**GitHub Stats**: {analysis.stars} stars, {analysis.forks} forks

**Key Features**:
{features_str}

**README Summary**:
{analysis.readme_summary or 'Not available'}

**Post Style**: {style_name}

Generate an engaging LinkedIn post following the {style_name} format.
Remember to write from the correct perspective based on the ownership context above.
"""
        return prompt
