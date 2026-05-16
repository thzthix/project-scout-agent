from __future__ import annotations

import json
from typing import Any, Protocol

from langchain_core.prompts import ChatPromptTemplate

from project_scout_agent.schemas.enrichment import EnrichedCandidate
from project_scout_agent.schemas.evaluation import RepoEvaluation
from project_scout_agent.schemas.request import ProjectScoutRequest


def build_evaluation_context(
    request: ProjectScoutRequest,
    candidate: EnrichedCandidate,
) -> dict:
    project_context = {
        "project_goal": request.project_goal,
        "target_repository_description": request.target_repository_description,
        "priorities": request.priorities,
        "preferred_languages": request.constraints.preferred_languages,
        "must_have_docs": request.constraints.must_have_docs,
    }
    if request.custom_priorities:
        project_context["custom_priorities"] = request.custom_priorities

    return {
        "project": project_context,
        "candidate": {
            "repo_name": candidate.candidate.repo_name,
            "description": candidate.candidate.description,
            "readme_excerpt": candidate.readme_excerpt,
            "topics": candidate.topics,
            "primary_language": candidate.primary_language,
            "license_name": candidate.license_name,
            "stars": candidate.candidate.stars,
            "updated_at": candidate.candidate.updated_at,
        },
    }


class StructuredOutputRunnable(Protocol):
    def invoke(self, input: Any) -> RepoEvaluation | dict[str, Any]:
        ...


class StructuredOutputModel(Protocol):
    def with_structured_output(
        self,
        schema: type[RepoEvaluation],
    ) -> StructuredOutputRunnable:
        ...


def _build_evaluation_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You evaluate whether a GitHub repository is a good fit for a user's project. "
                    "Use only the provided evidence. Do not invent missing facts. "
                    "Score conservatively when evidence is weak or incomplete. "
                    "Keep recommendation_reason and evidence_summary brief and concrete. "
                    "Copy the provided candidate identity fields exactly."
                ),
            ),
            (
                "human",
                (
                    "Candidate identity:\n"
                    "{candidate_identity}\n\n"
                    "Evaluation context:\n"
                    "{evaluation_context}"
                ),
            ),
        ]
    )


def _build_candidate_identity(candidate: EnrichedCandidate) -> dict[str, str]:
    return {
        "repo_name": candidate.candidate.repo_name,
        "repo_url": candidate.candidate.repo_url,
    }


def _serialize_prompt_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _coerce_repo_evaluation(
    result: RepoEvaluation | dict[str, Any],
    candidate: EnrichedCandidate,
) -> RepoEvaluation:
    payload = result.model_dump() if isinstance(result, RepoEvaluation) else dict(result)
    payload["repo_name"] = candidate.candidate.repo_name
    payload["repo_url"] = candidate.candidate.repo_url
    return RepoEvaluation.model_validate(payload)


def evaluate_candidate(
    request: ProjectScoutRequest,
    candidate: EnrichedCandidate,
    llm: StructuredOutputModel,
) -> RepoEvaluation:
    evaluation_context = build_evaluation_context(
        request=request,
        candidate=candidate,
    )
    prompt = _build_evaluation_prompt()
    prompt_value = prompt.invoke(
        {
            "candidate_identity": _serialize_prompt_payload(
                _build_candidate_identity(candidate)
            ),
            "evaluation_context": _serialize_prompt_payload(evaluation_context),
        }
    )
    structured_llm = llm.with_structured_output(RepoEvaluation)
    result = structured_llm.invoke(prompt_value)
    return _coerce_repo_evaluation(
        result=result,
        candidate=candidate,
    )


def evaluate_candidates(
    request: ProjectScoutRequest,
    candidates: list[EnrichedCandidate],
    llm: StructuredOutputModel,
) -> list[RepoEvaluation]:
    evaluations: list[RepoEvaluation] = []

    for candidate in candidates:
        evaluations.append(
            evaluate_candidate(
                request=request,
                candidate=candidate,
                llm=llm,
            )
        )

    return evaluations
