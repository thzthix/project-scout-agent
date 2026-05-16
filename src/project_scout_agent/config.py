import os

from dotenv import load_dotenv

load_dotenv()


def get_github_token() -> str:
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    if not github_token:
        raise ValueError("GitHub 검색을 실행하려면 GITHUB_TOKEN이 필요합니다.")
    return github_token
