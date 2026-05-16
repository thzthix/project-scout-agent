from __future__ import annotations

import json
import urllib.request
from urllib.error import HTTPError, URLError
from typing import Any

from langchain.tools import tool
from pydantic import BaseModel, Field

from project_scout_agent.config import get_github_token


GITHUB_API_BASE_URL = "https://api.github.com"


class RepoActivityToolInput(BaseModel):
    repo_url: str = Field(
        min_length=1,
        max_length=300,
        description="GitHub repository URL to inspect for activity signals.",
    )
    max_release_names: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of recent release names to include.",
    )


def _extract_repo_coordinates(repo_url: str) -> tuple[str, str]:
    repo_url_parts = repo_url.rstrip("/").split("/")
    if len(repo_url_parts) < 2:
        raise ValueError("유효한 GitHub repository URL이 필요합니다.")

    owner = repo_url_parts[-2].strip()
    repo_name = repo_url_parts[-1].strip()
    if not owner or not repo_name:
        raise ValueError("유효한 GitHub repository URL이 필요합니다.")

    return owner, repo_name


def _load_github_json(api_url: str, github_token: str) -> Any:
    request = urllib.request.Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"GitHub follow-up tool 요청이 실패했습니다. status={error.code}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            "GitHub follow-up tool 요청 중 네트워크 오류가 발생했습니다."
        ) from error


def _build_release_names(
    releases_payload: list[dict[str, Any]],
    max_release_names: int,
) -> list[str]:
    release_names: list[str] = []

    for release in releases_payload[:max_release_names]:
        release_name = (release.get("name") or release.get("tag_name") or "").strip()
        if release_name:
            release_names.append(release_name)

    return release_names


@tool(args_schema=RepoActivityToolInput)
def fetch_repo_activity_summary(
    repo_url: str,
    max_release_names: int = 3,
) -> dict[str, Any]:
    """Fetch bounded GitHub activity signals for a repository."""
    github_token = get_github_token()
    owner, repo_name = _extract_repo_coordinates(repo_url)
    repo_payload = _load_github_json(
        f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo_name}",
        github_token,
    )
    releases_payload = _load_github_json(
        f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo_name}/releases?per_page={max_release_names}",
        github_token,
    )

    return {
        "repo_name": repo_payload.get("name") or repo_name,
        "repo_url": repo_payload.get("html_url") or repo_url,
        "stars": repo_payload.get("stargazers_count") or 0,
        "forks": repo_payload.get("forks_count") or 0,
        "open_issues_count": repo_payload.get("open_issues_count") or 0,
        "subscribers_count": repo_payload.get("subscribers_count") or 0,
        "updated_at": repo_payload.get("updated_at") or "",
        "pushed_at": repo_payload.get("pushed_at") or "",
        "archived": bool(repo_payload.get("archived")),
        "release_names": _build_release_names(
            releases_payload if isinstance(releases_payload, list) else [],
            max_release_names=max_release_names,
        ),
    }
