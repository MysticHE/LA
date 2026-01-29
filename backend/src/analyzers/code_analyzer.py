import json
import logging
import re
from typing import Optional, TYPE_CHECKING

from src.models.schemas import TechStackItem

if TYPE_CHECKING:
    from src.services.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyze code files to detect tech stack.

    Supports AI-powered analysis with fallback to pattern matching.
    """

    # AI prompt for tech stack analysis
    TECH_STACK_PROMPT = """Analyze this project's technology stack from the configuration files.

Files:
{file_contents}

Primary language: {primary_language}

Return a JSON array of the most significant technologies used in this project:
[{{"name": "Technology Name", "category": "framework|library|database|tool|language"}}]

Categories:
- "framework": Web frameworks, backend frameworks (e.g., React, Django, Express)
- "library": Significant libraries (e.g., Tailwind CSS, Prisma, Pandas)
- "database": Databases (e.g., PostgreSQL, MongoDB, Redis)
- "tool": Build tools, testing tools (e.g., Webpack, Jest, Docker)
- "language": Programming languages (e.g., TypeScript, Python, Rust)

Focus on:
- Frameworks and major libraries that define the architecture
- Databases and data stores
- Build tools and testing frameworks
- Significant integrations (AI, payments, auth)

Return 5-15 most significant technologies. Return ONLY the JSON array, no explanation."""

    def __init__(self, ai_client: Optional["OpenAIClient"] = None):
        """Initialize the code analyzer.

        Args:
            ai_client: Optional AI client for enhanced analysis.
        """
        self.ai_client = ai_client

    FRAMEWORK_PATTERNS = {
        "package.json": {
            "react": ("React", "framework"),
            "next": ("Next.js", "framework"),
            "vue": ("Vue.js", "framework"),
            "nuxt": ("Nuxt.js", "framework"),
            "angular": ("Angular", "framework"),
            "svelte": ("Svelte", "framework"),
            "express": ("Express.js", "framework"),
            "fastify": ("Fastify", "framework"),
            "nest": ("NestJS", "framework"),
            "tailwindcss": ("Tailwind CSS", "library"),
            "typescript": ("TypeScript", "language"),
            "prisma": ("Prisma", "library"),
            "drizzle": ("Drizzle", "library"),
            "mongoose": ("MongoDB", "database"),
            "pg": ("PostgreSQL", "database"),
            "redis": ("Redis", "database"),
            "socket.io": ("Socket.io", "library"),
            "graphql": ("GraphQL", "library"),
            "trpc": ("tRPC", "library"),
            "jest": ("Jest", "tool"),
            "vitest": ("Vitest", "tool"),
            "playwright": ("Playwright", "tool"),
            "cypress": ("Cypress", "tool"),
            "docker": ("Docker", "tool"),
            "webpack": ("Webpack", "tool"),
            "vite": ("Vite", "tool"),
            "esbuild": ("esbuild", "tool"),
        },
        "requirements.txt": {
            "django": ("Django", "framework"),
            "flask": ("Flask", "framework"),
            "fastapi": ("FastAPI", "framework"),
            "sqlalchemy": ("SQLAlchemy", "library"),
            "pandas": ("Pandas", "library"),
            "numpy": ("NumPy", "library"),
            "tensorflow": ("TensorFlow", "library"),
            "pytorch": ("PyTorch", "library"),
            "scikit-learn": ("scikit-learn", "library"),
            "celery": ("Celery", "library"),
            "redis": ("Redis", "database"),
            "psycopg": ("PostgreSQL", "database"),
            "pymongo": ("MongoDB", "database"),
            "pytest": ("pytest", "tool"),
            "pydantic": ("Pydantic", "library"),
            "httpx": ("HTTPX", "library"),
            "requests": ("Requests", "library"),
            "beautifulsoup": ("BeautifulSoup", "library"),
            "scrapy": ("Scrapy", "framework"),
            "langchain": ("LangChain", "library"),
            "openai": ("OpenAI", "library"),
        },
        "pyproject.toml": {
            "django": ("Django", "framework"),
            "flask": ("Flask", "framework"),
            "fastapi": ("FastAPI", "framework"),
            "poetry": ("Poetry", "tool"),
            "black": ("Black", "tool"),
            "ruff": ("Ruff", "tool"),
            "mypy": ("mypy", "tool"),
        },
        "Cargo.toml": {
            "tokio": ("Tokio", "framework"),
            "actix": ("Actix", "framework"),
            "axum": ("Axum", "framework"),
            "rocket": ("Rocket", "framework"),
            "diesel": ("Diesel", "library"),
            "sqlx": ("SQLx", "library"),
            "serde": ("Serde", "library"),
        },
        "go.mod": {
            "gin": ("Gin", "framework"),
            "echo": ("Echo", "framework"),
            "fiber": ("Fiber", "framework"),
            "gorm": ("GORM", "library"),
        },
    }

    LANGUAGE_MAP = {
        "JavaScript": "JavaScript",
        "TypeScript": "TypeScript",
        "Python": "Python",
        "Rust": "Rust",
        "Go": "Go",
        "Java": "Java",
        "C#": "C#",
        "Ruby": "Ruby",
        "PHP": "PHP",
        "Swift": "Swift",
        "Kotlin": "Kotlin",
    }

    def analyze(
        self, file_contents: dict[str, str], primary_language: Optional[str]
    ) -> list[TechStackItem]:
        """Analyze file contents to detect tech stack.

        Uses AI analysis if available, falls back to pattern matching.
        """
        # Try AI analysis first if client is available
        if self.ai_client and file_contents:
            ai_result = self._analyze_with_ai(file_contents, primary_language)
            if ai_result:
                return ai_result

        # Fallback to pattern matching
        return self._analyze_with_patterns(file_contents, primary_language)

    def _analyze_with_ai(
        self, file_contents: dict[str, str], primary_language: Optional[str]
    ) -> Optional[list[TechStackItem]]:
        """Analyze tech stack using AI.

        Args:
            file_contents: Dictionary of filename to content.
            primary_language: Primary language of the repository.

        Returns:
            List of TechStackItem or None if AI analysis fails.
        """
        try:
            # Condense file contents (limit size for token efficiency)
            condensed = self._condense_file_contents(file_contents)

            prompt = self.TECH_STACK_PROMPT.format(
                file_contents=condensed,
                primary_language=primary_language or "Not specified",
            )

            result = self.ai_client.generate_content(
                system_prompt="You are a technical analyst identifying technology stacks. Return only valid JSON.",
                user_prompt=prompt,
            )

            if not result.success or not result.content:
                logger.debug("AI tech stack analysis failed: %s", result.error)
                return None

            # Parse JSON response
            tech_stack = self._parse_ai_response(result.content, primary_language)
            if tech_stack:
                logger.debug("AI tech stack analysis returned %d items", len(tech_stack))
                return tech_stack

            return None

        except Exception as e:
            logger.debug("AI tech stack analysis error: %s", str(e))
            return None

    def _condense_file_contents(self, file_contents: dict[str, str]) -> str:
        """Condense file contents for AI prompt (limit tokens)."""
        condensed_parts = []
        max_chars_per_file = 2000

        for filename, content in file_contents.items():
            if len(content) > max_chars_per_file:
                content = content[:max_chars_per_file] + "\n... (truncated)"
            condensed_parts.append(f"=== {filename} ===\n{content}")

        return "\n\n".join(condensed_parts)

    def _parse_ai_response(
        self, response: str, primary_language: Optional[str]
    ) -> Optional[list[TechStackItem]]:
        """Parse AI response into TechStackItem list."""
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

            tech_stack = []
            seen = set()
            valid_categories = {"framework", "library", "database", "tool", "language"}

            # Add primary language first
            if primary_language and primary_language in self.LANGUAGE_MAP:
                lang_name = self.LANGUAGE_MAP[primary_language]
                tech_stack.append(TechStackItem(name=lang_name, category="language"))
                seen.add(lang_name.lower())

            for item in data:
                if not isinstance(item, dict):
                    continue

                name = item.get("name", "").strip()
                category = item.get("category", "library").strip().lower()

                if not name or name.lower() in seen:
                    continue

                if category not in valid_categories:
                    category = "library"

                tech_stack.append(TechStackItem(name=name, category=category))
                seen.add(name.lower())

            return tech_stack if tech_stack else None

        except (json.JSONDecodeError, ValueError) as e:
            logger.debug("Failed to parse AI tech stack response: %s", str(e))
            return None

    def _analyze_with_patterns(
        self, file_contents: dict[str, str], primary_language: Optional[str]
    ) -> list[TechStackItem]:
        """Analyze tech stack using pattern matching (fallback)."""
        tech_stack = []
        seen = set()

        if primary_language and primary_language in self.LANGUAGE_MAP:
            lang_name = self.LANGUAGE_MAP[primary_language]
            tech_stack.append(TechStackItem(name=lang_name, category="language"))
            seen.add(lang_name.lower())

        for filename, content in file_contents.items():
            if filename not in self.FRAMEWORK_PATTERNS:
                continue

            patterns = self.FRAMEWORK_PATTERNS[filename]
            content_lower = content.lower()

            for pattern, (name, category) in patterns.items():
                if pattern in content_lower and name.lower() not in seen:
                    tech_stack.append(TechStackItem(name=name, category=category))
                    seen.add(name.lower())

        if "package.json" in file_contents:
            tech_stack = self._analyze_package_json(
                file_contents["package.json"], tech_stack, seen
            )

        return tech_stack

    def _analyze_package_json(
        self, content: str, tech_stack: list[TechStackItem], seen: set
    ) -> list[TechStackItem]:
        """Deep analyze package.json for more accurate detection."""
        try:
            pkg = json.loads(content)
            all_deps = {}
            all_deps.update(pkg.get("dependencies", {}))
            all_deps.update(pkg.get("devDependencies", {}))

            for dep in all_deps:
                dep_lower = dep.lower()
                for pattern, (name, category) in self.FRAMEWORK_PATTERNS[
                    "package.json"
                ].items():
                    if pattern in dep_lower and name.lower() not in seen:
                        tech_stack.append(TechStackItem(name=name, category=category))
                        seen.add(name.lower())

        except json.JSONDecodeError:
            pass

        return tech_stack
