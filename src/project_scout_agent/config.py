import os

from dotenv import load_dotenv

load_dotenv()


def get_github_token() -> str:
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    if not github_token:
        raise ValueError("GitHub 검색을 실행하려면 GITHUB_TOKEN이 필요합니다.")
    return github_token


def get_openai_api_key() -> str:
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_api_key:
        raise ValueError("OpenAI 평가를 실행하려면 OPENAI_API_KEY가 필요합니다.")
    return openai_api_key


def get_openai_model() -> str:
    openai_model = os.getenv("OPENAI_MODEL", "").strip()
    if not openai_model:
        raise ValueError("OpenAI 평가를 실행하려면 OPENAI_MODEL이 필요합니다.")
    return openai_model


def get_google_api_key() -> str:
    google_api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not google_api_key:
        raise ValueError("Gemini 평가를 실행하려면 GOOGLE_API_KEY가 필요합니다.")
    return google_api_key


def get_gemini_model() -> str:
    gemini_model = os.getenv("GEMINI_MODEL", "").strip()
    if not gemini_model:
        raise ValueError("Gemini 평가를 실행하려면 GEMINI_MODEL이 필요합니다.")
    return gemini_model
