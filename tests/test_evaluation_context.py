import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.evaluation import build_evaluation_context
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


def build_enriched_candidate() -> EnrichedCandidate:
    return EnrichedCandidate(
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


class EvaluationContextTest(unittest.TestCase):
    def test_build_evaluation_context_keeps_project_and_candidate_boundaries(self) -> None:
        context = build_evaluation_context(
            request=build_valid_request(),
            candidate=build_enriched_candidate(),
        )

        self.assertEqual(
            context["project"]["target_repository_description"],
            "python agent workflow reference repository",
        )
        self.assertEqual(context["candidate"]["repo_name"], "langgraph")
        self.assertEqual(context["candidate"]["primary_language"], "Python")
        self.assertNotIn("project_name", context["project"])
        self.assertNotIn("repo_url", context["candidate"])
        self.assertNotIn("forks", context["candidate"])

    def test_build_evaluation_context_includes_constraints_and_readme_excerpt(self) -> None:
        context = build_evaluation_context(
            request=build_valid_request(),
            candidate=build_enriched_candidate(),
        )

        self.assertEqual(context["project"]["preferred_languages"], ["python"])
        self.assertTrue(context["project"]["must_have_docs"])
        self.assertIn("stateful agent systems", context["candidate"]["readme_excerpt"])
