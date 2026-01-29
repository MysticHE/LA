"""AI prompt generator for Claude-powered LinkedIn post generation.

This module builds system prompts and user prompts for Claude to generate
LinkedIn posts based on repository analysis and selected post style.
"""

from src.models.schemas import AnalysisResult, PostStyle, RepositoryOwnership


VALUE_FRAMEWORK = """
ENGAGEMENT RULES (CRITICAL - Apply to EVERY post):

1. FRUSTRATION-FIRST HOOK
   Before writing, identify the 3 most frustrating problems developers face that this project solves.
   Use the STRONGEST frustration as your opening hook.
   Bad: "I built a tool that does X"
   Good: "Tired of spending 2 hours configuring webpack every project?"

2. THE 3-STEP VALUE RULE
   For EVERY feature you mention, include:
   - Feature: What it does
   - Use Case: A specific real-world scenario
   - Benefit: The outcome (time saved, risk eliminated, capability unlocked)

   Example: "Runs locally (feature) → Process sensitive client data (use case) → Zero security risk (benefit)"

3. ACTIVE VOICE ONLY
   Replace passive phrases:
   ❌ "It has...", "Included is...", "There is...", "It provides..."
   ✅ "You can now...", "Say goodbye to...", "Finally...", "Stop wasting time on..."

4. OUTCOME OVER FEATURE
   Lead with what the reader GAINS, not what the tool HAS.
   ❌ "Features real-time sync"
   ✅ "Never lose work to a browser crash again"
"""


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

BEFORE WRITING: Identify the 3 biggest frustrations your target audience has. Pick the most painful one for your hook.

Structure:
1. HOOK: Start with a frustration statement the reader has experienced (NOT "I built...")
2. AGITATE: Describe the consequences of this problem (wasted time, security risks, missed deadlines)
3. SOLUTION: Introduce the project as the answer
4. VALUE PROOF: Show 2-3 features WITH their real-world use cases and benefits
5. CTA: Ask a question that invites them to share their own frustrations

Tone: Empathetic, relatable, solution-focused
Example hook: "How many hours have you lost debugging CORS errors this month?"
""",
        PostStyle.TIPS_LEARNINGS: """
You are writing a LinkedIn post in the Tips & Learnings style.

BEFORE WRITING: Think about what SURPRISED you while building this. What did you learn that others might not know?

Structure:
1. HOOK: Start with a counterintuitive insight or "I was wrong about..." statement
2. CONTEXT: Brief setup (1-2 sentences about what you were building)
3. LESSONS: 3-5 tips, each structured as:
   - The mistake/assumption I made
   - What I learned
   - What you should do instead
4. TAKEAWAY: The one thing to remember
5. CTA: "What's the most surprising thing you learned building [related topic]?"

Tone: Reflective, vulnerable, educational
""",
        PostStyle.TECHNICAL_SHOWCASE: """
You are writing a LinkedIn post in the Technical Showcase style.

BEFORE WRITING: What technical decision would make another developer say "oh that's clever"?

Structure:
1. HOOK: Lead with a surprising metric OR a "Here's why I didn't use [popular thing]"
2. THE PROBLEM: What technical challenge did this solve? (Be specific)
3. THE APPROACH: Key architecture decisions WITH reasoning
4. THE TRADE-OFF: What did you sacrifice and why it was worth it
5. THE RESULT: Concrete outcomes (speed, maintainability, developer experience)
6. CTA: Invite debate ("Would you have done it differently?")

Tone: Technical but conversational, confident but open to discussion
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
""" + VALUE_FRAMEWORK

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
    def _infer_audience(cls, analysis: AnalysisResult) -> str:
        """Infer target audience from tech stack and features."""
        tech_names = [t.name.lower() for t in analysis.tech_stack]
        desc = (analysis.description or "").lower()

        audiences = []

        if any(t in tech_names for t in ["react", "vue", "angular", "next.js", "nextjs"]):
            audiences.append("frontend developers")
        if any(t in tech_names for t in ["fastapi", "django", "express", "nestjs", "flask"]):
            audiences.append("backend developers")
        if any(t in tech_names for t in ["docker", "kubernetes", "terraform", "aws", "azure"]):
            audiences.append("DevOps engineers")
        if any(t in tech_names for t in ["openai", "langchain", "claude", "llm", "gpt"]):
            audiences.append("AI/ML engineers")
        if any(t in tech_names for t in ["typescript", "rust", "go"]):
            audiences.append("developers who value type safety/performance")
        if "cli" in desc or "command" in desc or "terminal" in desc:
            audiences.append("developers who prefer terminal workflows")
        if "api" in desc:
            audiences.append("developers building integrations")

        if not audiences:
            audiences.append("software developers")

        return ", ".join(audiences[:3])

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

        # Generate value-oriented feature descriptions
        features_with_value = []
        for f in analysis.features[:5]:  # Limit to top 5
            features_with_value.append(
                f"- {f.name}: {f.description}\n"
                f"  → Think: What problem does this solve? What can the user now do?"
            )
        features_value_str = (
            "\n".join(features_with_value) if features_with_value else "Not specified"
        )

        # Infer target audience
        audience_hints = cls._infer_audience(analysis)

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

---

**THE "SO WHAT?" FRAMEWORK** (Use this to find your hook):

Likely Target Audience: {audience_hints}

Think about:
- What tedious task does this eliminate?
- What risky process does this make safe?
- What expensive thing does this make free?
- What complex thing does this make simple?

---

**Features to Translate into Value**:
{features_value_str}

For each feature above, identify:
1. A real-world scenario where someone would use this
2. The outcome/benefit they get

---

**README Context**:
{analysis.readme_summary or 'Not available'}

---

**Post Style**: {style_name}

CRITICAL INSTRUCTION: Start by identifying the strongest frustration this project addresses. Use that as your opening hook. Do NOT start with "I built..." or "Introducing...".

Generate an engaging LinkedIn post following the {style_name} format.
Remember to write from the correct perspective based on the ownership context above.
"""
        return prompt
