import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from project_scout_agent.followup_tools import (
    _build_release_names,
    fetch_repo_activity_summary,
)


class FollowUpToolsTest(unittest.TestCase):
    def test_build_release_names_keeps_only_bounded_non_empty_names(self) -> None:
        releases_payload = [
            {"name": "v1.2.0"},
            {"tag_name": "v1.1.0"},
            {"name": ""},
            {"tag_name": "v1.0.0"},
        ]

        release_names = _build_release_names(
            releases_payload,
            max_release_names=3,
        )

        self.assertEqual(release_names, ["v1.2.0", "v1.1.0"])

    def test_fetch_repo_activity_summary_returns_bounded_activity_fields(self) -> None:
        repo_payload = {
            "name": "langgraph",
            "html_url": "https://github.com/langchain-ai/langgraph",
            "stargazers_count": 1000,
            "forks_count": 200,
            "open_issues_count": 12,
            "subscribers_count": 30,
            "updated_at": "2026-05-16T00:00:00Z",
            "pushed_at": "2026-05-16T12:00:00Z",
            "archived": False,
        }
        releases_payload = [
            {"name": "v1.2.0"},
            {"tag_name": "v1.1.0"},
            {"name": "v1.0.0"},
            {"name": "v0.9.0"},
        ]

        with patch(
            "project_scout_agent.followup_tools._load_github_json",
            side_effect=[repo_payload, releases_payload],
        ):
            summary = fetch_repo_activity_summary.invoke(
                {
                    "repo_url": "https://github.com/langchain-ai/langgraph",
                    "max_release_names": 3,
                }
            )

        self.assertEqual(summary["repo_name"], "langgraph")
        self.assertEqual(summary["stars"], 1000)
        self.assertEqual(summary["forks"], 200)
        self.assertEqual(summary["open_issues_count"], 12)
        self.assertEqual(summary["release_names"], ["v1.2.0", "v1.1.0", "v1.0.0"])


if __name__ == "__main__":
    unittest.main()
