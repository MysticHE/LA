import json
import re
from typing import Optional
from src.models.schemas import TechStackItem


class CodeAnalyzer:
    """Analyze code files to detect tech stack."""

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
        """Analyze file contents to detect tech stack."""
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
