"""LinkedIn post content analyzer.

Analyzes pasted LinkedIn post content to extract themes, tone, content type,
key points, entities, and hashtags for repurposing.
"""

import re
import json
from typing import Optional, Union
from src.models.linkedin_models import ContentAnalysisResult


# AI analysis prompt for structured content analysis
AI_ANALYSIS_SYSTEM_PROMPT = """You are an expert LinkedIn content analyst.
Analyze the provided LinkedIn post and extract structured information.

Return ONLY valid JSON with this exact structure (no markdown, no code blocks):
{
    "tone": "professional|casual|motivational|technical|humorous",
    "content_type": "story|tips|announcement|opinion|case-study",
    "themes": ["theme1", "theme2"],
    "key_points": ["point1", "point2", "point3"],
    "entities": ["entity1", "entity2"]
}

Guidelines:
- tone: The overall voice/mood of the post
- content_type: The primary format/structure of the content
- themes: Main topics discussed (max 5, e.g., "leadership", "AI/ML", "career growth")
- key_points: Core messages or takeaways (max 5, concise phrases)
- entities: Technologies, companies, or notable people mentioned (max 10)

Be precise and analytical. Return ONLY the JSON object."""


class LinkedInAnalyzer:
    """Analyzes LinkedIn post content for repurposing."""

    # Tone detection patterns
    TONE_PATTERNS = {
        "motivational": [
            r"\b(journey|growth|mindset|believe|inspire|achieve|success|lesson|learned)\b",
            r"(^|\n)[\u2728\U0001f4aa\U0001f680\u2b50\U0001f4a1]",
            r"\b(never give up|keep going|you can|don't stop)\b",
        ],
        "technical": [
            r"\b(api|sdk|framework|architecture|implementation|algorithm|optimization)\b",
            r"\b(performance|latency|throughput|scalable|microservice)\b",
            r"\b(code|function|class|method|deploy|ci\/cd)\b",
        ],
        "humorous": [
            r"\b(lol|haha|joke|funny|hilarious)\b",
            r"(^|\n)[\U0001f602\U0001f923\U0001f605\U0001f606]",
            r"\b(plot twist|spoiler alert|true story)\b",
        ],
        "casual": [
            r"\b(hey|btw|tbh|imho|gonna|wanna|kinda)\b",
            r"\b(cool|awesome|crazy|wild|insane)\b",
        ],
        "professional": [
            r"\b(strategy|leadership|stakeholder|roi|kpi|metric)\b",
            r"\b(announce|pleased|excited to share|thrilled)\b",
            r"\b(team|company|organization|business)\b",
        ],
    }

    # Content type detection patterns
    CONTENT_TYPE_PATTERNS = {
        "story": [
            r"\b(years ago|one day|remember when|let me tell you)\b",
            r"\b(happened|experience|learned|realized)\b",
            r"(^|\n)(i was|we were|it was)\b",
        ],
        "tips": [
            r"\b(\d+\s*(tips|ways|things|steps|mistakes|lessons))\b",
            r"(^|\n)(tip|pro tip|here's how|how to)\b",
            r"\b(avoid|instead|don't|always|never)\b",
        ],
        "announcement": [
            r"\b(announce|launch|release|introducing|now available)\b",
            r"\b(new|just|today|finally|excited to)\b",
            r"\b(check out|try|get started)\b",
        ],
        "opinion": [
            r"\b(i think|i believe|in my opinion|unpopular opinion)\b",
            r"\b(controversial|hot take|disagree|debate)\b",
            r"\b(should|shouldn't|need to|must)\b",
        ],
        "case-study": [
            r"\b(case study|results|outcome|impact|before.*after)\b",
            r"\b(increased|decreased|improved|saved|reduced)\b",
            r"\b(\d+%|\d+x|million|thousand)\b",
        ],
    }

    # Entity extraction patterns
    ENTITY_PATTERNS = {
        "companies": r"@(\w+)|(?:at\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|Co)\.?)?)",
        "technologies": r"\b(React|Vue|Angular|Node\.?js|Python|JavaScript|TypeScript|AWS|Azure|GCP|Docker|Kubernetes|AI|ML|GPT|Claude|OpenAI|LangChain|FastAPI|Django|Express|Next\.?js|Vercel|Supabase|Firebase|MongoDB|PostgreSQL|Redis)\b",
        "people": r"(?:(?:@|by\s+|with\s+|from\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?))",
    }

    def __init__(self, ai_client=None):
        """Initialize the analyzer.

        Args:
            ai_client: Optional AI client for enhanced analysis.
        """
        self.ai_client = ai_client

    def analyze_with_ai(self, content: str) -> Optional[ContentAnalysisResult]:
        """Analyze content using AI for more accurate results.

        Args:
            content: The LinkedIn post text to analyze.

        Returns:
            ContentAnalysisResult if AI analysis succeeds, None otherwise.
        """
        if not self.ai_client:
            return None

        try:
            result = self.ai_client.generate_content(
                system_prompt=AI_ANALYSIS_SYSTEM_PROMPT,
                user_prompt=f"Analyze this LinkedIn post:\n\n{content}",
                max_tokens=800,
            )

            if not result.success or not result.content:
                return None

            # Parse the JSON response
            response_text = result.content.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            ai_data = json.loads(response_text)

            # Extract hashtags using pattern matching (AI doesn't need to do this)
            hashtags = self._extract_hashtags(content)

            cleaned = self._clean_content(content)

            return ContentAnalysisResult(
                original_content=content,
                cleaned_content=cleaned,
                themes=ai_data.get("themes", [])[:5],
                tone=ai_data.get("tone", "professional"),
                content_type=ai_data.get("content_type", "opinion"),
                key_points=ai_data.get("key_points", [])[:5],
                entities=ai_data.get("entities", [])[:10],
                hashtags=hashtags,
            )

        except (json.JSONDecodeError, KeyError, TypeError):
            # Fall back to keyword-based analysis if AI response is invalid
            return None
        except Exception:
            return None

    def analyze(self, content: str, use_ai: bool = True) -> ContentAnalysisResult:
        """Analyze LinkedIn post content.

        Uses AI analysis when available, falls back to keyword-based analysis.

        Args:
            content: The LinkedIn post text to analyze.
            use_ai: Whether to attempt AI analysis first (default True).

        Returns:
            ContentAnalysisResult with extracted information.
        """
        # Try AI analysis first if enabled and client available
        if use_ai and self.ai_client:
            ai_result = self.analyze_with_ai(content)
            if ai_result:
                return ai_result

        # Fall back to keyword-based analysis
        cleaned = self._clean_content(content)

        return ContentAnalysisResult(
            original_content=content,
            cleaned_content=cleaned,
            themes=self._extract_themes(cleaned),
            tone=self._detect_tone(cleaned),
            content_type=self._detect_content_type(cleaned),
            key_points=self._extract_key_points(cleaned),
            entities=self._extract_entities(cleaned),
            hashtags=self._extract_hashtags(content),
        )

    def _clean_content(self, content: str) -> str:
        """Clean and normalize the content."""
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', content)
        # Remove excessive newlines
        cleaned = re.sub(r'\n{3,}', '\n\n', content)
        # Strip leading/trailing whitespace
        cleaned = cleaned.strip()
        return cleaned

    def _detect_tone(self, content: str) -> str:
        """Detect the overall tone of the content."""
        content_lower = content.lower()
        scores = {}

        for tone, patterns in self.TONE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                score += len(matches)
            scores[tone] = score

        # Return tone with highest score, default to professional
        if max(scores.values()) == 0:
            return "professional"
        return max(scores, key=scores.get)

    def _detect_content_type(self, content: str) -> str:
        """Detect the type of content."""
        content_lower = content.lower()
        scores = {}

        for content_type, patterns in self.CONTENT_TYPE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, content_lower, re.IGNORECASE)
                score += len(matches)
            scores[content_type] = score

        # Return type with highest score, default to opinion
        if max(scores.values()) == 0:
            return "opinion"
        return max(scores, key=scores.get)

    def _extract_themes(self, content: str) -> list[str]:
        """Extract main themes/topics from content."""
        themes = []
        content_lower = content.lower()

        # Theme keywords
        theme_keywords = {
            "career growth": ["career", "promotion", "job", "interview", "hiring"],
            "leadership": ["leader", "manage", "team", "culture", "leadership"],
            "technology": ["tech", "software", "code", "developer", "engineering"],
            "startup": ["startup", "founder", "venture", "entrepreneur", "funding"],
            "productivity": ["productivity", "efficiency", "workflow", "time management"],
            "AI/ML": ["ai", "machine learning", "gpt", "llm", "artificial intelligence"],
            "remote work": ["remote", "wfh", "hybrid", "distributed team"],
            "learning": ["learn", "course", "tutorial", "education", "skill"],
        }

        for theme, keywords in theme_keywords.items():
            if any(kw in content_lower for kw in keywords):
                themes.append(theme)

        return themes[:5]

    def _extract_key_points(self, content: str) -> list[str]:
        """Extract key points/takeaways from content."""
        key_points = []

        # Split by common separators
        lines = re.split(r'\n+|\.\s+', content)

        for line in lines:
            line = line.strip()
            # Skip very short or very long lines
            if len(line) < 20 or len(line) > 200:
                continue
            # Look for lines that start with numbers, bullets, or key phrases
            if re.match(r'^(\d+[\.\):]|\u2022|\u2013|\-|•)', line):
                key_points.append(re.sub(r'^(\d+[\.\):]|\u2022|\u2013|\-|•)\s*', '', line))
            elif any(line.lower().startswith(phrase) for phrase in
                     ["the key", "lesson", "takeaway", "important", "remember"]):
                key_points.append(line)

        # If no structured points found, take first few meaningful sentences
        if not key_points:
            sentences = re.split(r'[.!?]+', content)
            for sentence in sentences[1:4]:  # Skip first (usually hook)
                sentence = sentence.strip()
                if 30 < len(sentence) < 200:
                    key_points.append(sentence)

        return key_points[:5]

    def _extract_entities(self, content: str) -> list[str]:
        """Extract mentioned entities (companies, people, technologies)."""
        entities = set()

        # Extract technologies
        tech_matches = re.findall(self.ENTITY_PATTERNS["technologies"], content, re.IGNORECASE)
        entities.update(tech_matches)

        # Extract @mentions
        mention_matches = re.findall(r'@(\w+)', content)
        entities.update(mention_matches)

        return list(entities)[:10]

    def _extract_hashtags(self, content: str) -> list[str]:
        """Extract hashtags from content."""
        hashtags = re.findall(r'#(\w+)', content)
        return list(set(hashtags))[:10]


async def analyze_linkedin_content(
    content: str,
    ai_client=None
) -> ContentAnalysisResult:
    """Convenience function for analyzing LinkedIn content.

    Args:
        content: The LinkedIn post text.
        ai_client: Optional AI client for enhanced analysis.

    Returns:
        ContentAnalysisResult with analysis data.
    """
    analyzer = LinkedInAnalyzer(ai_client=ai_client)
    return analyzer.analyze(content)
