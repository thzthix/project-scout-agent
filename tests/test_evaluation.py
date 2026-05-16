import pathlib
import sys
import unittest
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.evaluation import evaluate_candidate, evaluate_candidates
from project_scout_agent.schemas.enrichment import EnrichedCandidate
from project_scout_agent.schemas.evaluation import RepoEvaluation
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


def build_second_enriched_candidate() -> EnrichedCandidate:
    return EnrichedCandidate(
        candidate=SearchCandidate(
            repo_name="haystack",
            repo_url="https://github.com/deepset-ai/haystack",
            description="LLM orchestration framework.",
            stars=200,
            forks=20,
            updated_at="2026-05-15T00:00:00Z",
        ),
        readme_excerpt="Haystack helps build production-ready LLM applications.",
        topics=["llm", "rag"],
        primary_language="Python",
        license_name="Apache-2.0",
        homepage_url="https://haystack.deepset.ai",
    )


def build_valid_evaluation_payload() -> dict[str, Any]:
    return {
        "repo_name": "wrong-name",
        "repo_url": "https://wrong.example.com/repo",
        "scores": {
            "readme_score": 4,
            "docs_score": 4,
            "activity_score": 5,
            "example_score": 4,
            "overall_score": 4,
        },
        "recommendation_reason": "This repository is a strong fit for a Python agent workflow project.",
        "evidence_summary": "The README is clear, the topics match, and the repository shows recent activity.",
        "follow_up": {
            "confidence": 0.84,
            "needs_followup": False,
            "missing_evidence": [],
            "ambiguity_reason": "",
        },
    }


class FakeStructuredOutputRunnable:
    def __init__(
        self,
        response: RepoEvaluation | dict[str, Any] | list[RepoEvaluation | dict[str, Any]],
    ) -> None:
        self.response = response
        self.invocations: list[Any] = []

    def invoke(self, input: Any) -> RepoEvaluation | dict[str, Any]:
        self.invocations.append(input)
        if isinstance(self.response, list):
            return self.response[len(self.invocations) - 1]
        return self.response


class FakeStructuredOutputModel:
    def __init__(
        self,
        response: RepoEvaluation | dict[str, Any] | list[RepoEvaluation | dict[str, Any]],
    ) -> None:
        self.response = response
        self.schemas: list[type[RepoEvaluation]] = []
        self.structured_runnable = FakeStructuredOutputRunnable(response)

    def with_structured_output(
        self,
        schema: type[RepoEvaluation],
    ) -> FakeStructuredOutputRunnable:
        self.schemas.append(schema)
        return self.structured_runnable


class EvaluateCandidateTest(unittest.TestCase):
    def test_evaluate_candidate_returns_repo_evaluation(self) -> None:
        llm = FakeStructuredOutputModel(build_valid_evaluation_payload())

        evaluation = evaluate_candidate(
            request=build_valid_request(),
            candidate=build_enriched_candidate(),
            llm=llm,
        )

        self.assertIsInstance(evaluation, RepoEvaluation)
        self.assertEqual(evaluation.repo_name, "langgraph")
        self.assertEqual(
            evaluation.repo_url,
            "https://github.com/langchain-ai/langgraph",
        )
        self.assertEqual(evaluation.scores.overall_score, 4)
        self.assertEqual(llm.schemas, [RepoEvaluation])

    def test_evaluate_candidate_passes_candidate_identity_and_context_to_prompt(self) -> None:
        llm = FakeStructuredOutputModel(build_valid_evaluation_payload())

        evaluate_candidate(
            request=build_valid_request(),
            candidate=build_enriched_candidate(),
            llm=llm,
        )

        prompt_value = llm.structured_runnable.invocations[0]
        prompt_text = "\n".join(message.content for message in prompt_value.messages)

        self.assertIn('"repo_name": "langgraph"', prompt_text)
        self.assertIn('"repo_url": "https://github.com/langchain-ai/langgraph"', prompt_text)
        self.assertIn('"must_have_docs": true', prompt_text)
        self.assertIn('"readme_excerpt": "LangGraph helps build stateful agent systems."', prompt_text)

    def test_evaluate_candidates_returns_evaluations_in_input_order(self) -> None:
        llm = FakeStructuredOutputModel(
            [
                build_valid_evaluation_payload(),
                {
                    **build_valid_evaluation_payload(),
                    "repo_name": "wrong-second-name",
                    "repo_url": "https://wrong.example.com/second-repo",
                    "recommendation_reason": "This repository is useful for comparing another Python LLM stack.",
                },
            ]
        )

        evaluations = evaluate_candidates(
            request=build_valid_request(),
            candidates=[
                build_enriched_candidate(),
                build_second_enriched_candidate(),
            ],
            llm=llm,
        )

        self.assertEqual(len(evaluations), 2)
        self.assertEqual(evaluations[0].repo_name, "langgraph")
        self.assertEqual(
            evaluations[0].repo_url,
            "https://github.com/langchain-ai/langgraph",
        )
        self.assertEqual(evaluations[1].repo_name, "haystack")
        self.assertEqual(
            evaluations[1].repo_url,
            "https://github.com/deepset-ai/haystack",
        )
        self.assertEqual(len(llm.structured_runnable.invocations), 2)


if __name__ == "__main__":
    unittest.main()
