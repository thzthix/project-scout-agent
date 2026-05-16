from __future__ import annotations

from typing import Any, Protocol

from project_scout_agent.followup_tools import fetch_repo_activity_summary
from project_scout_agent.evaluation import (
    StructuredOutputModel,
    evaluate_candidate,
    reevaluate_candidate_with_followup,
)
from project_scout_agent.schemas.enrichment import EnrichedCandidate
from project_scout_agent.schemas.evaluation import RepoEvaluation
from project_scout_agent.schemas.request import ProjectScoutRequest


class ToolInvoker(Protocol):
    def invoke(self, input: dict[str, Any]) -> Any:
        ...


def should_fetch_repo_activity(evaluation: RepoEvaluation) -> bool:
    if not evaluation.follow_up.needs_followup:
        return False

    return "maintenance_signal" in evaluation.follow_up.missing_evidence


def collect_followup_evidence(
    candidate: EnrichedCandidate,
    evaluation: RepoEvaluation,
    activity_tool: ToolInvoker = fetch_repo_activity_summary,
) -> list[dict[str, Any]]:
    evidence_items: list[dict[str, Any]] = []

    if should_fetch_repo_activity(evaluation):
        activity_summary = activity_tool.invoke(
            {
                "repo_url": candidate.candidate.repo_url,
                "max_release_names": 3,
            }
        )
        evidence_items.append(
            {
                "tool_name": "fetch_repo_activity_summary",
                "evidence": dict(activity_summary),
            }
        )

    return evidence_items


def evaluate_candidate_with_followup(
    request: ProjectScoutRequest,
    candidate: EnrichedCandidate,
    llm: StructuredOutputModel,
    activity_tool: ToolInvoker = fetch_repo_activity_summary,
) -> RepoEvaluation:
    initial_evaluation = evaluate_candidate(
        request=request,
        candidate=candidate,
        llm=llm,
    )
    followup_evidence = collect_followup_evidence(
        candidate=candidate,
        evaluation=initial_evaluation,
        activity_tool=activity_tool,
    )
    if not followup_evidence:
        return initial_evaluation

    return reevaluate_candidate_with_followup(
        request=request,
        candidate=candidate,
        initial_evaluation=initial_evaluation,
        followup_evidence=followup_evidence,
        llm=llm,
    )
