"""Analyzer for generating reader-friendly project insights."""

from typing import Optional
from src.models.schemas import ProjectInsight, InsightType, TechStackItem


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
    """Analyzes project to generate reader-friendly insights."""

    def analyze(
        self,
        tech_stack: list[TechStackItem],
        file_contents: dict[str, str],
        file_structure: list[str],
        primary_language: Optional[str] = None,
    ) -> list[ProjectInsight]:
        """Analyze project and return insights."""
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
