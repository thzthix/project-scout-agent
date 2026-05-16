from pydantic import BaseModel, Field

from project_scout_agent.schemas.search_candidate import SearchCandidate


class EnrichedCandidate(BaseModel):
    candidate: SearchCandidate
    readme_excerpt: str = Field(
        default="",
        max_length=8000,
        description="Short README excerpt used as evaluation context.",
    )
    topics: list[str] = Field(
        default_factory=list,
        description="GitHub topics attached to the repository.",
    )
    primary_language: str = Field(
        default="",
        max_length=100,
        description="Primary language reported by GitHub.",
    )
    license_name: str = Field(
        default="",
        max_length=200,
        description="Repository license name when available.",
    )
    homepage_url: str = Field(
        default="",
        max_length=500,
        description="Repository homepage URL when available.",
    )
