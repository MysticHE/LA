import os
from pathlib import Path
from src.models.schemas import AnalysisResult, PostStyle, GeneratedPrompt


class PromptBuilder:
    """Build prompts for LinkedIn post generation."""

    def __init__(self):
        self.prompts_dir = Path(__file__).parent.parent.parent / "prompts"

    def build(self, analysis: AnalysisResult, style: PostStyle) -> GeneratedPrompt:
        """Build a prompt from analysis results and style."""
        template = self._load_template(style)
        formatted_prompt = self._format_template(template, analysis)

        instructions = self._get_instructions(style)

        return GeneratedPrompt(
            style=style, prompt=formatted_prompt, instructions=instructions
        )

    def _load_template(self, style: PostStyle) -> str:
        """Load the prompt template for the given style."""
        template_files = {
            PostStyle.PROBLEM_SOLUTION: "problem_solution.md",
            PostStyle.TIPS_LEARNINGS: "tips_learnings.md",
            PostStyle.TECHNICAL_SHOWCASE: "technical_showcase.md",
        }

        template_path = self.prompts_dir / template_files[style]

        if template_path.exists():
            return template_path.read_text(encoding="utf-8")

        return self._get_default_template(style)

    def _format_template(self, template: str, analysis: AnalysisResult) -> str:
        """Format the template with analysis data."""
        tech_stack_str = ", ".join(
            [f"{t.name} ({t.category})" for t in analysis.tech_stack]
        )

        features_str = "\n".join(
            [f"- {f.name}: {f.description}" for f in analysis.features]
        )

        file_structure_str = "\n".join(analysis.file_structure[:20])

        replacements = {
            "{repo_name}": analysis.repo_name,
            "{description}": analysis.description or "No description provided",
            "{tech_stack}": tech_stack_str or "Not detected",
            "{features}": features_str or "No features detected",
            "{readme_summary}": analysis.readme_summary or "No README summary available",
            "{file_structure}": file_structure_str or "Not available",
            "{stars}": str(analysis.stars),
            "{forks}": str(analysis.forks),
            "{language}": analysis.language or "Unknown",
        }

        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)

        return result

    def _get_instructions(self, style: PostStyle) -> str:
        """Get usage instructions for the prompt."""
        style_names = {
            PostStyle.PROBLEM_SOLUTION: "Problem-Solution",
            PostStyle.TIPS_LEARNINGS: "Tips & Learnings",
            PostStyle.TECHNICAL_SHOWCASE: "Technical Showcase",
        }

        return f"""
## How to use this prompt:

1. Copy the prompt above
2. Open Claude Code CLI: `claude`
3. Paste the prompt and press Enter
4. Review and edit the generated LinkedIn post
5. Copy the final post to LinkedIn

**Style**: {style_names[style]}
**Character limit**: 3000 (LinkedIn max)

**Pro tips**:
- Ask Claude to make it more personal if the first draft feels generic
- Request specific adjustments like "make the hook more attention-grabbing"
- Ask for hashtag suggestions relevant to your audience
""".strip()

    def _get_default_template(self, style: PostStyle) -> str:
        """Return a default template if file doesn't exist."""
        return f"""
# LinkedIn Post Request

Based on this project:
**Name**: {{repo_name}}
**Description**: {{description}}
**Tech Stack**: {{tech_stack}}
**Features**: {{features}}

Please write an engaging LinkedIn post in {style.value} format.
Keep it under 3000 characters. Include relevant hashtags.
""".strip()
