from typing import Literal

from pydantic import BaseModel, Field


ScoreValue = Literal[1, 2, 3, 4, 5]
MissingEvidenceTag = Literal[
    "docs_quality",
    "maintenance_signal",
    "example_coverage",
    "production_usage",
    "installation_clarity",
]


class ScoreBreakdown(BaseModel):
    readme_score: ScoreValue = Field(
        description=(
            "README quality score from 1 to 5. Consider clarity of project overview, "
            "setup guidance, usage explanation, and how easy the repository is to understand "
            "from the README alone."
        )
    )
    docs_score: ScoreValue = Field(
        description=(
            "Documentation quality score from 1 to 5. Consider whether an official docs entry "
            "point exists and whether it gives a clear, useful overview for getting started."
        )
    )
    activity_score: ScoreValue = Field(
        description=(
            "Repository activity score from 1 to 5. Consider recent update timing, release "
            "signals, and adoption indicators such as stars or forks."
        )
    )
    example_score: ScoreValue = Field(
        description=(
            "Example coverage score from 1 to 5. Consider whether the repository provides "
            "examples, tutorials, or usage snippets that help a new developer learn by doing."
        )
    )
    overall_score: ScoreValue = Field(
        description=(
            "Overall repository fit score from 1 to 5. Reflect the candidate's usefulness for "
            "the user's project goal after considering all other scores together."
        )
    )


class FollowUpAssessment(BaseModel):
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the current evaluation, from 0.0 to 1.0.",
    )
    needs_followup: bool = Field(
        description="Whether more investigation is recommended before finalizing this candidate."
    )
    missing_evidence: list[MissingEvidenceTag] = Field(
        default_factory=list,
        description="Evidence categories that are still missing or unclear.",
    )
    ambiguity_reason: str = Field(
        max_length=200,
        description=(
            "Short explanation of why the current evaluation is still ambiguous. Keep it brief."
        ),
    )


class RepoEvaluation(BaseModel):
    repo_name: str = Field(description="Repository name.")
    repo_url: str = Field(description="Repository URL.")
    scores: ScoreBreakdown
    recommendation_reason: str = Field(
        max_length=240,
        description=(
            "One or two sentences explaining why this repository is recommended. Keep it brief."
        ),
    )
    evidence_summary: str = Field(
        max_length=240,
        description=(
            "Short summary of the evidence used for the evaluation. Keep it brief and evidence-focused."
        ),
    )
    follow_up: FollowUpAssessment
