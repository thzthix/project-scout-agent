import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.constants import RequestSection
from project_scout_agent.schemas.query_seed import QuerySeed
from project_scout_agent.search import (
    _build_search_candidates,
    search_repositories_for_seed,
)


def build_query_seed() -> QuerySeed:
    return QuerySeed(
        query="python agent workflow reference repository",
        source=RequestSection.TARGET_REPOSITORY_DESCRIPTION,
        used_fields=["target_repository_description"],
    )


class SearchTest(unittest.TestCase):
    def test_build_search_candidates_maps_github_payload(self) -> None:
        payload = {
            "items": [
                {
                    "name": "langgraph",
                    "html_url": "https://github.com/langchain-ai/langgraph",
                    "description": "Build stateful multi-actor applications with LLMs.",
                    "stargazers_count": 15000,
                    "forks_count": 1200,
                    "updated_at": "2026-05-16T00:00:00Z",
                }
            ]
        }

        candidates = _build_search_candidates(payload)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].repo_name, "langgraph")
        self.assertEqual(
            candidates[0].repo_url,
            "https://github.com/langchain-ai/langgraph",
        )
        self.assertEqual(candidates[0].stars, 15000)
        self.assertEqual(candidates[0].forks, 1200)

    def test_build_search_candidates_fills_empty_description(self) -> None:
        payload = {
            "items": [
                {
                    "name": "example-repo",
                    "html_url": "https://github.com/example/example-repo",
                    "description": None,
                    "stargazers_count": 10,
                    "forks_count": 2,
                    "updated_at": "2026-05-16T00:00:00Z",
                }
            ]
        }

        candidates = _build_search_candidates(payload)

        self.assertEqual(candidates[0].description, "")

    def test_search_requires_github_token(self) -> None:
        query_seed = build_query_seed()

        with self.assertRaisesRegex(
            ValueError,
            "GITHUB_TOKEN이 필요합니다",
        ):
            search_repositories_for_seed(
                query_seed=query_seed,
                github_token="",
            )

    def test_search_validates_per_page_range(self) -> None:
        query_seed = build_query_seed()

        with self.assertRaisesRegex(
            ValueError,
            "per_page는 1 이상 100 이하여야 합니다",
        ):
            search_repositories_for_seed(
                query_seed=query_seed,
                github_token="test-token",
                per_page=0,
            )


if __name__ == "__main__":
    unittest.main()
