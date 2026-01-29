"""Analyzer for generating reader-friendly project insights."""

import json
import logging
from typing import Optional, TYPE_CHECKING

from src.models.schemas import ProjectInsight, InsightType, TechStackItem

if TYPE_CHECKING:
    from src.services.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


PLATFORM_PATTERNS: list[dict] = [
    {
        "patterns": ["vercel.json", "@vercel/"],
        "title": "Vercel Deployment",
        "description": "Deployed on Vercel - optimized for global edge delivery",
        "icon": "▲",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["netlify.toml", "netlify"],
        "title": "Netlify Deployment",
        "description": "Netlify deployment - JAMstack optimized hosting",
        "icon": "🌐",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["aws-sdk", "serverless.yml", "@aws-sdk/"],
        "title": "AWS Infrastructure",
        "description": "AWS cloud infrastructure - enterprise-grade scalability",
        "icon": "☁️",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["Dockerfile", "docker-compose"],
        "title": "Containerized",
        "description": "Containerized deployment - consistent across environments",
        "icon": "🐳",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["railway.json"],
        "title": "Railway Deployment",
        "description": "Modern PaaS deployment - simplified DevOps",
        "icon": "🚂",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["render.yaml"],
        "title": "Render Deployment",
        "description": "Modern PaaS deployment - simplified DevOps",
        "icon": "🎨",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["@supabase/supabase-js", "supabase"],
        "title": "Supabase Backend",
        "description": "Supabase backend - real-time database + auth in one",
        "icon": "⚡",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["firebase", "@firebase/"],
        "title": "Firebase Integration",
        "description": "Firebase integration - Google's app development platform",
        "icon": "🔥",
        "type": InsightType.HIGHLIGHT,
    },
]

SERVICE_PATTERNS: list[dict] = [
    {
        "patterns": ["stripe"],
        "title": "Stripe Payments",
        "description": "Stripe payments - secure payment processing integrated",
        "icon": "💳",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["@auth0/", "auth0"],
        "title": "Auth0 Authentication",
        "description": "Enterprise auth solution - secure user management",
        "icon": "🔐",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["@clerk/", "clerk"],
        "title": "Clerk Authentication",
        "description": "Modern auth platform - seamless user management",
        "icon": "🔐",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["@sendgrid/", "sendgrid"],
        "title": "SendGrid Email",
        "description": "Transactional email service - reliable email delivery",
        "icon": "📧",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["resend"],
        "title": "Resend Email",
        "description": "Modern email API - developer-friendly email delivery",
        "icon": "📧",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["twilio"],
        "title": "Twilio Integration",
        "description": "Twilio integration - SMS/voice communication enabled",
        "icon": "📱",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["cloudinary"],
        "title": "Cloudinary Media",
        "description": "Cloudinary - optimized image/video management",
        "icon": "🖼️",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["algoliasearch", "algolia"],
        "title": "Algolia Search",
        "description": "Algolia search - lightning-fast search experience",
        "icon": "🔍",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["@sentry/", "sentry"],
        "title": "Error Monitoring",
        "description": "Error monitoring - production issue tracking",
        "icon": "🐛",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["mixpanel", "amplitude", "posthog"],
        "title": "Product Analytics",
        "description": "Product analytics - user behavior tracking",
        "icon": "📊",
        "type": InsightType.HIGHLIGHT,
    },
]

AI_PATTERNS: list[dict] = [
    {
        "patterns": ["openai"],
        "title": "OpenAI Integration",
        "description": "OpenAI integration - GPT-powered AI capabilities",
        "icon": "🤖",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["@anthropic-ai/sdk", "anthropic"],
        "title": "Claude AI",
        "description": "Claude AI - advanced reasoning capabilities",
        "icon": "🧠",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["langchain"],
        "title": "LangChain",
        "description": "LangChain - sophisticated AI workflow orchestration",
        "icon": "🔗",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["pinecone", "chromadb", "weaviate", "@pinecone-database/"],
        "title": "Vector Database",
        "description": "Vector database - semantic search & AI memory",
        "icon": "🧮",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["transformers", "huggingface", "@huggingface/"],
        "title": "Hugging Face",
        "description": "Hugging Face - access to thousands of ML models",
        "icon": "🤗",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["replicate"],
        "title": "Replicate AI",
        "description": "Replicate - easy access to open-source AI models",
        "icon": "🎭",
        "type": InsightType.HIGHLIGHT,
    },
]

ARCHITECTURE_PATTERNS: list[dict] = [
    {
        "patterns": ["turbo.json", "nx.json", "lerna.json"],
        "title": "Monorepo Architecture",
        "description": "Monorepo architecture - unified codebase management",
        "icon": "📦",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["@apollo/", "graphql", "apollo-server"],
        "title": "GraphQL API",
        "description": "GraphQL API - flexible, efficient data fetching",
        "icon": "📡",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["@trpc/"],
        "title": "tRPC",
        "description": "End-to-end type safety - seamless API integration",
        "icon": "🔷",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["kafkajs", "kafka", "rabbitmq", "amqplib", "bull", "bullmq"],
        "title": "Event-Driven Architecture",
        "description": "Event-driven architecture - scalable async processing",
        "icon": "⚡",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["serverless", "@aws-cdk/"],
        "title": "Serverless Architecture",
        "description": "Serverless architecture - pay-per-use, auto-scaling",
        "icon": "λ",
        "type": InsightType.STRENGTH,
    },
]

UX_PATTERNS: list[dict] = [
    {
        "patterns": ["socket.io", "pusher", "ably", "@pusher/"],
        "title": "Real-Time Updates",
        "description": "Real-time updates - live data synchronization",
        "icon": "🔴",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["next-pwa", "workbox", "@ducanh2912/next-pwa"],
        "title": "Progressive Web App",
        "description": "Progressive Web App - installable, offline-capable",
        "icon": "📲",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["next-intl", "i18next", "react-intl", "react-i18next"],
        "title": "Internationalization",
        "description": "Internationalization - multi-language support",
        "icon": "🌍",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["next-themes", "theme-ui"],
        "title": "Dark Mode",
        "description": "Dark mode support - user preference respected",
        "icon": "🌙",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["@axe-core/", "pa11y", "axe-core"],
        "title": "Accessibility Testing",
        "description": "Accessibility-focused - inclusive user experience",
        "icon": "♿",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["framer-motion", "gsap", "@formkit/auto-animate"],
        "title": "Rich Animations",
        "description": "Rich animations - polished user interactions",
        "icon": "✨",
        "type": InsightType.HIGHLIGHT,
    },
]

DATA_PATTERNS: list[dict] = [
    {
        "patterns": ["pg", "postgres", "postgresql", "@prisma/client"],
        "title": "PostgreSQL Database",
        "description": "PostgreSQL database - robust relational data storage",
        "icon": "🐘",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["mongoose", "mongodb"],
        "title": "MongoDB Database",
        "description": "MongoDB - flexible document-based storage",
        "icon": "🍃",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["redis", "ioredis"],
        "title": "Redis Caching",
        "description": "Redis caching - high-performance data layer",
        "icon": "⚡",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["@aws-sdk/client-s3", "minio"],
        "title": "Cloud Storage",
        "description": "Cloud storage - scalable file management",
        "icon": "☁️",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["@planetscale/", "planetscale"],
        "title": "PlanetScale Database",
        "description": "PlanetScale - serverless MySQL with branching",
        "icon": "🪐",
        "type": InsightType.STRENGTH,
    },
]

BUSINESS_PATTERNS: list[dict] = [
    {
        "patterns": ["subscription", "billing", "plans"],
        "title": "SaaS-Ready",
        "description": "SaaS-ready - subscription management built-in",
        "icon": "💼",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["tenant", "organization", "multi-tenant"],
        "title": "Multi-Tenant Architecture",
        "description": "Multi-tenant architecture - enterprise-ready",
        "icon": "🏢",
        "type": InsightType.STRENGTH,
    },
    {
        "patterns": ["admin", "dashboard"],
        "title": "Admin Dashboard",
        "description": "Admin dashboard - built-in management interface",
        "icon": "📊",
        "type": InsightType.HIGHLIGHT,
    },
    {
        "patterns": ["api-key", "rate-limit", "usage"],
        "title": "API-First Design",
        "description": "API-first design - potential for API monetization",
        "icon": "🔌",
        "type": InsightType.STRENGTH,
    },
]

ALL_PATTERNS = (
    PLATFORM_PATTERNS
    + SERVICE_PATTERNS
    + AI_PATTERNS
    + ARCHITECTURE_PATTERNS
    + UX_PATTERNS
    + DATA_PATTERNS
    + BUSINESS_PATTERNS
)


class InsightsAnalyzer:
    """Analyzes project to generate reader-friendly insights.

    Supports AI-powered analysis with fallback to pattern matching.
    """

    # AI prompt for insights analysis
    INSIGHTS_PROMPT = """Analyze this project for LinkedIn-worthy insights.

README (truncated):
{readme}

Tech Stack: {tech_stack}

File Structure Sample: {file_structure}

Identify project insights and categorize them:
- "strength": Robust capabilities that show technical maturity (deployment, monitoring, architecture patterns, testing)
- "highlight": Notable features that make the project interesting (AI integration, real-time features, payments, unique functionality)
- "consideration": Areas for improvement or things to note (missing auth, no database, limited deployment options)

Return a JSON array:
[{{"type": "strength|highlight|consideration", "title": "Short Title (2-4 words)", "description": "One sentence description", "icon": "single emoji"}}]

Guidelines:
- Focus on what would impress or interest a LinkedIn audience
- Be specific to this project, not generic
- Return 3-8 most relevant insights
- Each description should be concise (under 80 characters)

Return ONLY the JSON array, no explanation."""

    def __init__(self, ai_client: Optional["OpenAIClient"] = None):
        """Initialize the insights analyzer.

        Args:
            ai_client: Optional AI client for enhanced analysis.
        """
        self.ai_client = ai_client

    def analyze(
        self,
        tech_stack: list[TechStackItem],
        file_contents: dict[str, str],
        file_structure: list[str],
        primary_language: Optional[str] = None,
        readme: Optional[str] = None,
    ) -> list[ProjectInsight]:
        """Analyze project and return insights.

        Uses AI analysis if available and README is provided, falls back to pattern matching.
        """
        # Try AI analysis first if client and README are available
        if self.ai_client and readme:
            ai_result = self._analyze_with_ai(tech_stack, readme, file_structure)
            if ai_result:
                return ai_result

        # Fallback to pattern matching
        return self._analyze_with_patterns(
            tech_stack, file_contents, file_structure, primary_language
        )

    def _analyze_with_ai(
        self,
        tech_stack: list[TechStackItem],
        readme: str,
        file_structure: list[str],
    ) -> Optional[list[ProjectInsight]]:
        """Analyze project insights using AI.

        Args:
            tech_stack: List of detected technologies.
            readme: README content.
            file_structure: List of file paths.

        Returns:
            List of ProjectInsight or None if AI analysis fails.
        """
        try:
            # Prepare tech stack string
            tech_stack_str = ", ".join([t.name for t in tech_stack]) or "Not specified"

            # Truncate README for token efficiency
            truncated_readme = readme[:4000] if len(readme) > 4000 else readme

            # Sample file structure (limit to 50 items)
            file_structure_sample = "\n".join(file_structure[:50])

            prompt = self.INSIGHTS_PROMPT.format(
                readme=truncated_readme,
                tech_stack=tech_stack_str,
                file_structure=file_structure_sample,
            )

            result = self.ai_client.generate_content(
                system_prompt="You are a technical analyst identifying LinkedIn-worthy project insights. Return only valid JSON.",
                user_prompt=prompt,
            )

            if not result.success or not result.content:
                logger.debug("AI insights analysis failed: %s", result.error)
                return None

            # Parse JSON response
            insights = self._parse_ai_response(result.content)
            if insights:
                logger.debug("AI insights analysis returned %d items", len(insights))
                return insights

            return None

        except Exception as e:
            logger.debug("AI insights analysis error: %s", str(e))
            return None

    def _parse_ai_response(self, response: str) -> Optional[list[ProjectInsight]]:
        """Parse AI response into ProjectInsight list."""
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Handle markdown code blocks
            if response.startswith("```"):
                lines = response.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block:
                        json_lines.append(line)
                response = "\n".join(json_lines)

            # Find JSON array in response
            start = response.find("[")
            end = response.rfind("]") + 1
            if start == -1 or end == 0:
                return None

            json_str = response[start:end]
            data = json.loads(json_str)

            if not isinstance(data, list):
                return None

            insights = []
            seen_titles = set()
            type_map = {
                "strength": InsightType.STRENGTH,
                "highlight": InsightType.HIGHLIGHT,
                "consideration": InsightType.CONSIDERATION,
            }

            for item in data:
                if not isinstance(item, dict):
                    continue

                title = item.get("title", "").strip()
                description = item.get("description", "").strip()
                icon = item.get("icon", "📌").strip()
                insight_type_str = item.get("type", "highlight").strip().lower()

                if not title or not description or title in seen_titles:
                    continue

                insight_type = type_map.get(insight_type_str, InsightType.HIGHLIGHT)

                # Ensure icon is a single character/emoji
                if len(icon) > 4:
                    icon = "📌"

                insights.append(
                    ProjectInsight(
                        type=insight_type,
                        title=title,
                        description=description,
                        icon=icon,
                    )
                )
                seen_titles.add(title)

            return insights if insights else None

        except (json.JSONDecodeError, ValueError) as e:
            logger.debug("Failed to parse AI insights response: %s", str(e))
            return None

    def _analyze_with_patterns(
        self,
        tech_stack: list[TechStackItem],
        file_contents: dict[str, str],
        file_structure: list[str],
        primary_language: Optional[str] = None,
    ) -> list[ProjectInsight]:
        """Analyze project insights using pattern matching (fallback)."""
        insights: list[ProjectInsight] = []
        seen_titles: set[str] = set()

        combined_content = self._combine_content(file_contents, file_structure)
        tech_names = {t.name.lower() for t in tech_stack}

        for pattern_def in ALL_PATTERNS:
            if self._matches_pattern(
                pattern_def["patterns"], combined_content, tech_names
            ):
                title = pattern_def["title"]
                if title not in seen_titles:
                    seen_titles.add(title)
                    insights.append(
                        ProjectInsight(
                            type=pattern_def["type"],
                            title=title,
                            description=pattern_def["description"],
                            icon=pattern_def["icon"],
                        )
                    )

        considerations = self._detect_considerations(
            tech_stack, file_contents, file_structure, primary_language
        )
        for consideration in considerations:
            if consideration.title not in seen_titles:
                seen_titles.add(consideration.title)
                insights.append(consideration)

        return insights

    def _combine_content(
        self, file_contents: dict[str, str], file_structure: list[str]
    ) -> str:
        """Combine all file contents and structure for pattern matching."""
        parts = list(file_contents.values()) + file_structure
        return " ".join(parts).lower()

    def _matches_pattern(
        self, patterns: list[str], content: str, tech_names: set[str]
    ) -> bool:
        """Check if any pattern matches in content or tech stack."""
        for pattern in patterns:
            pattern_lower = pattern.lower()
            if pattern_lower in content or pattern_lower in tech_names:
                return True
        return False

    def _detect_considerations(
        self,
        tech_stack: list[TechStackItem],
        file_contents: dict[str, str],
        file_structure: list[str],
        primary_language: Optional[str],
    ) -> list[ProjectInsight]:
        """Detect potential considerations."""
        considerations: list[ProjectInsight] = []
        combined_content = self._combine_content(file_contents, file_structure)
        tech_names = {t.name.lower() for t in tech_stack}

        auth_indicators = [
            "auth",
            "login",
            "session",
            "@auth0/",
            "@clerk/",
            "nextauth",
            "passport",
            "jwt",
            "firebase-auth",
            "supabase-auth",
        ]
        has_auth = any(ind in combined_content for ind in auth_indicators)
        if not has_auth:
            considerations.append(
                ProjectInsight(
                    type=InsightType.CONSIDERATION,
                    title="No Auth Detected",
                    description="Authentication not detected - may need user management",
                    icon="🔓",
                )
            )

        db_indicators = [
            "prisma",
            "mongoose",
            "pg",
            "mysql",
            "sqlite",
            "mongodb",
            "supabase",
            "firebase",
            "drizzle",
            "typeorm",
            "sequelize",
        ]
        has_db = any(ind in combined_content or ind in tech_names for ind in db_indicators)
        if not has_db:
            considerations.append(
                ProjectInsight(
                    type=InsightType.CONSIDERATION,
                    title="No Database Detected",
                    description="No database found - may be frontend-only or use external APIs",
                    icon="💾",
                )
            )

        deployment_files = [
            "dockerfile",
            "docker-compose",
            "vercel.json",
            "netlify.toml",
            "railway.json",
            "render.yaml",
            ".github/workflows",
            "serverless.yml",
            "fly.toml",
        ]
        has_deployment = any(f in combined_content for f in deployment_files)
        if not has_deployment:
            considerations.append(
                ProjectInsight(
                    type=InsightType.CONSIDERATION,
                    title="No Deployment Config",
                    description="No deployment config - manual deployment may be needed",
                    icon="🚀",
                )
            )

        return considerations
