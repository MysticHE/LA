"""Content classifier for LinkedIn posts."""

import re
from typing import Optional
from src.models.image_schemas import ContentAnalysis, ContentType, ClassificationResult


class ContentClassifier:
    """Classify LinkedIn post content into content types."""

    # Pattern weights for each content type
    # Higher weight = stronger signal for that content type
    CONTENT_TYPE_PATTERNS = {
        ContentType.TUTORIAL: {
            'patterns': [
                (r'\bhow\s+to\b', 3),
                (r'\bstep[\s-]by[\s-]step\b', 3),
                (r'\btutorial\b', 4),
                (r'\bguide\b', 2),
                (r'\blearn\s+how\b', 3),
                (r'\blet\s+me\s+show\s+you\b', 2),
                (r'\bhere\'?s\s+how\b', 3),
                (r'\bwalkthrough\b', 3),
                (r'\bexplained\b', 2),
                (r'\bintroduction\s+to\b', 2),
                (r'\bgetting\s+started\b', 2),
                (r'\bfor\s+beginners?\b', 2),
                (r'\bstep\s+\d+\b', 2),
                (r'\bfirst[,\s]+.*second[,\s]+.*third\b', 2),
                (r'\b1\.\s+.*2\.\s+.*3\.\b', 2),
            ],
            'base_score': 0,
        },
        ContentType.ANNOUNCEMENT: {
            'patterns': [
                (r'\bannouncing\b', 4),
                (r'\bexcited\s+to\s+announce\b', 4),
                (r'\bwe\'?re\s+launching\b', 3),
                (r'\bjust\s+launched\b', 3),
                (r'\bnew\s+release\b', 3),
                (r'\bintroducing\b', 3),
                (r'\bcoming\s+soon\b', 2),
                (r'\bnow\s+available\b', 3),
                (r'\bofficial(?:ly)?\b', 2),
                (r'\bwe\'?ve\s+released\b', 3),
                (r'\bjust\s+shipped\b', 3),
                (r'\bbig\s+news\b', 3),
                (r'\bexciting\s+news\b', 2),
                (r'\bproud\s+to\s+share\b', 2),
                (r'\bcheck\s+it\s+out\b', 1),
            ],
            'base_score': 0,
        },
        ContentType.TIPS: {
            'patterns': [
                (r'\btips?\b', 3),
                (r'\btricks?\b', 2),
                (r'\bhacks?\b', 2),
                (r'\bbest\s+practices?\b', 3),
                (r'\bpro\s+tip\b', 4),
                (r'\bquick\s+tip\b', 4),
                (r'\bhere\s+are\s+\d+\b', 2),
                (r'\bthings?\s+(?:i|you)\s+(?:wish|learned)\b', 2),
                (r'\blessons?\s+learned\b', 2),
                (r'\badvice\b', 2),
                (r'\bdo\'?s?\s+and\s+don\'?ts?\b', 3),
                (r'\bavoid\s+(?:these|this)\b', 2),
                (r'\bmistakes?\s+to\s+avoid\b', 3),
                (r'\bshortcuts?\b', 2),
                (r'\bsecrets?\b', 2),
            ],
            'base_score': 0,
        },
        ContentType.STORY: {
            'patterns': [
                (r'\bmy\s+journey\b', 3),
                (r'\bmy\s+story\b', 4),
                (r'\bpersonal\s+experience\b', 3),
                (r'\bi\s+remember\b', 2),
                (r'\byears?\s+ago\b', 2),
                (r'\bwhen\s+i\s+started\b', 3),
                (r'\blooking\s+back\b', 2),
                (r'\blessons?\s+from\b', 2),
                (r'\bfailed\b', 2),
                (r'\bstruggled?\b', 2),
                (r'\bovercome\b', 2),
                (r'\btransformed\b', 2),
                (r'\bchanged\s+my\s+life\b', 3),
                (r'\breflecting\s+on\b', 2),
                (r'\bfrom\s+.*to\s+', 2),
            ],
            'base_score': 0,
        },
        ContentType.TECHNICAL: {
            'patterns': [
                (r'\barchitecture\b', 3),
                (r'\bimplementation\b', 2),
                (r'\balgorithm\b', 3),
                (r'\bperformance\b', 2),
                (r'\boptimization\b', 3),
                (r'\bscalability\b', 3),
                (r'\bbenchmark\b', 3),
                (r'\bdeep\s+dive\b', 3),
                (r'\bunder\s+the\s+hood\b', 3),
                (r'\btechnical\s+debt\b', 3),
                (r'\bcode\s+review\b', 2),
                (r'\brefactoring\b', 3),
                (r'\bdesign\s+pattern\b', 3),
                (r'\bmicroservices?\b', 2),
                (r'\bapi\s+design\b', 2),
                (r'\bsystem\s+design\b', 3),
            ],
            'base_score': 0,
        },
        ContentType.CAREER: {
            'patterns': [
                (r'\bjob\s+search\b', 3),
                (r'\bcareer\b', 3),
                (r'\binterview\b', 3),
                (r'\bhiring\b', 3),
                (r'\brecruiting\b', 2),
                (r'\bresume\b', 3),
                (r'\bcv\b', 2),
                (r'\bsalary\b', 3),
                (r'\bpromotion\b', 3),
                (r'\bwe\'?re\s+hiring\b', 4),
                (r'\bjob\s+offer\b', 3),
                (r'\bnew\s+role\b', 2),
                (r'\bjoined\b', 2),
                (r'\bleft\s+(?:my\s+)?job\b', 2),
                (r'\bopen\s+(?:to\s+)?(?:new\s+)?opportunities?\b', 3),
                (r'\blayoffs?\b', 2),
            ],
            'base_score': 0,
        },
    }

    # Additional signals from ContentAnalysis
    THEME_TYPE_MAPPING = {
        'learning': ContentType.TUTORIAL,
        'career': ContentType.CAREER,
        'testing': ContentType.TECHNICAL,
        'performance': ContentType.TECHNICAL,
        'devops': ContentType.TECHNICAL,
        'security': ContentType.TECHNICAL,
        'API development': ContentType.TECHNICAL,
        'databases': ContentType.TECHNICAL,
    }

    def classify(
        self,
        analysis: ContentAnalysis,
        original_text: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify content based on ContentAnalysis.

        Args:
            analysis: ContentAnalysis object from ContentAnalyzer
            original_text: Optional original text for better pattern matching

        Returns:
            ClassificationResult with content_type and confidence score
        """
        # Build combined content from analysis for pattern matching
        content_parts = [
            ' '.join(analysis.themes),
            ' '.join(analysis.keywords),
            ' '.join(analysis.suggested_visual_elements),
        ]

        # If original text is provided, use it for pattern matching
        if original_text:
            content_parts.append(original_text)

        content = ' '.join(content_parts).lower()

        # Calculate scores for each content type
        scores: dict[ContentType, float] = {}

        for content_type, config in self.CONTENT_TYPE_PATTERNS.items():
            score = config['base_score']

            for pattern, weight in config['patterns']:
                if re.search(pattern, content, re.IGNORECASE):
                    score += weight

            # Add theme-based signals
            for theme in analysis.themes:
                if theme.lower() in self.THEME_TYPE_MAPPING:
                    if self.THEME_TYPE_MAPPING[theme.lower()] == content_type:
                        score += 2

            scores[content_type] = score

        # Find the content type with highest score
        max_score = max(scores.values())
        best_type = max(scores.keys(), key=lambda k: scores[k])

        # Calculate confidence based on score and difference from other scores
        if max_score == 0:
            # No patterns matched, default to TECHNICAL with low confidence
            return ClassificationResult(
                content_type=ContentType.TECHNICAL,
                confidence=0.3
            )

        # Calculate confidence
        # Higher score and bigger gap = higher confidence
        total_score = sum(scores.values())
        if total_score > 0:
            score_ratio = max_score / total_score
        else:
            score_ratio = 0

        # Scale confidence: min 0.4, max 0.95
        # score_ratio of 0.5+ indicates a dominant type
        confidence = min(0.95, max(0.4, 0.4 + (score_ratio * 0.7)))

        # If score is high (many patterns matched), boost confidence
        if max_score >= 10:
            confidence = min(0.95, confidence + 0.15)
        elif max_score >= 6:
            confidence = min(0.95, confidence + 0.1)
        elif max_score >= 4:
            confidence = min(0.95, confidence + 0.05)

        return ClassificationResult(
            content_type=best_type,
            confidence=round(confidence, 2)
        )

    def classify_from_text(self, text: str) -> ClassificationResult:
        """
        Classify content directly from text using pattern matching.

        This method can be used when ContentAnalysis is not available.

        Args:
            text: The post text to classify

        Returns:
            ClassificationResult with content_type and confidence score
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty or None.")

        content = text.lower()

        # Calculate scores for each content type
        scores: dict[ContentType, float] = {}

        for content_type, config in self.CONTENT_TYPE_PATTERNS.items():
            score = config['base_score']

            for pattern, weight in config['patterns']:
                if re.search(pattern, content, re.IGNORECASE):
                    score += weight

            scores[content_type] = score

        # Find the content type with highest score
        max_score = max(scores.values())
        best_type = max(scores.keys(), key=lambda k: scores[k])

        # Calculate confidence based on score and difference from other scores
        if max_score == 0:
            # No patterns matched, default to TECHNICAL with low confidence
            return ClassificationResult(
                content_type=ContentType.TECHNICAL,
                confidence=0.3
            )

        # Calculate confidence
        total_score = sum(scores.values())
        if total_score > 0:
            score_ratio = max_score / total_score
        else:
            score_ratio = 0

        # Scale confidence: min 0.4, max 0.95
        confidence = min(0.95, max(0.4, 0.4 + (score_ratio * 0.7)))

        # If score is high (many patterns matched), boost confidence
        if max_score >= 10:
            confidence = min(0.95, confidence + 0.15)
        elif max_score >= 6:
            confidence = min(0.95, confidence + 0.1)
        elif max_score >= 4:
            confidence = min(0.95, confidence + 0.05)

        return ClassificationResult(
            content_type=best_type,
            confidence=round(confidence, 2)
        )
