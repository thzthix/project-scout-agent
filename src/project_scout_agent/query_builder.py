from project_scout_agent.constants import RequestSection
from project_scout_agent.schemas.query_seed import QueryPlan, QuerySeed
from project_scout_agent.schemas.request import ProjectScoutRequest

def _build_constraint_tokens(request: ProjectScoutRequest) -> tuple[list[str], list[str]]:
    constraint_tokens: list[str] = []
    used_constraint_fields: list[str] = []

    if request.constraints.preferred_languages:
        constraint_tokens.extend(
            language.strip()
            for language in request.constraints.preferred_languages
            if language.strip()
        )
        used_constraint_fields.append("constraints.preferred_languages")

    return constraint_tokens, used_constraint_fields


def _build_target_description_seed(
    request: ProjectScoutRequest,
) -> QuerySeed | None:
    target_description = request.target_repository_description.strip()
    if target_description:
        return QuerySeed(
            query=target_description,
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
            constraint_tokens, used_constraint_fields = _build_constraint_tokens(request)
            if constraint_tokens:
                seed_keywords_query = " ".join([seed_keywords_query, *constraint_tokens])

            return QuerySeed(
                query=seed_keywords_query,
                source=RequestSection.SEED_KEYWORDS,
                used_fields=["seed_keywords", *used_constraint_fields],
            )
    return None


def _build_constraints_seed(request: ProjectScoutRequest) -> QuerySeed | None:
    return None


def build_query_seeds(request: ProjectScoutRequest) -> QueryPlan:
    candidate_seeds = [
        _build_target_description_seed(request),
        _build_seed_keywords_seed(request),
        _build_constraints_seed(request),
    ]

    query_seeds = [query_seed for query_seed in candidate_seeds if query_seed is not None]

    return QueryPlan(query_seeds=query_seeds)
