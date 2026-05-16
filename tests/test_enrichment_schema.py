import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.schemas.enrichment import EnrichedCandidate
from project_scout_agent.schemas.search_candidate import SearchCandidate


class EnrichmentSchemaTest(unittest.TestCase):
    def test_enriched_candidate_accepts_minimal_payload(self) -> None:
        enriched_candidate = EnrichedCandidate(
            candidate=SearchCandidate(
                repo_name="langgraph",
                repo_url="https://github.com/langchain-ai/langgraph",
                description="Stateful agent workflow library.",
                stars=100,
                forks=10,
                updated_at="2026-05-16T00:00:00Z",
            ),
            readme_excerpt="LangGraph helps build stateful agent systems.",
            topics=["agents", "langgraph"],
            primary_language="Python",
            license_name="MIT License",
            homepage_url="https://www.langchain.com/langgraph",
        )

        self.assertEqual(enriched_candidate.candidate.repo_name, "langgraph")
        self.assertEqual(enriched_candidate.primary_language, "Python")

    def test_enriched_candidate_defaults_optional_fields(self) -> None:
        enriched_candidate = EnrichedCandidate(
            candidate=SearchCandidate(
                repo_name="haystack",
                repo_url="https://github.com/deepset-ai/haystack",
                description="LLM orchestration framework.",
                stars=200,
                forks=20,
                updated_at="2026-05-16T00:00:00Z",
            ),
        )

        self.assertEqual(enriched_candidate.readme_excerpt, "")
        self.assertEqual(enriched_candidate.topics, [])
        self.assertEqual(enriched_candidate.primary_language, "")
