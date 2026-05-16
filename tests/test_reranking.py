import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.reranking import (
    build_reranking_signals,
    build_reranking_artifact,
    rerank_candidates,
    score_candidate_for_reranking,
)
from project_scout_agent.schemas.enrichment import EnrichedCandidate
from project_scout_agent.schemas.request import ProjectScoutRequest
from project_scout_agent.schemas.search_candidate import SearchCandidate


def build_valid_request() -> ProjectScoutRequest:
    return ProjectScoutRequest.model_validate(
        {
            "project_name": "Project Scout Agent",
            "project_goal": "I want to build an agent system that finds and evaluates GitHub repositories for my project.",
            "target_repository_description": "python agent workflow reference repository",
            "priorities": ["docs_quality", "activity"],
            "custom_priorities": [],
            "seed_keywords": ["langchain", "langgraph", "tool calling"],
            "constraints": {
                "preferred_languages": ["python"],
                "license_types": [],
                "must_have_docs": True,
            },
        }
    )


def build_enriched_candidate(
    *,
    repo_name: str,
    repo_url: str,
    stars: int,
    forks: int,
    updated_at: str,
    primary_language: str,
) -> EnrichedCandidate:
    return EnrichedCandidate(
        candidate=SearchCandidate(
            repo_name=repo_name,
            repo_url=repo_url,
            description="Repository description.",
            stars=stars,
            forks=forks,
            updated_at=updated_at,
        ),
        readme_excerpt="README excerpt.",
        topics=["agents"],
        primary_language=primary_language,
        license_name="MIT License",
        homepage_url="",
    )


class RerankingTest(unittest.TestCase):
    def test_build_reranking_signals_includes_language_match_and_authority(self) -> None:
        request = build_valid_request()
        candidate = build_enriched_candidate(
            repo_name="langgraph",
            repo_url="https://github.com/langchain-ai/langgraph",
            stars=1000,
            forks=200,
            updated_at="2026-05-16T00:00:00Z",
            primary_language="Python",
        )

        signals = build_reranking_signals(
            request=request,
            candidate=candidate,
        )

        self.assertTrue(signals["language_match"])
        self.assertEqual(signals["stars"], 1000)
        self.assertEqual(signals["forks"], 200)
        self.assertEqual(signals["updated_at"], "2026-05-16T00:00:00Z")
        self.assertGreater(signals["authority_score"], 0.0)

    def test_score_candidate_for_reranking_prefers_language_match_first(self) -> None:
        request = build_valid_request()
        matching_candidate = build_enriched_candidate(
            repo_name="python-agent",
            repo_url="https://github.com/example/python-agent",
            stars=50,
            forks=10,
            updated_at="2026-05-16T00:00:00Z",
            primary_language="Python",
        )
        non_matching_candidate = build_enriched_candidate(
            repo_name="typescript-agent",
            repo_url="https://github.com/example/typescript-agent",
            stars=10000,
            forks=500,
            updated_at="2026-05-16T00:00:00Z",
            primary_language="TypeScript",
        )

        matching_score = score_candidate_for_reranking(
            request=request,
            candidate=matching_candidate,
        )
        non_matching_score = score_candidate_for_reranking(
            request=request,
            candidate=non_matching_candidate,
        )

        self.assertGreater(matching_score, non_matching_score)

    def test_rerank_candidates_sorts_by_deterministic_score(self) -> None:
        request = build_valid_request()
        older_python_candidate = build_enriched_candidate(
            repo_name="older-python-agent",
            repo_url="https://github.com/example/older-python-agent",
            stars=500,
            forks=100,
            updated_at="2024-01-01T00:00:00Z",
            primary_language="Python",
        )
        fresher_python_candidate = build_enriched_candidate(
            repo_name="fresher-python-agent",
            repo_url="https://github.com/example/fresher-python-agent",
            stars=500,
            forks=100,
            updated_at="2026-05-16T00:00:00Z",
            primary_language="Python",
        )
        non_matching_candidate = build_enriched_candidate(
            repo_name="rust-agent",
            repo_url="https://github.com/example/rust-agent",
            stars=5000,
            forks=800,
            updated_at="2026-05-16T00:00:00Z",
            primary_language="Rust",
        )

        reranked_candidates = rerank_candidates(
            request=request,
            candidates=[
                non_matching_candidate,
                older_python_candidate,
                fresher_python_candidate,
            ],
        )

        self.assertEqual(reranked_candidates[0].candidate.repo_name, "fresher-python-agent")
        self.assertEqual(reranked_candidates[1].candidate.repo_name, "older-python-agent")
        self.assertEqual(reranked_candidates[2].candidate.repo_name, "rust-agent")

    def test_build_reranking_artifact_explains_rank_order(self) -> None:
        request = build_valid_request()
        matching_candidate = build_enriched_candidate(
            repo_name="python-agent",
            repo_url="https://github.com/example/python-agent",
            stars=500,
            forks=100,
            updated_at="2026-05-16T00:00:00Z",
            primary_language="Python",
        )
        non_matching_candidate = build_enriched_candidate(
            repo_name="rust-agent",
            repo_url="https://github.com/example/rust-agent",
            stars=5000,
            forks=800,
            updated_at="2026-05-16T00:00:00Z",
            primary_language="Rust",
        )

        artifact = build_reranking_artifact(
            request=request,
            candidates=[non_matching_candidate, matching_candidate],
        )

        self.assertEqual(artifact[0]["rank"], 1)
        self.assertEqual(artifact[0]["repo_name"], "python-agent")
        self.assertEqual(artifact[0]["score"]["language_match"], 1)
        self.assertGreater(artifact[0]["score"]["authority_score"], 0.0)
        self.assertEqual(artifact[1]["rank"], 2)
        self.assertEqual(artifact[1]["repo_name"], "rust-agent")
        self.assertFalse(artifact[1]["signals"]["language_match"])


if __name__ == "__main__":
    unittest.main()
