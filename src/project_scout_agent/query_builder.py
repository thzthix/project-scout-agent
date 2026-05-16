from project_scout_agent.constants import RequestSection
from project_scout_agent.schemas.query_seed import QueryPlan, QuerySeed
from project_scout_agent.schemas.request import ProjectScoutRequest


def _build_target_description_seed(
    request: ProjectScoutRequest,
) -> QuerySeed | None:
    target_description_query = request.target_repository_description.strip()
    if target_description_query:
        return QuerySeed(
            query=target_description_query,
            source=RequestSection.TARGET_REPOSITORY_DESCRIPTION,
            used_fields=["target_repository_description"],
        )
    return None


def _build_seed_keywords_seed(request: ProjectScoutRequest) -> QuerySeed | None:
    if request.seed_keywords:
        seed_keywords_query = " ".join(
            keyword.strip() for keyword in request.seed_keywords if keyword.strip()
        )
        if seed_keywords_query:
            return QuerySeed(
                query=seed_keywords_query,
                source=RequestSection.SEED_KEYWORDS,
                used_fields=["seed_keywords"],
            )
    return None


def _build_constraints_seed(request: ProjectScoutRequest) -> QuerySeed | None:
    constraint_tokens: list[str] = []
    used_constraint_fields: list[str] = []

    if request.constraints.preferred_languages:
        constraint_tokens.extend(
            language.strip()
            for language in request.constraints.preferred_languages
            if language.strip()
        )
        used_constraint_fields.append("constraints.preferred_languages")

    if request.constraints.license_types:
        constraint_tokens.extend(
            license_type.strip()
            for license_type in request.constraints.license_types
            if license_type.strip()
        )
        used_constraint_fields.append("constraints.license_types")

    if request.constraints.must_have_docs:
        constraint_tokens.append("documentation")
        used_constraint_fields.append("constraints.must_have_docs")

    constraint_query = " ".join(constraint_tokens)
    if constraint_query:
        return QuerySeed(
            query=constraint_query,
            source=RequestSection.CONSTRAINTS,
            used_fields=used_constraint_fields,
        )
    return None


def build_query_seeds(request: ProjectScoutRequest) -> QueryPlan:
    candidate_seeds = [
        _build_target_description_seed(request),
        _build_seed_keywords_seed(request),
        _build_constraints_seed(request),
    ]

    query_seeds = [query_seed for query_seed in candidate_seeds if query_seed is not None]

    return QueryPlan(query_seeds=query_seeds)
