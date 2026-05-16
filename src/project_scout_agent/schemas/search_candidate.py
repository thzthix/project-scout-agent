from pydantic import BaseModel, Field

from project_scout_agent.schemas.query_seed import QuerySeed


class SearchCandidate(BaseModel):
    repo_name: str = Field(
        min_length=1,
        max_length=120,
        description="Repository name returned from search.",
    )
    repo_url: str = Field(
        min_length=1,
        max_length=300,
        description="Repository URL returned from search.",
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Short repository description returned from search.",
    )
    stars: int = Field(
        ge=0,
        description="Repository star count returned from search.",
    )
    forks: int = Field(
        ge=0,
        description="Repository fork count returned from search.",
    )
    updated_at: str = Field(
        min_length=1,
        max_length=50,
        description="Repository updated timestamp returned from search.",
    )


class SearchResultForSeed(BaseModel):
    query_seed: QuerySeed = Field(
        description="Query seed used to run this search execution."
    )
    candidates: list[SearchCandidate] = Field(
        default_factory=list,
        description="Repository candidates returned for the query seed.",
    )
