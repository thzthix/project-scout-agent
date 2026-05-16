import pathlib
import sys
import unittest
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.followup import (
    collect_followup_evidence,
    evaluate_candidate_with_followup,
    should_fetch_repo_activity,
)
from project_scout_agent.schemas.request import ProjectScoutRequest
from project_scout_agent.schemas.enrichment import EnrichedCandidate
from project_scout_agent.schemas.evaluation import RepoEvaluation
from project_scout_agent.schemas.request import ProjectScoutRequest
from project_scout_agent.schemas.search_candidate import SearchCandidate


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


def build_evaluation(
    *,
    needs_followup: bool,
    missing_evidence: list[str],
) -> RepoEvaluation:
    return RepoEvaluation.model_validate(
        {
            "repo_name": "langgraph",
            "repo_url": "https://github.com/langchain-ai/langgraph",
            "scores": {
                "readme_score": 4,
                "docs_score": 4,
                "activity_score": 3,
                "example_score": 4,
                "overall_score": 4,
            },
            "recommendation_reason": "This repository is a strong fit for a Python agent workflow project.",
            "evidence_summary": "The README is clear and the repository appears active, but maintenance evidence is incomplete.",
            "follow_up": {
                "confidence": 0.61,
                "needs_followup": needs_followup,
                "missing_evidence": missing_evidence,
                "ambiguity_reason": "Recent maintenance evidence is still limited.",
            },
        }
    )


class FakeTool:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.invocations: list[dict[str, Any]] = []

    def invoke(self, input: dict[str, Any]) -> dict[str, Any]:
        self.invocations.append(input)
        return self.response


class FakeStructuredOutputRunnable:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.invocations: list[Any] = []

    def invoke(self, input: Any) -> dict[str, Any]:
        self.invocations.append(input)
        return self.responses[len(self.invocations) - 1]


class FakeStructuredOutputModel:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.structured_runnable = FakeStructuredOutputRunnable(responses)

    def with_structured_output(
        self,
        schema: type[RepoEvaluation],
    ) -> FakeStructuredOutputRunnable:
        return self.structured_runnable


class FollowUpTest(unittest.TestCase):
    def test_should_fetch_repo_activity_requires_followup_and_maintenance_signal(self) -> None:
        self.assertTrue(
            should_fetch_repo_activity(
                build_evaluation(
                    needs_followup=True,
                    missing_evidence=["maintenance_signal"],
                )
            )
        )
        self.assertFalse(
            should_fetch_repo_activity(
                build_evaluation(
                    needs_followup=False,
                    missing_evidence=["maintenance_signal"],
                )
            )
        )
        self.assertFalse(
            should_fetch_repo_activity(
                build_evaluation(
                    needs_followup=True,
                    missing_evidence=["docs_quality"],
                )
            )
        )

    def test_collect_followup_evidence_runs_activity_tool_only_when_needed(self) -> None:
        candidate = build_enriched_candidate()
        evaluation = build_evaluation(
            needs_followup=True,
            missing_evidence=["maintenance_signal"],
        )
        activity_tool = FakeTool(
            {
                "repo_name": "langgraph",
                "release_names": ["v1.2.0"],
                "updated_at": "2026-05-16T00:00:00Z",
            }
        )

        evidence_items = collect_followup_evidence(
            candidate=candidate,
            evaluation=evaluation,
            activity_tool=activity_tool,
        )

        self.assertEqual(len(evidence_items), 1)
        self.assertEqual(evidence_items[0]["tool_name"], "fetch_repo_activity_summary")
        self.assertEqual(
            activity_tool.invocations,
            [
                {
                    "repo_url": "https://github.com/langchain-ai/langgraph",
                    "max_release_names": 3,
                }
            ],
        )

    def test_collect_followup_evidence_skips_tool_when_not_needed(self) -> None:
        candidate = build_enriched_candidate()
        evaluation = build_evaluation(
            needs_followup=False,
            missing_evidence=[],
        )
        activity_tool = FakeTool({"repo_name": "langgraph"})

        evidence_items = collect_followup_evidence(
            candidate=candidate,
            evaluation=evaluation,
            activity_tool=activity_tool,
        )

        self.assertEqual(evidence_items, [])
        self.assertEqual(activity_tool.invocations, [])

    def test_evaluate_candidate_with_followup_returns_initial_evaluation_when_no_tool_is_needed(self) -> None:
        llm = FakeStructuredOutputModel(
            [
                {
                    **build_evaluation(
                        needs_followup=False,
                        missing_evidence=[],
                    ).model_dump()
                }
            ]
        )
        activity_tool = FakeTool({"repo_name": "langgraph"})

        final_evaluation = evaluate_candidate_with_followup(
            request=build_valid_request(),
            candidate=build_enriched_candidate(),
            llm=llm,
            activity_tool=activity_tool,
        )

        self.assertFalse(final_evaluation.follow_up.needs_followup)
        self.assertEqual(activity_tool.invocations, [])
        self.assertEqual(len(llm.structured_runnable.invocations), 1)

    def test_evaluate_candidate_with_followup_runs_tool_and_reevaluation_when_needed(self) -> None:
        llm = FakeStructuredOutputModel(
            [
                {
                    **build_evaluation(
                        needs_followup=True,
                        missing_evidence=["maintenance_signal"],
                    ).model_dump()
                },
                {
                    **build_evaluation(
                        needs_followup=False,
                        missing_evidence=[],
                    ).model_dump(),
                    "scores": {
                        "readme_score": 4,
                        "docs_score": 4,
                        "activity_score": 5,
                        "example_score": 4,
                        "overall_score": 5,
                    },
                    "evidence_summary": "Recent release and push signals improved maintenance confidence.",
                },
            ]
        )
        activity_tool = FakeTool(
            {
                "repo_name": "langgraph",
                "release_names": ["v1.2.0"],
                "pushed_at": "2026-05-16T12:00:00Z",
            }
        )

        final_evaluation = evaluate_candidate_with_followup(
            request=build_valid_request(),
            candidate=build_enriched_candidate(),
            llm=llm,
            activity_tool=activity_tool,
        )

        self.assertEqual(len(activity_tool.invocations), 1)
        self.assertEqual(len(llm.structured_runnable.invocations), 2)
        self.assertFalse(final_evaluation.follow_up.needs_followup)
        self.assertEqual(final_evaluation.scores.overall_score, 5)


if __name__ == "__main__":
    unittest.main()
