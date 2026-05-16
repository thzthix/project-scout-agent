from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from project_scout_agent.schemas.enrichment import EnrichedCandidate
from project_scout_agent.schemas.request import ProjectScoutRequest


def _normalize_text(value: str) -> str:
    return value.strip().lower()


def _normalize_language(value: str) -> str:
    return _normalize_text(value)


def _preferred_language_match(
    request: ProjectScoutRequest,
    candidate: EnrichedCandidate,
) -> bool:
    preferred_languages = {
        _normalize_language(language)
        for language in request.constraints.preferred_languages
        if language.strip()
    }
    if not preferred_languages:
        return False

    candidate_language = _normalize_language(candidate.primary_language)
    return candidate_language in preferred_languages


def _freshness_score(updated_at: str) -> float:
    updated_datetime = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    age_in_days = max((datetime.now(UTC) - updated_datetime).days, 0)
    return -math.log10(age_in_days + 1)


def _authority_score(candidate: EnrichedCandidate) -> float:
    star_score = math.log10(candidate.candidate.stars + 1)
    fork_score = math.log10(candidate.candidate.forks + 1)
    freshness_score = _freshness_score(candidate.candidate.updated_at)
    return star_score + fork_score + freshness_score


def build_reranking_signals(
    request: ProjectScoutRequest,
    candidate: EnrichedCandidate,
) -> dict[str, Any]:
    language_match = _preferred_language_match(
        request=request,
        candidate=candidate,
    )
    authority_score = _authority_score(candidate)

    return {
        "language_match": language_match,
        "stars": candidate.candidate.stars,
        "forks": candidate.candidate.forks,
        "updated_at": candidate.candidate.updated_at,
        "authority_score": authority_score,
    }


def score_candidate_for_reranking(
    request: ProjectScoutRequest,
    candidate: EnrichedCandidate,
) -> tuple[int, float]:
    signals = build_reranking_signals(
        request=request,
        candidate=candidate,
    )
    return int(signals["language_match"]), float(signals["authority_score"])


def rerank_candidates(
    request: ProjectScoutRequest,
    candidates: list[EnrichedCandidate],
) -> list[EnrichedCandidate]:
    return sorted(
        candidates,
        key=lambda candidate: score_candidate_for_reranking(
            request=request,
            candidate=candidate,
        ),
        reverse=True,
    )


def build_reranking_artifact(
    request: ProjectScoutRequest,
    candidates: list[EnrichedCandidate],
) -> list[dict[str, Any]]:
    reranked_candidates = rerank_candidates(
        request=request,
        candidates=candidates,
    )
    artifact: list[dict[str, Any]] = []

    for rank, candidate in enumerate(reranked_candidates, start=1):
        signals = build_reranking_signals(
            request=request,
            candidate=candidate,
        )
        artifact.append(
            {
                "rank": rank,
                "repo_name": candidate.candidate.repo_name,
                "repo_url": candidate.candidate.repo_url,
                "score": {
                    "language_match": int(signals["language_match"]),
                    "authority_score": round(float(signals["authority_score"]), 4),
                },
                "signals": signals,
            }
        )

    return artifact
