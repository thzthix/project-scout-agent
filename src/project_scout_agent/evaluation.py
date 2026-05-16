from __future__ import annotations

from project_scout_agent.schemas.enrichment import EnrichedCandidate
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
