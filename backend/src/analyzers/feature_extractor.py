import re
from typing import Optional
from src.models.schemas import Feature


class FeatureExtractor:
    """Extract key features from repository content."""

    FEATURE_PATTERNS = {
        "authentication": {
            "patterns": [
                r"auth",
                r"login",
                r"signup",
                r"jwt",
                r"oauth",
                r"session",
                r"passport",
            ],
            "name": "Authentication",
            "description": "User authentication and authorization system",
        },
        "api": {
            "patterns": [r"api", r"rest", r"graphql", r"endpoint", r"route"],
            "name": "API",
            "description": "RESTful or GraphQL API endpoints",
        },
        "database": {
            "patterns": [
                r"database",
                r"mongodb",
                r"postgres",
                r"mysql",
                r"sqlite",
                r"prisma",
                r"orm",
                r"model",
            ],
            "name": "Database Integration",
            "description": "Data persistence and database operations",
        },
        "realtime": {
            "patterns": [r"websocket", r"socket\.io", r"realtime", r"live"],
            "name": "Real-time Features",
            "description": "Real-time updates and WebSocket communication",
        },
        "testing": {
            "patterns": [r"test", r"spec", r"jest", r"pytest", r"vitest", r"cypress"],
            "name": "Testing Suite",
            "description": "Automated testing and quality assurance",
        },
        "ci_cd": {
            "patterns": [
                r"github.actions",
                r"\.github/workflows",
                r"ci",
                r"deploy",
                r"docker",
            ],
            "name": "CI/CD Pipeline",
            "description": "Continuous integration and deployment automation",
        },
        "caching": {
            "patterns": [r"cache", r"redis", r"memcache"],
            "name": "Caching",
            "description": "Performance optimization with caching layer",
        },
        "file_upload": {
            "patterns": [r"upload", r"multer", r"s3", r"storage", r"blob"],
            "name": "File Upload",
            "description": "File upload and storage handling",
        },
        "email": {
            "patterns": [r"email", r"mail", r"smtp", r"sendgrid", r"nodemailer"],
            "name": "Email Service",
            "description": "Email sending and notification system",
        },
        "payment": {
            "patterns": [r"stripe", r"payment", r"checkout", r"billing"],
            "name": "Payment Processing",
            "description": "Payment integration and billing system",
        },
        "search": {
            "patterns": [r"search", r"elasticsearch", r"algolia", r"meilisearch"],
            "name": "Search Functionality",
            "description": "Full-text search and filtering capabilities",
        },
        "analytics": {
            "patterns": [r"analytics", r"tracking", r"metrics", r"dashboard"],
            "name": "Analytics",
            "description": "Usage tracking and analytics dashboard",
        },
        "i18n": {
            "patterns": [r"i18n", r"localization", r"translation", r"locale"],
            "name": "Internationalization",
            "description": "Multi-language support and localization",
        },
        "ai_ml": {
            "patterns": [
                r"openai",
                r"llm",
                r"machine.learning",
                r"tensorflow",
                r"pytorch",
                r"langchain",
            ],
            "name": "AI/ML Integration",
            "description": "Artificial intelligence and machine learning features",
        },
    }

    def extract(
        self,
        readme: Optional[str],
        file_contents: dict[str, str],
        file_structure: list[str],
    ) -> list[Feature]:
        """Extract features from repository content."""
        features = []
        detected = set()

        search_text = " ".join(
            [
                readme or "",
                " ".join(file_contents.values()),
                " ".join(file_structure),
            ]
        ).lower()

        for feature_id, config in self.FEATURE_PATTERNS.items():
            if feature_id in detected:
                continue

            for pattern in config["patterns"]:
                if re.search(pattern, search_text, re.IGNORECASE):
                    features.append(
                        Feature(name=config["name"], description=config["description"])
                    )
                    detected.add(feature_id)
                    break

        if readme:
            readme_features = self._extract_from_readme(readme, detected)
            features.extend(readme_features)

        return features[:10]

    def _extract_from_readme(self, readme: str, detected: set) -> list[Feature]:
        """Extract additional features from README structure."""
        features = []

        section_patterns = [
            (r"##?\s*features?\s*\n([\s\S]*?)(?=\n##|\Z)", "feature_list"),
            (r"##?\s*what.+does\s*\n([\s\S]*?)(?=\n##|\Z)", "what_it_does"),
            (r"##?\s*highlights?\s*\n([\s\S]*?)(?=\n##|\Z)", "highlights"),
        ]

        for pattern, section_type in section_patterns:
            match = re.search(pattern, readme, re.IGNORECASE)
            if match:
                section_content = match.group(1)
                bullet_items = re.findall(r"[-*]\s*(.+)", section_content)
                for item in bullet_items[:5]:
                    item_clean = re.sub(r"[*_`\[\]]", "", item).strip()
                    if (
                        len(item_clean) > 10
                        and item_clean.lower() not in detected
                        and len(item_clean) < 100
                    ):
                        features.append(
                            Feature(
                                name=item_clean[:50],
                                description=f"From README: {item_clean}",
                            )
                        )
                        detected.add(item_clean.lower())

        return features[:5]
