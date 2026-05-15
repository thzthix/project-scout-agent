import pathlib
import sys
import unittest

from pydantic import ValidationError

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.schemas.evaluation import RepoEvaluation


def build_valid_payload() -> dict:
    return {
        "repo_name": "example-repo",
        "repo_url": "https://github.com/example/example-repo",
        "scores": {
            "readme_score": 4,
            "docs_score": 3,
            "activity_score": 5,
            "example_score": 4,
            "overall_score": 4,
        },
        "recommendation_reason": "This repository is a strong fit for a beginner-friendly agent project.",
        "evidence_summary": "The README is clear, the docs entry point exists, and the repo shows healthy activity.",
        "follow_up": {
            "confidence": 0.82,
            "needs_followup": False,
            "missing_evidence": [],
            "ambiguity_reason": "",
        },
    }


class RepoEvaluationSchemaTest(unittest.TestCase):
    def test_valid_payload_passes_validation(self) -> None:
        payload = build_valid_payload()

        evaluation = RepoEvaluation.model_validate(payload)

        self.assertEqual(evaluation.scores.overall_score, 4)
        self.assertFalse(evaluation.follow_up.needs_followup)

    def test_score_out_of_range_fails_validation(self) -> None:
        payload = build_valid_payload()
        payload["scores"]["overall_score"] = 6

        with self.assertRaises(ValidationError):
            RepoEvaluation.model_validate(payload)

    def test_unknown_missing_evidence_tag_fails_validation(self) -> None:
        payload = build_valid_payload()
        payload["follow_up"]["missing_evidence"] = ["unknown_signal"]

        with self.assertRaises(ValidationError):
            RepoEvaluation.model_validate(payload)

    def test_overlong_recommendation_reason_fails_validation(self) -> None:
        payload = build_valid_payload()
        payload["recommendation_reason"] = "a" * 241

        with self.assertRaises(ValidationError):
            RepoEvaluation.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
