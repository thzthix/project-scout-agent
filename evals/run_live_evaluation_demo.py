from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from project_scout_agent.enrichment import enrich_candidates
from project_scout_agent.followup import evaluate_candidate_with_followup
from project_scout_agent.llm import create_evaluator_llm
from project_scout_agent.query_builder import build_query_seeds
from project_scout_agent.reranking import build_reranking_artifact, rerank_candidates
from project_scout_agent.schemas.request import ProjectScoutRequest
from project_scout_agent.search import search_repositories


def _build_demo_request() -> ProjectScoutRequest:
    return ProjectScoutRequest.model_validate(
        {
            "project_name": "Project Scout Agent",
            "project_goal": (
                "I want to build a production-friendly Python agent system with "
                "strong typing and structured outputs."
            ),
            "target_repository_description": (
                "python agent workflow reference repository"
            ),
            "priorities": [
                "docs_quality",
                "activity",
                "example_coverage",
            ],
            "custom_priorities": [],
            "seed_keywords": ["langchain", "langgraph", "structured output"],
            "constraints": {
                "preferred_languages": ["python"],
                "license_types": [],
                "must_have_docs": True,
            },
        }
    )


def main() -> None:
    request = _build_demo_request()
    llm = create_evaluator_llm()

    query_plan = build_query_seeds(request)
    search_results = search_repositories(
        query_plan=query_plan,
        per_page=5,
    )
    candidates = [
        candidate
        for search_result in search_results
        for candidate in search_result.candidates
    ]
    if not candidates:
        raise RuntimeError("검색 결과가 없어 live evaluation demo를 진행할 수 없습니다.")

    enriched_candidates = enrich_candidates(candidates)
    reranked_candidates = rerank_candidates(
        request=request,
        candidates=enriched_candidates,
    )
    top_candidate = reranked_candidates[0]
    reranking_artifact = build_reranking_artifact(
        request=request,
        candidates=reranked_candidates[:5],
    )
    final_evaluation = evaluate_candidate_with_followup(
        request=request,
        candidate=top_candidate,
        llm=llm,
    )

    print("=== Query Plan ===")
    print(json.dumps(query_plan.model_dump(), ensure_ascii=False, indent=2))
    print("\n=== Top Reranking Artifact ===")
    print(json.dumps(reranking_artifact[:3], ensure_ascii=False, indent=2))
    print("\n=== Final Evaluation ===")
    print(json.dumps(final_evaluation.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
