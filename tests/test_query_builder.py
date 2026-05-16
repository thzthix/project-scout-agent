import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.constants import RequestSection
from project_scout_agent.query_builder import build_query_seeds
from project_scout_agent.schemas.request import ProjectScoutRequest


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
                "license_types": ["MIT"],
                "must_have_docs": True,
            },
        }
    )


class QueryBuilderTest(unittest.TestCase):
    def _find_query_by_source(
        self,
        query_plan,
        source: RequestSection,
    ):
        for query_seed in query_plan.query_seeds:
            if query_seed.source == source:
                return query_seed
        return None

    def test_build_query_seeds_creates_three_queries_when_all_inputs_exist(self) -> None:
        request = build_valid_request()

        query_plan = build_query_seeds(request)

        self.assertEqual(len(query_plan.query_seeds), 3)
        self.assertIsNotNone(
            self._find_query_by_source(
                query_plan,
                RequestSection.TARGET_REPOSITORY_DESCRIPTION,
            )
        )
        self.assertIsNotNone(
            self._find_query_by_source(
                query_plan,
                RequestSection.SEED_KEYWORDS,
            )
        )
        self.assertIsNotNone(
            self._find_query_by_source(
                query_plan,
                RequestSection.CONSTRAINTS,
            )
        )

    def test_build_query_seeds_skips_seed_keyword_query_when_keywords_are_empty(self) -> None:
        request = build_valid_request()
        request.seed_keywords = []

        query_plan = build_query_seeds(request)

        self.assertEqual(len(query_plan.query_seeds), 2)
        self.assertNotIn(
            RequestSection.SEED_KEYWORDS,
            [query_seed.source for query_seed in query_plan.query_seeds],
        )

    def test_build_query_seeds_skips_constraint_query_when_constraints_are_empty(self) -> None:
        request = build_valid_request()
        request.constraints.preferred_languages = []
        request.constraints.license_types = []
        request.constraints.must_have_docs = False

        query_plan = build_query_seeds(request)

        self.assertEqual(len(query_plan.query_seeds), 2)
        self.assertNotIn(
            RequestSection.CONSTRAINTS,
            [query_seed.source for query_seed in query_plan.query_seeds],
        )

    def test_constraint_query_tracks_used_constraint_fields(self) -> None:
        request = build_valid_request()

        query_plan = build_query_seeds(request)
        constraint_query = self._find_query_by_source(
            query_plan,
            RequestSection.CONSTRAINTS,
        )

        self.assertIsNotNone(constraint_query)
        self.assertEqual(
            constraint_query.used_fields,
            [
                "constraints.preferred_languages",
                "constraints.license_types",
                "constraints.must_have_docs",
            ],
        )


if __name__ == "__main__":
    unittest.main()
