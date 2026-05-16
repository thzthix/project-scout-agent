from __future__ import annotations

from project_scout_agent.config import get_gemini_model, get_google_api_key


def create_evaluator_llm():
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError as error:
        raise RuntimeError(
            "Gemini evaluator를 사용하려면 langchain-google-genai 패키지가 필요합니다."
        ) from error

    return ChatGoogleGenerativeAI(
        model=get_gemini_model(),
        google_api_key=get_google_api_key(),
        temperature=0,
    )
