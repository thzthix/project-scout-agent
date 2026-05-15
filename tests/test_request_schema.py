import pathlib
import sys
import unittest

from pydantic import ValidationError

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.schemas.request import ProjectScoutRequest


def build_valid_request_payload() -> dict:
    return {
        "project_name": "Project Scout Agent",
        "project_goal": "I want to build an agent system that finds and evaluates GitHub repositories for my project.",
        "target_repository_description": "Find Python repositories related to agent workflows, tool use, and structured output.",
        "priorities": ["docs_quality", "beginner_friendliness", "activity"],
        "custom_priorities": [],
        "seed_keywords": ["langchain", "langgraph", "agent workflow", "tool calling"],
        "constraints": {
            "preferred_languages": ["python"],
            "license_types": [],
            "must_have_docs": True,
        },
    }


class ProjectScoutRequestSchemaTest(unittest.TestCase):
    def test_valid_request_passes_validation(self) -> None:
        payload = build_valid_request_payload()

        request = ProjectScoutRequest.model_validate(payload)

        self.assertEqual(request.project_name, "Project Scout Agent")
        self.assertTrue(request.constraints.must_have_docs)
        self.assertEqual(request.priorities[0], "docs_quality")

    def test_project_goal_that_is_too_short_fails_validation(self) -> None:
        payload = build_valid_request_payload()
        payload["project_goal"] = "too short"

        with self.assertRaises(ValidationError):
            ProjectScoutRequest.model_validate(payload)

    def test_project_name_that_is_too_long_fails_validation(self) -> None:
        payload = build_valid_request_payload()
        payload["project_name"] = "P" * 81

        with self.assertRaises(ValidationError):
            ProjectScoutRequest.model_validate(payload)

    def test_constraints_defaults_are_applied(self) -> None:
        payload = build_valid_request_payload()
        payload.pop("constraints")

        request = ProjectScoutRequest.model_validate(payload)

        self.assertEqual(request.constraints.preferred_languages, [])
        self.assertEqual(request.constraints.license_types, [])
        self.assertFalse(request.constraints.must_have_docs)

    def test_unknown_priority_fails_validation(self) -> None:
        payload = build_valid_request_payload()
        payload["priorities"] = ["unknown_priority"]

        with self.assertRaises(ValidationError):
            ProjectScoutRequest.model_validate(payload)

    def test_too_many_custom_priorities_fail_validation(self) -> None:
        payload = build_valid_request_payload()
        payload["custom_priorities"] = ["one", "two", "three", "four"]

        with self.assertRaises(ValidationError):
            ProjectScoutRequest.model_validate(payload)

    def test_custom_priority_that_is_too_long_fails_validation(self) -> None:
        payload = build_valid_request_payload()
        payload["custom_priorities"] = ["a" * 61]

        with self.assertRaises(ValidationError):
            ProjectScoutRequest.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
