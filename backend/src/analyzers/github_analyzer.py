import re
import os
from typing import Optional
from github import Github, GithubException
from src.models.schemas import AnalysisResult, TechStackItem, Feature
from src.analyzers.code_analyzer import CodeAnalyzer
from src.analyzers.feature_extractor import FeatureExtractor


class GitHubAnalyzer:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.github = Github(self.token) if self.token else Github()
        self.code_analyzer = CodeAnalyzer()
        self.feature_extractor = FeatureExtractor()

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
            readme_content, repo_contents, file_structure
        )

        readme_summary = self._summarize_readme(readme_content)

        return AnalysisResult(
            repo_name=repo.name,
            description=repo.description,
            stars=repo.stargazers_count,
            forks=repo.forks_count,
            language=repo.language,
            tech_stack=tech_stack,
            features=features,
            readme_summary=readme_summary,
            file_structure=file_structure[:50],
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
        """Extract first meaningful paragraph from README."""
        if not readme:
            return None

        lines = readme.split("\n")
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
        if len(summary) > 500:
            summary = summary[:497] + "..."
        return summary if summary else None
