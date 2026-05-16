from pydantic import BaseModel, Field

from project_scout_agent.constants import RequestSection


class QuerySeed(BaseModel):
    query: str = Field(
        min_length=3,
        max_length=200,
        description="Search query text generated from the structured project request.",
    )
    source: RequestSection = Field(
        description="Primary input source that produced this query seed."
    )
    used_fields: list[str] = Field(
        min_length=1,
        description="Request fields that were used to construct this query seed.",
    )


class QueryPlan(BaseModel):
    query_seeds: list[QuerySeed] = Field(
        min_length=1,
        description="Structured query seeds created from the project request.",
    )
