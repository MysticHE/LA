import re
import os
import logging
from typing import Optional, TYPE_CHECKING
from github import Github, GithubException
from src.models.schemas import AnalysisResult, TechStackItem, Feature, InsightType
from src.analyzers.code_analyzer import CodeAnalyzer
from src.analyzers.feature_extractor import FeatureExtractor
from src.analyzers.insights_analyzer import InsightsAnalyzer

if TYPE_CHECKING:
    from src.services.openai_client import OpenAIClient

logger = logging.getLogger(__name__)


AI_SUMMARY_PROMPT = """Summarize this GitHub project in 1-2 sentences for a LinkedIn audience.

Project: {repo_name}
Description: {description}
Tech Stack: {tech_stack}
README excerpt: {readme_excerpt}

Write a compelling, concise summary (under 150 characters) that captures what makes this project interesting.
Return ONLY the summary text, no quotes or explanation."""


class GitHubAnalyzer:
    def __init__(
        self,
        token: Optional[str] = None,
        openai_client: Optional["OpenAIClient"] = None,
    ):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.github = Github(self.token) if self.token else Github()
        self.openai_client = openai_client
        # Pass AI client to analyzers for enhanced analysis
        self.code_analyzer = CodeAnalyzer(ai_client=openai_client)
        self.feature_extractor = FeatureExtractor()
        self.insights_analyzer = InsightsAnalyzer(ai_client=openai_client)

    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        """Extract owner and repo name from GitHub URL."""
        patterns = [
            r"github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
            r"github\.com/([^/]+)/([^/]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2).rstrip("/")
        raise ValueError(f"Invalid GitHub URL: {url}")

    async def analyze(self, url: str) -> AnalysisResult:
        """Analyze a GitHub repository."""
        owner, repo_name = self._parse_repo_url(url)

        try:
            repo = self.github.get_repo(f"{owner}/{repo_name}")
        except GithubException as e:
            if e.status == 404:
                raise ValueError(f"Repository not found: {owner}/{repo_name}")
            elif e.status == 403:
                raise ValueError("API rate limit exceeded. Try adding a GitHub token.")
            raise ValueError(f"GitHub API error: {e.data.get('message', str(e))}")

        readme_content = self._get_readme(repo)
        file_structure = self._get_file_structure(repo)
        repo_contents = self._get_key_files(repo)

        tech_stack = self.code_analyzer.analyze(repo_contents, repo.language)
        features = self.feature_extractor.extract(
            readme_content,
            repo_contents,
            file_structure,
            openai_client=self.openai_client,
            repo_description=repo.description or "",
        )

        readme_summary = self._summarize_readme(readme_content)

        insights = self.insights_analyzer.analyze(
            tech_stack=tech_stack,
            file_contents=repo_contents,
            file_structure=file_structure,
            primary_language=repo.language,
            readme=readme_content,
        )

        # Merge features with highlight insights (de-duplicate)
        merged_features = self._merge_features_and_highlights(
            features=features,
            insights=insights,
        )

        # Filter insights to only Strengths and Considerations
        filtered_insights = [
            i for i in insights if i.type != InsightType.HIGHLIGHT
        ]

        # Generate AI summary if client available
        ai_summary = self._generate_ai_summary(
            repo_name=repo.name,
            description=repo.description,
            tech_stack=tech_stack,
            readme=readme_content,
        )

        return AnalysisResult(
            repo_name=repo.name,
            description=repo.description,
            stars=repo.stargazers_count,
            forks=repo.forks_count,
            language=repo.language,
            tech_stack=tech_stack,
            features=merged_features,
            readme_summary=readme_summary,
            ai_summary=ai_summary,
            file_structure=file_structure[:50],
            insights=filtered_insights,
        )

    def _get_readme(self, repo) -> Optional[str]:
        """Get README content."""
        try:
            readme = repo.get_readme()
            return readme.decoded_content.decode("utf-8")
        except GithubException:
            return None

    def _get_file_structure(self, repo, path: str = "", depth: int = 0) -> list[str]:
        """Get repository file structure (limited depth)."""
        if depth > 2:
            return []

        files = []
        try:
            contents = repo.get_contents(path)
            for content in contents:
                if content.type == "dir":
                    if content.name not in [
                        "node_modules",
                        ".git",
                        "__pycache__",
                        "venv",
                        ".venv",
                        "dist",
                        "build",
                    ]:
                        files.append(f"{content.path}/")
                        files.extend(
                            self._get_file_structure(repo, content.path, depth + 1)
                        )
                else:
                    files.append(content.path)
        except GithubException:
            pass
        return files

    def _get_key_files(self, repo) -> dict[str, str]:
        """Get content of key configuration files."""
        key_files = [
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            "Gemfile",
            "composer.json",
        ]

        contents = {}
        for filename in key_files:
            try:
                file_content = repo.get_contents(filename)
                contents[filename] = file_content.decoded_content.decode("utf-8")
            except GithubException:
                pass

        return contents

    def _summarize_readme(self, readme: Optional[str]) -> Optional[str]:
        """Extract first meaningful paragraph from README with HTML/markdown stripped."""
        if not readme:
            return None

        # Strip HTML tags
        text = re.sub(r"<[^>]+>", "", readme)
        # Strip markdown images ![alt](url)
        text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
        # Strip markdown links but keep text [text](url) -> text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # Strip HTML entities
        text = re.sub(r"&[a-zA-Z]+;", " ", text)
        # Strip badge URLs and shields.io references
        text = re.sub(r"https?://[^\s]+", "", text)

        lines = text.split("\n")
        summary_lines = []
        in_content = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_content and summary_lines:
                    break
                continue
            if stripped.startswith("#"):
                in_content = True
                continue
            if stripped.startswith(("![", "[!", "<!--", "```")):
                continue
            if in_content:
                summary_lines.append(stripped)
                if len(" ".join(summary_lines)) > 300:
                    break

        summary = " ".join(summary_lines)
        # Clean up multiple spaces
        summary = re.sub(r"\s+", " ", summary).strip()
        if len(summary) > 500:
            summary = summary[:497] + "..."
        return summary if summary else None

    def _generate_ai_summary(
        self,
        repo_name: str,
        description: Optional[str],
        tech_stack: list[TechStackItem],
        readme: Optional[str],
    ) -> Optional[str]:
        """Generate an AI summary for the project."""
        if not self.openai_client:
            return None

        try:
            tech_stack_str = ", ".join([t.name for t in tech_stack[:10]]) or "Not specified"
            readme_excerpt = (readme[:1500] if readme else "") or "No README available"

            prompt = AI_SUMMARY_PROMPT.format(
                repo_name=repo_name,
                description=description or "No description",
                tech_stack=tech_stack_str,
                readme_excerpt=readme_excerpt,
            )

            result = self.openai_client.generate_content(
                system_prompt="You are a technical writer creating concise project summaries. Return only the summary text.",
                user_prompt=prompt,
            )

            if result.success and result.content:
                summary = result.content.strip().strip('"').strip("'")
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                return summary
            return None
        except Exception as e:
            logger.debug("AI summary generation failed: %s", str(e))
            return None

    def _merge_features_and_highlights(
        self,
        features: list[Feature],
        insights: list,
    ) -> list[Feature]:
        """Merge features with highlight insights, de-duplicating by title."""
        merged = []
        seen_titles: set[str] = set()

        # Add features first (higher priority - from README)
        for f in features:
            normalized = f.name.lower().strip()
            if normalized not in seen_titles:
                merged.append(f)
                seen_titles.add(normalized)

        # Add highlights that don't duplicate features
        for insight in insights:
            if insight.type != InsightType.HIGHLIGHT:
                continue
            normalized = insight.title.lower().strip()
            if normalized not in seen_titles:
                merged.append(
                    Feature(name=insight.title, description=insight.description)
                )
                seen_titles.add(normalized)

        return merged[:8]  # Limit to 8 items
