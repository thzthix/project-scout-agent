import json
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError

from project_scout_agent.constants import GITHUB_REPOSITORY_SEARCH_URL
from project_scout_agent.config import get_github_token
from project_scout_agent.schemas.query_seed import QueryPlan, QuerySeed
from project_scout_agent.schemas.search_candidate import (
    SearchCandidate,
    SearchResultForSeed,
)


def _build_search_candidates(payload: dict) -> list[SearchCandidate]:
    return [
        SearchCandidate(
            repo_name=item["name"],
            repo_url=item["html_url"],
            description=item.get("description") or "",
            stars=item["stargazers_count"],
            forks=item["forks_count"],
            updated_at=item["updated_at"],
        )
        for item in payload.get("items", [])
    ]


def search_repositories_for_seed(
    query_seed: QuerySeed,
    github_token: str | None = None,
    per_page: int = 10,
    sort_by: str | None = None,
) -> SearchResultForSeed:
    resolved_github_token = github_token.strip() if github_token else get_github_token()

    if per_page < 1 or per_page > 100:
        raise ValueError("per_page는 1 이상 100 이하여야 합니다.")

    encoded_query = urllib.parse.quote(query_seed.query)
    search_url = f"{GITHUB_REPOSITORY_SEARCH_URL}?q={encoded_query}&per_page={per_page}"
    if sort_by:
        search_url = f"{search_url}&sort={urllib.parse.quote(sort_by)}&order=desc"
    request = urllib.request.Request(
        search_url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {resolved_github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"GitHub 검색 요청이 실패했습니다. status={error.code}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            "GitHub 검색 요청 중 네트워크 오류가 발생했습니다."
        ) from error

    candidates = _build_search_candidates(payload)

    return SearchResultForSeed(
        query_seed=query_seed,
        candidates=candidates,
    )


def search_repositories(
    query_plan: QueryPlan,
    github_token: str | None = None,
    per_page: int = 10,
    sort_by: str | None = None,
) -> list[SearchResultForSeed]:
    search_results: list[SearchResultForSeed] = []

    for query_seed in query_plan.query_seeds:
        search_results.append(
            search_repositories_for_seed(
                query_seed=query_seed,
                github_token=github_token,
                per_page=per_page,
                sort_by=sort_by,
            )
        )

    return search_results
