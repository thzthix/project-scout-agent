from __future__ import annotations

import base64
import json
import urllib.request
from urllib.error import HTTPError, URLError

from project_scout_agent.config import get_github_token
from project_scout_agent.schemas.enrichment import EnrichedCandidate
from project_scout_agent.schemas.search_candidate import SearchCandidate


GITHUB_API_BASE_URL = "https://api.github.com"
README_EXCERPT_MAX_CHARS = 4000


def _extract_repo_coordinates(candidate: SearchCandidate) -> tuple[str, str]:
    repo_url_parts = candidate.repo_url.rstrip("/").split("/")
    if len(repo_url_parts) < 2:
        raise ValueError("유효한 GitHub repository URL이 필요합니다.")

    owner = repo_url_parts[-2].strip()
    repo_name = repo_url_parts[-1].strip()
    if not owner or not repo_name:
        raise ValueError("유효한 GitHub repository URL이 필요합니다.")

    return owner, repo_name


def _load_github_json(api_url: str, github_token: str) -> dict:
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
            f"GitHub enrichment 요청이 실패했습니다. status={error.code}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            "GitHub enrichment 요청 중 네트워크 오류가 발생했습니다."
        ) from error


def _build_readme_excerpt(readme_payload: dict) -> str:
    encoded_content = (readme_payload.get("content") or "").strip()
    if not encoded_content:
        return ""

    decoded_bytes = base64.b64decode(encoded_content)
    decoded_text = decoded_bytes.decode("utf-8", errors="ignore")
    normalized_text = " ".join(decoded_text.split())
    return normalized_text[:README_EXCERPT_MAX_CHARS]


def enrich_candidate(
    candidate: SearchCandidate,
    github_token: str | None = None,
) -> EnrichedCandidate:
    resolved_github_token = github_token.strip() if github_token else get_github_token()
    owner, repo_name = _extract_repo_coordinates(candidate)

    repo_payload = _load_github_json(
        f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo_name}",
        resolved_github_token,
    )
    readme_payload = _load_github_json(
        f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo_name}/readme",
        resolved_github_token,
    )

    return EnrichedCandidate(
        candidate=candidate,
        readme_excerpt=_build_readme_excerpt(readme_payload),
        topics=repo_payload.get("topics") or [],
        primary_language=repo_payload.get("language") or "",
        license_name=(repo_payload.get("license") or {}).get("name") or "",
        homepage_url=repo_payload.get("homepage") or "",
    )


def enrich_candidates(
    candidates: list[SearchCandidate],
    github_token: str | None = None,
) -> list[EnrichedCandidate]:
    enriched_candidates: list[EnrichedCandidate] = []

    for candidate in candidates:
        enriched_candidates.append(
            enrich_candidate(
                candidate=candidate,
                github_token=github_token,
            )
        )

    return enriched_candidates
