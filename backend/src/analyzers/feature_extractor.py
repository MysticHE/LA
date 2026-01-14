import re
import json
import logging
from typing import Optional, TYPE_CHECKING

from src.models.schemas import Feature

if TYPE_CHECKING:
    from src.services.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract key features from repository content.

    Prioritizes unique project-specific features from README over generic categories.
    """

    # Generic categories as fallback only
    FALLBACK_PATTERNS = {
        "authentication": {
            "patterns": [r"\bauth\b", r"\blogin\b", r"\bjwt\b", r"\boauth"],
            "name": "Authentication",
        },
        "realtime": {
            "patterns": [r"websocket", r"socket\.io", r"real-?time"],
            "name": "Real-time Updates",
        },
        "ai_ml": {
            "patterns": [r"openai", r"\bllm\b", r"langchain", r"gpt", r"\bai\b"],
            "name": "AI Integration",
        },
        "payment": {
            "patterns": [r"stripe", r"payment", r"billing"],
            "name": "Payment Processing",
        },
    }

    def extract(
        self,
        readme: Optional[str],
        file_contents: dict[str, str],
        file_structure: list[str],
        openai_client: Optional["OpenAIClient"] = None,
        repo_description: str = "",
    ) -> list[Feature]:
        """Extract features prioritizing AI extraction when available."""
        features = []
        seen_names = set()

        # 1. First priority: AI extraction (if client available)
        if readme and openai_client:
            ai_features = self._extract_with_ai(readme, openai_client, repo_description)
            for f in ai_features:
                name_lower = f.name.lower()
                if name_lower not in seen_names:
                    features.append(f)
                    seen_names.add(name_lower)

        # 2. Fall back to regex if AI returned < 3 features
        if len(features) < 3 and readme:
            readme_features = self._extract_unique_from_readme(readme)
            for f in readme_features:
                name_lower = f.name.lower()
                if name_lower not in seen_names:
                    features.append(f)
                    seen_names.add(name_lower)

        # 3. Extract from project description if still < 5 features
        if readme and len(features) < 5:
            desc_features = self._extract_from_description(readme)
            for f in desc_features:
                name_lower = f.name.lower()
                if name_lower not in seen_names:
                    features.append(f)
                    seen_names.add(name_lower)

        # 4. Fallback: Only add generic categories if we have < 3 features
        if len(features) < 3:
            search_text = " ".join([
                readme or "",
                " ".join(file_contents.values()),
            ]).lower()

            fallback_features = self._detect_fallback_features(search_text, seen_names)
            features.extend(fallback_features)

        return features[:7]

    def _extract_with_ai(
        self,
        readme: str,
        openai_client: "OpenAIClient",
        repo_description: str = "",
    ) -> list[Feature]:
        """Use AI to extract key features from README content."""
        prompt = f"""Extract 3-7 key features from this project README.

Rules:
- Focus on what makes this project unique and useful
- Use concise feature names (2-5 words each)
- Skip generic features like "API", "Database", "Testing", "CI/CD"
- Extract actual capabilities, not section headers
- Each feature should describe a distinct capability

README:
{readme[:4000]}

{f"Project description: {repo_description}" if repo_description else ""}

Return ONLY a JSON array in this exact format:
[{{"name": "Feature Name", "description": "Brief description of the feature"}}]"""

        try:
            result = openai_client.generate_content(
                system_prompt="You extract project features from README files. Return only valid JSON array, no markdown.",
                user_prompt=prompt,
                model="gpt-4o-mini",
                max_tokens=500,
            )

            if result.success and result.content:
                return self._parse_ai_features(result.content)
        except Exception as e:
            logger.warning(f"AI feature extraction failed: {e}")

        return []

    def _parse_ai_features(self, content: str) -> list[Feature]:
        """Parse AI-generated JSON into Feature objects."""
        try:
            content = content.strip()
            if content.startswith("```"):
                content = re.sub(r"```(?:json)?\s*", "", content)
                content = content.rstrip("`")

            features_data = json.loads(content)

            if not isinstance(features_data, list):
                return []

            features = []
            for item in features_data[:7]:
                if isinstance(item, dict) and "name" in item:
                    name = str(item["name"]).strip()[:50]
                    desc = str(item.get("description", name)).strip()[:100]
                    if name and len(name) >= 3:
                        features.append(Feature(name=name, description=desc))

            return features
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse AI features: {e}")
            return []

    def _extract_unique_from_readme(self, readme: str) -> list[Feature]:
        """Extract actual feature descriptions from README sections."""
        features = []

        # Patterns to find feature sections
        section_patterns = [
            r"##?\s*(?:key\s+)?features?\s*\n([\s\S]*?)(?=\n##|\n---|\Z)",
            r"##?\s*what.+does\s*\n([\s\S]*?)(?=\n##|\n---|\Z)",
            r"##?\s*highlights?\s*\n([\s\S]*?)(?=\n##|\n---|\Z)",
            r"##?\s*capabilities\s*\n([\s\S]*?)(?=\n##|\n---|\Z)",
            r"##?\s*why\s+.+\?\s*\n([\s\S]*?)(?=\n##|\n---|\Z)",
        ]

        for pattern in section_patterns:
            match = re.search(pattern, readme, re.IGNORECASE)
            if match:
                section = match.group(1)
                items = self._parse_feature_items(section)
                features.extend(items)
                if len(features) >= 5:
                    break

        return features[:7]

    def _parse_feature_items(self, section: str) -> list[Feature]:
        """Parse bullet points and extract clean feature names."""
        features = []

        # Match bullet points (-, *, •) or numbered items
        bullet_pattern = r"(?:^|\n)\s*(?:[-*•]|\d+\.)\s*\*{0,2}([^*\n]+)"
        items = re.findall(bullet_pattern, section)

        for item in items:
            # Clean markdown formatting
            clean = re.sub(r"[`\[\]()]", "", item).strip()
            clean = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", clean)  # Remove bold/italic

            # Skip if too short, too long, or looks like a link/code
            if len(clean) < 5 or len(clean) > 80:
                continue
            if clean.startswith("http") or clean.startswith("/"):
                continue
            if clean.lower() in ["features", "installation", "usage", "license"]:
                continue

            # Extract name (before colon or dash if present)
            if ":" in clean:
                name = clean.split(":")[0].strip()
                desc = clean.split(":", 1)[1].strip() if ":" in clean else ""
            elif " - " in clean:
                name = clean.split(" - ")[0].strip()
                desc = clean.split(" - ", 1)[1].strip()
            else:
                name = clean
                desc = ""

            # Capitalize first letter
            name = name[0].upper() + name[1:] if name else name

            # Skip generic/boring names
            generic = ["api", "database", "testing", "ci/cd", "documentation"]
            if name.lower() in generic:
                continue

            features.append(Feature(
                name=name[:50],
                description=desc[:100] if desc else name
            ))

        return features

    def _extract_from_description(self, readme: str) -> list[Feature]:
        """Extract key capabilities from the project description."""
        features = []

        # Get first paragraph (usually the main description)
        lines = readme.strip().split("\n")
        desc_lines = []

        for line in lines:
            line = line.strip()
            # Skip headers and badges
            if line.startswith("#") or line.startswith("!") or line.startswith("["):
                continue
            if not line:
                if desc_lines:
                    break
                continue
            desc_lines.append(line)
            if len(desc_lines) >= 3:
                break

        description = " ".join(desc_lines)

        # Look for key action verbs that describe what the project does
        action_patterns = [
            (r"(?:that\s+|to\s+|for\s+)(\w+(?:ing|s|es)\s+\w+(?:\s+\w+)?)", "verb_phrase"),
            (r"(?:enables?|allows?|provides?|supports?)\s+(\w+(?:\s+\w+){1,3})", "capability"),
            (r"(?:automatically|seamlessly)\s+(\w+s?\s+\w+(?:\s+\w+)?)", "auto_feature"),
        ]

        for pattern, _ in action_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches[:2]:
                clean = match.strip()
                if len(clean) > 5 and len(clean) < 40:
                    name = clean[0].upper() + clean[1:]
                    features.append(Feature(name=name, description=f"Core capability"))

        return features[:3]

    def _detect_fallback_features(self, search_text: str, seen: set) -> list[Feature]:
        """Detect generic features as fallback only."""
        features = []

        for feature_id, config in self.FALLBACK_PATTERNS.items():
            if config["name"].lower() in seen:
                continue

            for pattern in config["patterns"]:
                if re.search(pattern, search_text, re.IGNORECASE):
                    features.append(Feature(
                        name=config["name"],
                        description=config["name"]
                    ))
                    seen.add(config["name"].lower())
                    break

        return features[:3]
