from enum import StrEnum

GITHUB_REPOSITORY_SEARCH_URL = "https://api.github.com/search/repositories"


class RequestSection(StrEnum):
    TARGET_REPOSITORY_DESCRIPTION = "target_repository_description"
    SEED_KEYWORDS = "seed_keywords"
    CONSTRAINTS = "constraints"
