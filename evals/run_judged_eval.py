from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path

from project_scout_agent.query_builder import build_query_seeds
from project_scout_agent.schemas.query_seed import QueryPlan
from project_scout_agent.schemas.request import ProjectScoutRequest
from project_scout_agent.schemas.search_candidate import SearchCandidate, SearchResultForSeed
from project_scout_agent.search import search_repositories_for_seed


EVAL_PATH = Path(__file__).with_name("judged_queries.json")
CACHE_DIR = Path(__file__).with_name("cache")
QUERY_SUFFIX = " in:name,description"


def _load_judged_queries() -> list[dict]:
    with EVAL_PATH.open() as eval_file:
        return json.load(eval_file)


def _build_cache_key(query: str, sort_by: str | None, per_page: int) -> str:
    safe_query = query.replace("/", "_").replace(" ", "_")
    safe_sort_by = sort_by or "best_match"
    return f"{safe_query}__sort_{safe_sort_by}__per_page_{per_page}.json"


def _load_cached_seed_result(
    query_seed,
    sort_by: str | None,
    per_page: int,
) -> SearchResultForSeed | None:
    cache_path = CACHE_DIR / _build_cache_key(query_seed.query, sort_by, per_page)
    if not cache_path.exists():
        return None

    with cache_path.open() as cache_file:
        payload = json.load(cache_file)

    return SearchResultForSeed(
        query_seed=query_seed,
        candidates=[
            SearchCandidate.model_validate(candidate_payload)
            for candidate_payload in payload["candidates"]
        ],
    )


def _save_cached_seed_result(
    search_result: SearchResultForSeed,
    sort_by: str | None,
    per_page: int,
) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / _build_cache_key(search_result.query_seed.query, sort_by, per_page)
    with cache_path.open("w") as cache_file:
        json.dump(
            {
                "candidates": [
                    candidate.model_dump()
                    for candidate in search_result.candidates
                ]
            },
            cache_file,
            indent=2,
        )


def _search_repositories_with_cache(
    query_plan: QueryPlan,
    sort_by: str | None = None,
    per_page: int = 10,
) -> list[SearchResultForSeed]:
    search_results: list[SearchResultForSeed] = []

    for query_seed in query_plan.query_seeds:
        cached_search_result = _load_cached_seed_result(query_seed, sort_by, per_page)
        if cached_search_result is not None:
            search_results.append(cached_search_result)
            continue

        fetched_search_result = search_repositories_for_seed(
            query_seed=query_seed,
            per_page=per_page,
            sort_by=sort_by,
        )
        _save_cached_seed_result(fetched_search_result, sort_by, per_page)
        search_results.append(fetched_search_result)

    return search_results


def _apply_query_suffix(query_plan: QueryPlan, query_suffix: str) -> QueryPlan:
    if not query_suffix:
        return query_plan

    return QueryPlan(
        query_seeds=[
            query_seed.model_copy(
                update={"query": f"{query_seed.query}{query_suffix}"}
            )
            for query_seed in query_plan.query_seeds
        ]
    )


def _dedup_candidates(search_results: list) -> list:
    deduped_candidates: list = []
    seen_repo_urls: set[str] = set()

    for search_result in search_results:
        for candidate in search_result.candidates:
            if candidate.repo_url in seen_repo_urls:
                continue
            seen_repo_urls.add(candidate.repo_url)
            deduped_candidates.append(candidate)

    return deduped_candidates


def _dedup_candidate_list(candidates: list) -> list:
    deduped_candidates: list = []
    seen_repo_urls: set[str] = set()

    for candidate in candidates:
        if candidate.repo_url in seen_repo_urls:
            continue
        seen_repo_urls.add(candidate.repo_url)
        deduped_candidates.append(candidate)

    return deduped_candidates


def _normalized_candidate_signature(candidate: SearchCandidate) -> str:
    normalized_name = re.sub(r"[^a-z0-9]+", " ", candidate.repo_name.lower()).strip()
    normalized_description = re.sub(
        r"[^a-z0-9]+",
        " ",
        candidate.description.lower(),
    ).strip()
    return f"{normalized_name}|{normalized_description}"


def _near_duplicate_prune_candidates(candidates: list[SearchCandidate]) -> list[SearchCandidate]:
    pruned_candidates: list[SearchCandidate] = []
    seen_signatures: set[str] = set()

    for candidate in candidates:
        signature = _normalized_candidate_signature(candidate)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        pruned_candidates.append(candidate)

    return pruned_candidates


def _extract_repo_full_name(repo_url: str) -> str:
    return "/".join(repo_url.rstrip("/").split("/")[-2:])


def _extract_repo_owner(repo_url: str) -> str:
    return repo_url.rstrip("/").split("/")[-2]


def _repo_identity_tokens(repo_full_name: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", repo_full_name.lower()) if token}


def _tokenize(text: str) -> set[str]:
    return {token for token in text.lower().split() if token}


def _build_query_tokens(search_results: list) -> set[str]:
    query_tokens: set[str] = set()

    for search_result in search_results:
        query_tokens.update(_tokenize(search_result.query_seed.query))

    return query_tokens


def _rerank_candidates(candidates: list, query_tokens: set[str]) -> list:
    def candidate_score(candidate) -> tuple[int, int, float]:
        owner_name = _extract_repo_owner(candidate.repo_url)
        candidate_text = f"{owner_name} {candidate.repo_name} {candidate.description}"
        candidate_tokens = _tokenize(candidate_text)
        token_overlap = len(candidate_tokens & query_tokens)
        name_exactness = sum(
            1 for token in query_tokens if token and token in candidate.repo_name.lower()
        )
        updated_at = datetime.fromisoformat(candidate.updated_at.replace("Z", "+00:00"))
        age_in_days = max((datetime.now(updated_at.tzinfo) - updated_at).days, 0)
        star_score = math.log10(candidate.stars + 1)
        fork_score = math.log10(candidate.forks + 1)
        freshness_score = -math.log10(age_in_days + 1)
        authority_score = star_score + fork_score + freshness_score
        return name_exactness, token_overlap, authority_score

    return sorted(
        candidates,
        key=candidate_score,
        reverse=True,
    )


def _precision_at_k(
    candidate_full_names: list[str],
    relevant_full_names: set[str],
    k: int,
) -> float:
    top_k = candidate_full_names[:k]
    if not top_k:
        return 0.0

    matched_count = sum(
        1 for candidate_full_name in top_k if candidate_full_name in relevant_full_names
    )
    return matched_count / len(top_k)


def _recall_at_k(
    candidate_full_names: list[str],
    relevant_full_names: set[str],
    k: int,
) -> float:
    if not relevant_full_names:
        return 0.0

    top_k = set(candidate_full_names[:k])
    matched_count = len(top_k & relevant_full_names)
    return matched_count / len(relevant_full_names)


def _best_name_similarity_at_k(
    candidate_full_names: list[str],
    relevant_full_names: set[str],
    k: int,
) -> float:
    top_k = candidate_full_names[:k]
    if not top_k or not relevant_full_names:
        return 0.0

    best_similarity = 0.0
    for candidate_full_name in top_k:
        candidate_tokens = _repo_identity_tokens(candidate_full_name)
        for relevant_full_name in relevant_full_names:
            relevant_tokens = _repo_identity_tokens(relevant_full_name)
            union = candidate_tokens | relevant_tokens
            if not union:
                continue
            similarity = len(candidate_tokens & relevant_tokens) / len(union)
            best_similarity = max(best_similarity, similarity)

    return best_similarity


def _unique_candidate_coverage_at_k(candidate_full_names: list[str], k: int) -> int:
    return len(set(candidate_full_names[:k]))


def run_judged_eval() -> dict:
    judged_queries = _load_judged_queries()
    brief_results: list[dict] = []

    for judged_query in judged_queries:
        request = ProjectScoutRequest.model_validate(judged_query["request"])
        query_plan = _apply_query_suffix(
            build_query_seeds(request),
            QUERY_SUFFIX,
        )
        best_match_results = _search_repositories_with_cache(query_plan)
        updated_sorted_results = _search_repositories_with_cache(query_plan, sort_by="updated")
        search_results = [*best_match_results, *updated_sorted_results]
        deduped_candidates = _dedup_candidate_list(
            _dedup_candidates(best_match_results) + _dedup_candidates(updated_sorted_results)
        )
        pruned_candidates = _near_duplicate_prune_candidates(deduped_candidates)
        raw_candidate_full_names = [
            _extract_repo_full_name(candidate.repo_url)
            for candidate in pruned_candidates
        ]
        query_tokens = _build_query_tokens(search_results)
        reranked_candidates = _rerank_candidates(pruned_candidates, query_tokens)
        reranked_candidate_full_names = [
            _extract_repo_full_name(candidate.repo_url)
            for candidate in reranked_candidates
        ]
        relevant_full_names = {
            relevant_repo["full_name"]
            for relevant_repo in judged_query["relevant_repositories"]
        }
        matched_repos = sorted(set(reranked_candidate_full_names) & relevant_full_names)

        brief_results.append(
            {
                "brief_id": judged_query["brief_id"],
                "precision_at_5": _precision_at_k(
                    reranked_candidate_full_names,
                    relevant_full_names,
                    5,
                ),
                "recall_at_10": _recall_at_k(
                    reranked_candidate_full_names,
                    relevant_full_names,
                    10,
                ),
                "best_name_similarity_at_10": _best_name_similarity_at_k(
                    reranked_candidate_full_names,
                    relevant_full_names,
                    10,
                ),
                "unique_candidate_coverage_at_10": _unique_candidate_coverage_at_k(
                    reranked_candidate_full_names,
                    10,
                ),
                "raw_top_candidate_full_names": raw_candidate_full_names[:10],
                "reranked_top_candidate_full_names": reranked_candidate_full_names[:10],
                "matched_repositories": matched_repos,
            }
        )

    mean_precision_at_5 = sum(
        brief_result["precision_at_5"] for brief_result in brief_results
    ) / len(brief_results)
    mean_recall_at_10 = sum(
        brief_result["recall_at_10"] for brief_result in brief_results
    ) / len(brief_results)
    mean_best_name_similarity_at_10 = sum(
        brief_result["best_name_similarity_at_10"] for brief_result in brief_results
    ) / len(brief_results)
    mean_unique_candidate_coverage_at_10 = sum(
        brief_result["unique_candidate_coverage_at_10"] for brief_result in brief_results
    ) / len(brief_results)

    return {
        "brief_results": brief_results,
        "mean_precision_at_5": mean_precision_at_5,
        "mean_recall_at_10": mean_recall_at_10,
        "mean_best_name_similarity_at_10": mean_best_name_similarity_at_10,
        "mean_unique_candidate_coverage_at_10": mean_unique_candidate_coverage_at_10,
    }


if __name__ == "__main__":
    print(json.dumps(run_judged_eval(), indent=2))
