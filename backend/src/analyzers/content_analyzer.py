"""Content analyzer for LinkedIn posts."""

import re
from typing import Optional
from src.models.image_schemas import ContentAnalysis, Sentiment


class ContentAnalyzer:
    """Analyze LinkedIn post content to extract themes, technologies, and sentiment."""

    # Technology patterns to detect
    TECHNOLOGY_PATTERNS = {
        # Programming Languages
        r'\bpython\b': 'Python',
        r'\bjavascript\b': 'JavaScript',
        r'\btypescript\b': 'TypeScript',
        r'\bjava\b': 'Java',
        r'\bc\+\+\b': 'C++',
        r'c#': 'C#',  # C# needs special handling (# is not a word boundary)
        r'\bruby\b': 'Ruby',
        r'\bgo\b(?!\s+to)': 'Go',  # Avoid matching "go to"
        r'\bgolang\b': 'Go',
        r'\brust\b': 'Rust',
        r'\bswift\b': 'Swift',
        r'\bkotlin\b': 'Kotlin',
        r'\bphp\b': 'PHP',
        r'\bscala\b': 'Scala',
        r'\br\s+programming\b|\br\s+language\b|\brlang\b': 'R',

        # Frameworks
        r'\breact\b': 'React',
        r'\bvue\.?js?\b': 'Vue.js',
        r'\bangular\b': 'Angular',
        r'\bsvelte\b': 'Svelte',
        r'\bnext\.?js\b': 'Next.js',
        r'\bnuxt\b': 'Nuxt.js',
        r'\bdjango\b': 'Django',
        r'\bflask\b': 'Flask',
        r'\bfastapi\b': 'FastAPI',
        r'\bexpress\b': 'Express.js',
        r'\bnestjs\b': 'NestJS',
        r'\bspring\b(?!\s+boot)': 'Spring',
        r'\bspring\s+boot\b': 'Spring Boot',
        r'\brails\b': 'Ruby on Rails',
        r'\bruby\s+on\s+rails\b': 'Ruby on Rails',
        r'\blaravel\b': 'Laravel',
        r'\.net\b': '.NET',
        r'\bdotnet\b': '.NET',

        # Databases
        r'\bpostgres(?:ql)?\b': 'PostgreSQL',
        r'\bmysql\b': 'MySQL',
        r'\bmongodb\b': 'MongoDB',
        r'\bredis\b': 'Redis',
        r'\belasticsearch\b': 'Elasticsearch',
        r'\bdynamodb\b': 'DynamoDB',
        r'\bsqlite\b': 'SQLite',

        # Cloud & DevOps
        r'\baws\b': 'AWS',
        r'\bamazon\s+web\s+services\b': 'AWS',
        r'\bazure\b': 'Azure',
        r'\bgcp\b': 'Google Cloud',
        r'\bgoogle\s+cloud\b': 'Google Cloud',
        r'\bdocker\b': 'Docker',
        r'\bkubernetes\b': 'Kubernetes',
        r'\bk8s\b': 'Kubernetes',
        r'\bterraform\b': 'Terraform',
        r'\bansible\b': 'Ansible',
        r'\bjenkins\b': 'Jenkins',
        r'\bgithub\s+actions\b': 'GitHub Actions',
        r'\bci/cd\b': 'CI/CD',

        # AI/ML
        r'\btensorflow\b': 'TensorFlow',
        r'\bpytorch\b': 'PyTorch',
        r'\bscikit[-\s]?learn\b': 'scikit-learn',
        r'\bkeras\b': 'Keras',
        r'\bopenai\b': 'OpenAI',
        r'\bchatgpt\b': 'ChatGPT',
        r'\bgpt[-\s]?[34]\b': 'GPT',
        r'\bllm\b': 'LLM',
        r'\bllms\b': 'LLMs',
        r'\blangchain\b': 'LangChain',
        r'\bhugging\s*face\b': 'Hugging Face',

        # Other Tools
        r'\bgit\b(?!hub)': 'Git',
        r'\bgithub\b': 'GitHub',
        r'\bgitlab\b': 'GitLab',
        r'\bjira\b': 'Jira',
        r'\bconfluence\b': 'Confluence',
        r'\bfigma\b': 'Figma',
        r'\bnotion\b': 'Notion',
        r'\bslack\b': 'Slack',
        r'\bvscode\b': 'VS Code',
        r'\bvisual\s+studio\s+code\b': 'VS Code',
    }

    # Theme patterns
    THEME_PATTERNS = {
        r'\b(?:machine\s+learning|ml|deep\s+learning|ai|artificial\s+intelligence)\b': 'machine learning',
        r'\b(?:web\s+development|webdev|frontend|backend|full[\s-]?stack)\b': 'web development',
        r'\b(?:mobile\s+development|ios|android|react\s+native|flutter)\b': 'mobile development',
        r'\b(?:devops|infrastructure|deployment|scaling)\b': 'devops',
        r'\b(?:data\s+science|data\s+analysis|analytics|data\s+engineering)\b': 'data science',
        r'\b(?:cloud\s+computing|serverless|microservices)\b': 'cloud computing',
        r'\b(?:security|cybersecurity|infosec|authentication|authorization)\b': 'security',
        r'\b(?:api|rest|graphql|grpc)\b': 'API development',
        r'\b(?:testing|test[-\s]driven|tdd|unit\s+test|integration\s+test)\b': 'testing',
        r'\b(?:performance|optimization|caching|speed)\b': 'performance',
        r'\b(?:career|job|interview|hiring|tech\s+industry)\b': 'career',
        r'\b(?:open[\s-]?source|oss|contributing|community)\b': 'open source',
        r'\b(?:startup|entrepreneurship|product|saas)\b': 'startup',
        r'\b(?:learning|tutorial|course|education|bootcamp)\b': 'learning',
        r'\b(?:automation|workflow|productivity)\b': 'automation',
        r'\b(?:database|sql|nosql|data\s+modeling)\b': 'databases',
        r'\b(?:blockchain|web3|crypto|smart\s+contracts)\b': 'blockchain',
    }

    # Sentiment indicators
    POSITIVE_WORDS = {
        'excited', 'amazing', 'love', 'great', 'awesome', 'fantastic',
        'wonderful', 'excellent', 'brilliant', 'thrilled', 'proud',
        'happy', 'success', 'achievement', 'breakthrough', 'innovative',
        'game-changer', 'impressed', 'grateful', 'blessed'
    }

    NEGATIVE_WORDS = {
        'frustrating', 'annoying', 'terrible', 'awful', 'disappointed',
        'failed', 'problem', 'issue', 'bug', 'broken', 'struggle',
        'difficult', 'challenging', 'nightmare', 'hate', 'worst'
    }

    INSPIRATIONAL_WORDS = {
        'journey', 'growth', 'learn', 'lessons', 'advice', 'tips',
        'inspire', 'motivation', 'dream', 'goal', 'vision', 'future',
        'transform', 'change', 'impact', 'purpose', 'meaningful'
    }

    INFORMATIVE_WORDS = {
        'how-to', 'guide', 'tutorial', 'explain', 'understand',
        'introduction', 'overview', 'comparison', 'difference', 'what-is',
        'deep-dive', 'analysis', 'review', 'breakdown', 'step-by-step'
    }

    # Visual element suggestions based on themes
    VISUAL_ELEMENTS = {
        'machine learning': ['neural network diagram', 'data visualization', 'robot icon'],
        'web development': ['code editor', 'browser window', 'responsive design'],
        'mobile development': ['smartphone mockup', 'app interface', 'mobile icons'],
        'devops': ['pipeline diagram', 'server rack', 'cloud infrastructure'],
        'data science': ['charts and graphs', 'data flow diagram', 'dashboard'],
        'cloud computing': ['cloud icons', 'server diagram', 'network topology'],
        'security': ['lock icon', 'shield', 'encryption symbols'],
        'API development': ['API endpoints diagram', 'request/response flow', 'documentation'],
        'testing': ['checkmark icons', 'test coverage diagram', 'green/red indicators'],
        'performance': ['speedometer', 'graphs trending up', 'lightning bolt'],
        'career': ['professional avatar', 'growth chart', 'milestone markers'],
        'open source': ['collaboration icons', 'community network', 'code contribution'],
        'startup': ['rocket icon', 'growth metrics', 'product mockup'],
        'learning': ['book icon', 'graduation cap', 'lightbulb'],
        'automation': ['gear icons', 'workflow arrows', 'robot'],
        'databases': ['database cylinders', 'table diagrams', 'data flow'],
        'blockchain': ['chain links', 'blocks diagram', 'decentralized network'],
    }

    def analyze(self, content: Optional[str]) -> ContentAnalysis:
        """
        Analyze LinkedIn post content to extract themes, technologies, and sentiment.

        Args:
            content: The LinkedIn post text to analyze

        Returns:
            ContentAnalysis object with extracted information

        Raises:
            ValueError: If content is empty or None
        """
        if content is None or content.strip() == '':
            raise ValueError("Content cannot be empty or None. Please provide valid post text.")

        content_lower = content.lower()

        # Extract technologies
        technologies = self._extract_technologies(content_lower)

        # Extract themes
        themes = self._extract_themes(content_lower)

        # Determine sentiment
        sentiment = self._analyze_sentiment(content_lower)

        # Extract keywords (unique words from technologies and themes)
        keywords = self._extract_keywords(technologies, themes)

        # Suggest visual elements based on themes
        visual_elements = self._suggest_visual_elements(themes)

        return ContentAnalysis(
            themes=themes,
            technologies=technologies,
            sentiment=sentiment,
            keywords=keywords,
            suggested_visual_elements=visual_elements
        )

    def _extract_technologies(self, content: str) -> list[str]:
        """Extract mentioned technologies from content."""
        technologies = []
        seen = set()

        for pattern, tech in self.TECHNOLOGY_PATTERNS.items():
            if re.search(pattern, content, re.IGNORECASE):
                if tech.lower() not in seen:
                    technologies.append(tech)
                    seen.add(tech.lower())

        return technologies

    def _extract_themes(self, content: str) -> list[str]:
        """Extract themes from content."""
        themes = []
        seen = set()

        for pattern, theme in self.THEME_PATTERNS.items():
            if re.search(pattern, content, re.IGNORECASE):
                if theme.lower() not in seen:
                    themes.append(theme)
                    seen.add(theme.lower())

        return themes

    def _analyze_sentiment(self, content: str) -> Sentiment:
        """Analyze the sentiment of the content."""
        positive_count = 0
        negative_count = 0
        inspirational_count = 0
        informative_count = 0

        words = set(re.findall(r'\b[\w-]+\b', content.lower()))

        for word in words:
            if word in self.POSITIVE_WORDS:
                positive_count += 1
            if word in self.NEGATIVE_WORDS:
                negative_count += 1

        # Check for inspirational patterns
        for word in self.INSPIRATIONAL_WORDS:
            if re.search(rf'\b{re.escape(word)}\b', content, re.IGNORECASE):
                inspirational_count += 1

        # Check for informative patterns
        for word in self.INFORMATIVE_WORDS:
            if re.search(rf'\b{re.escape(word)}\b', content, re.IGNORECASE):
                informative_count += 1

        # Determine dominant sentiment
        if inspirational_count >= 2:
            return Sentiment.INSPIRATIONAL
        elif informative_count >= 2:
            return Sentiment.INFORMATIVE
        elif positive_count > negative_count:
            return Sentiment.POSITIVE
        elif negative_count > positive_count:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL

    def _extract_keywords(self, technologies: list[str], themes: list[str]) -> list[str]:
        """Generate keywords from technologies and themes."""
        keywords = []
        seen = set()

        # Add technologies as keywords
        for tech in technologies:
            if tech.lower() not in seen:
                keywords.append(tech)
                seen.add(tech.lower())

        # Add themes as keywords
        for theme in themes:
            if theme.lower() not in seen:
                keywords.append(theme)
                seen.add(theme.lower())

        return keywords

    def _suggest_visual_elements(self, themes: list[str]) -> list[str]:
        """Suggest visual elements based on detected themes."""
        elements = []
        seen = set()

        for theme in themes:
            if theme in self.VISUAL_ELEMENTS:
                for element in self.VISUAL_ELEMENTS[theme]:
                    if element.lower() not in seen:
                        elements.append(element)
                        seen.add(element.lower())

        # Add default elements if no themes matched
        if not elements:
            elements = ['professional illustration', 'abstract tech pattern', 'modern design']

        return elements[:5]  # Limit to 5 suggestions
