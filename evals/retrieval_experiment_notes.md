# Retrieval Experiment Notes

## Goal

Build a deterministic retrieval baseline that gathers useful GitHub repository candidates for later AI evaluation.

The retrieval stage is not expected to identify the final canonical repository by itself.
Its role is to gather a broad but still meaningful candidate pool that a later AI evaluation step can judge.

## Current Best Retrieval Strategy

- Query A: `target_repository_description`
- Query B: `seed_keywords + preferred_languages`
- Retrieval qualifier for experiments: `in:name,description`
- Candidate generation: union of GitHub `best match` and `sort=updated`
- Post-processing:
  - URL-based dedup
  - near-duplicate pruning by normalized name/description signature
  - lightweight reranking by:
    - repo name match
    - lexical overlap
    - authority signals (`stars`, `forks`, `updated_at`)

## Why This Strategy Was Chosen

Early experiments showed that:

- `constraints` as a standalone query was too broad and returned many generic documentation repositories
- `must_have_docs` as a query term over-constrained retrieval and often led to zero results
- directly concatenating description and keywords also over-constrained retrieval

So the retrieval baseline was simplified to:

- keep project intent through `target_repository_description`
- keep the strongest lexical signal through `seed_keywords`
- keep only `preferred_languages` as a retrieval modifier
- move stricter quality signals such as docs/license toward later evaluation stages

## Judged Eval Setup

A small judged eval set was created in [judged_queries.json](/Users/seoha/project-scout-agent/evals/judged_queries.json:1).

It currently contains 5 briefs:

- python agent workflow
- python multi-agent framework
- python rag chatbot framework
- python structured agent framework
- java spring ai framework

Each brief contains:

- a full `ProjectScoutRequest`
- a small list of relevant repositories expressed as exact `owner/repo`

## Metrics Used

### Exact Metrics

- `Precision@5`
- `Recall@10`

These remained `0.0` across the tested retrieval variants.

### Diagnostic Metrics

Because exact judged hits stayed at zero, additional diagnostic metrics were introduced:

- `best_name_similarity_at_10`
  - measures the best token-level similarity between any top-10 candidate repo name and the judged relevant repo names
- `unique_candidate_coverage_at_10`
  - counts how many distinct candidates remain in the top 10 after union and pruning

These helped distinguish:

- completely wrong retrieval
- retrieval that is close to the right ecosystem but not yet exact

## Main Experiment Loop

### Baseline

- description-only query produced very few results
- seed-keywords query produced richer but noisy results
- constraints-only query produced many irrelevant documentation-oriented repos

### Experiments Tried

1. `description + keywords`
- over-constrained retrieval
- often produced zero results

2. `keywords + all constraints`
- over-constrained retrieval
- often produced zero results

3. `preferred_languages` only as retrieval modifier
- much safer than using docs/license in query text

4. `sort=stars`
- useful as a diagnostic
- did not improve exact judged hits

5. `in:name,description,readme`
- over-surfaced `awesome-*` and list-style repositories
- rejected

6. `topic:` query suffix
- over-constrained retrieval
- often produced empty result sets
- rejected

7. authority reranking
- improved the ordering of “nearby” candidates
- still did not produce exact judged hits

8. `best match + updated` union
- helped widen the candidate pool while keeping project-style repos in the mix

9. quoted identity query family
- slightly widened candidate coverage
- did not materially improve exact metrics

## Best Current Result

The best current experimental direction is:

- `in:name,description`
- `best match + updated` union
- dedup + near-duplicate pruning
- lexical + authority rerank

With this setup:

- `mean_precision_at_5 = 0.0`
- `mean_recall_at_10 = 0.0`
- `mean_best_name_similarity_at_10 = 0.2854`
- `mean_unique_candidate_coverage_at_10 = 8.6`

## Interpretation

The retrieval stage is not yet reliably surfacing the exact canonical repositories in top-k.

However, it is increasingly surfacing repositories that are close in name, ecosystem, and use case.

This suggests:

- retrieval is good enough to produce a useful candidate pool
- the next bottleneck is not pure retrieval
- the next bottleneck is richer metadata enrichment and AI-based candidate evaluation

## Portfolio Framing

This experiment sequence supports the following design story:

- started with a simple deterministic lexical baseline
- measured failure modes with a small judged eval set
- separated broad/noisy constraints from useful retrieval signals
- iterated on candidate generation and reranking without hardcoded owner/repo rules
- concluded that retrieval should optimize for candidate pool quality, not exact final selection
- reserved final precision for a later AI evaluation stage with richer metadata
