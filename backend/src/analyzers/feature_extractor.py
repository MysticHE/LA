import re
from typing import Optional
from src.models.schemas import Feature


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
    ) -> list[Feature]:
        """Extract features prioritizing unique project-specific ones."""
        features = []
        seen_names = set()

        # 1. First priority: Extract unique features from README
        if readme:
            readme_features = self._extract_unique_from_readme(readme)
            for f in readme_features:
                name_lower = f.name.lower()
                if name_lower not in seen_names:
                    features.append(f)
                    seen_names.add(name_lower)

        # 2. Second priority: Extract from project description (first paragraph)
        if readme and len(features) < 5:
            desc_features = self._extract_from_description(readme)
            for f in desc_features:
                name_lower = f.name.lower()
                if name_lower not in seen_names:
                    features.append(f)
                    seen_names.add(name_lower)

        # 3. Fallback: Only add generic categories if we have < 3 features
        if len(features) < 3:
            search_text = " ".join([
                readme or "",
                " ".join(file_contents.values()),
            ]).lower()

            fallback_features = self._detect_fallback_features(search_text, seen_names)
            features.extend(fallback_features)

        return features[:7]

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
