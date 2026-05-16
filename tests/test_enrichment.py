import base64
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.enrichment import (
    README_EXCERPT_MAX_CHARS,
    _build_readme_excerpt,
    _extract_repo_coordinates,
    enrich_candidate,
    enrich_candidates,
)
from project_scout_agent.schemas.search_candidate import SearchCandidate


class EnrichmentTest(unittest.TestCase):
    def test_extract_repo_coordinates_reads_owner_and_repo_name(self) -> None:
        candidate = SearchCandidate(
            repo_name="langgraph",
            repo_url="https://github.com/langchain-ai/langgraph",
            description="Stateful agent workflow library.",
            stars=100,
            forks=10,
            updated_at="2026-05-16T00:00:00Z",
        )

        owner, repo_name = _extract_repo_coordinates(candidate)

        self.assertEqual(owner, "langchain-ai")
        self.assertEqual(repo_name, "langgraph")

    def test_build_readme_excerpt_normalizes_whitespace_and_truncates(self) -> None:
        raw_text = ("Hello   world\n\n" * 1000).encode("utf-8")
        readme_payload = {
            "content": base64.b64encode(raw_text).decode("utf-8"),
        }

        excerpt = _build_readme_excerpt(readme_payload)

        self.assertTrue(excerpt.startswith("Hello world"))
        self.assertLessEqual(len(excerpt), README_EXCERPT_MAX_CHARS)

    def test_enrich_candidate_builds_enriched_candidate_from_github_payloads(self) -> None:
        candidate = SearchCandidate(
            repo_name="langgraph",
            repo_url="https://github.com/langchain-ai/langgraph",
            description="Stateful agent workflow library.",
            stars=100,
            forks=10,
            updated_at="2026-05-16T00:00:00Z",
        )

        repo_payload = {
            "topics": ["agents", "langgraph"],
            "language": "Python",
            "license": {"name": "MIT License"},
            "homepage": "https://www.langchain.com/langgraph",
        }
        readme_payload = {
            "content": base64.b64encode(
                b"LangGraph helps build stateful agent systems."
            ).decode("utf-8"),
        }

        with patch(
            "project_scout_agent.enrichment._load_github_json",
            side_effect=[repo_payload, readme_payload],
        ) as mock_load_github_json:
            enriched_candidate = enrich_candidate(
                candidate=candidate,
                github_token="test-token",
            )

        self.assertEqual(mock_load_github_json.call_count, 2)
        self.assertEqual(enriched_candidate.candidate.repo_name, "langgraph")
        self.assertEqual(enriched_candidate.topics, ["agents", "langgraph"])
        self.assertEqual(enriched_candidate.primary_language, "Python")
        self.assertEqual(enriched_candidate.license_name, "MIT License")
        self.assertIn("stateful agent systems", enriched_candidate.readme_excerpt)

    def test_enrich_candidates_enriches_each_candidate_in_order(self) -> None:
        first_candidate = SearchCandidate(
            repo_name="langgraph",
            repo_url="https://github.com/langchain-ai/langgraph",
            description="Stateful agent workflow library.",
            stars=100,
            forks=10,
            updated_at="2026-05-16T00:00:00Z",
        )
        second_candidate = SearchCandidate(
            repo_name="haystack",
            repo_url="https://github.com/deepset-ai/haystack",
            description="LLM orchestration framework.",
            stars=200,
            forks=20,
            updated_at="2026-05-16T00:00:00Z",
        )

        with patch(
            "project_scout_agent.enrichment.enrich_candidate",
            side_effect=[
                "first-enriched",
                "second-enriched",
            ],
        ) as mock_enrich_candidate:
            enriched_candidates = enrich_candidates(
                [first_candidate, second_candidate],
                github_token="test-token",
            )

        self.assertEqual(
            enriched_candidates,
            ["first-enriched", "second-enriched"],
        )
        self.assertEqual(mock_enrich_candidate.call_count, 2)
        first_call = mock_enrich_candidate.call_args_list[0].kwargs
        second_call = mock_enrich_candidate.call_args_list[1].kwargs
        self.assertEqual(first_call["candidate"], first_candidate)
        self.assertEqual(second_call["candidate"], second_candidate)
