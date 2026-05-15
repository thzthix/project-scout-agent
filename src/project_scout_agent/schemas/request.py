from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


KnownPriority = Literal[
    "docs_quality",
    "beginner_friendliness",
    "activity",
    "example_coverage",
    "production_readiness",
]


class SearchConstraints(BaseModel):
    preferred_languages: list[str] = Field(
        default_factory=list,
        description="Preferred programming languages for candidate repositories.",
    )
    license_types: list[str] = Field(
        default_factory=list,
        description=(
            "Optional accepted license types for candidate repositories. This field can stay empty "
            "when the user has no license preference. Later UI or workflow layers may normalize "
            "friendly user selections into standard license identifiers."
        ),
    )
    must_have_docs: bool = Field(
        default=False,
        description="Whether candidate repositories must have a documentation entry point.",
    )


class ProjectScoutRequest(BaseModel):
    project_name: str = Field(
        min_length=1,
        max_length=80,
        description="Short name of the user's project.",
    )
    project_goal: str = Field(
        min_length=10,
        max_length=500,
        description=(
            "What the user wants to build and why. Keep enough detail to guide repository search."
        ),
    )
    target_repository_description: str = Field(
        min_length=10,
        max_length=300,
        description=(
            "What kind of repositories the system should search for, such as framework type, "
            "reference implementation style, or technical focus."
        ),
    )
    priorities: list[KnownPriority] = Field(
        default_factory=list,
        description=(
            "Ordered known evaluation priorities such as docs_quality or beginner_friendliness."
        ),
    )
    custom_priorities: list[Annotated[str, StringConstraints(min_length=1, max_length=60)]] = Field(
        default_factory=list,
        max_length=3,
        description=(
            "Optional custom evaluation priorities when the built-in priority options are not enough."
        ),
    )
    seed_keywords: list[str] = Field(
        default_factory=list,
        description="Initial search keywords used to guide repository discovery.",
    )
    constraints: SearchConstraints = Field(
        default_factory=SearchConstraints,
        description="Structured constraints that narrow repository search.",
    )
