from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

from ..exceptions import MissingConfigError

load_dotenv()  # Load environment variables from .env file

# LangSmith: LANGCHAIN_TRACING_V2=true, LANGSMITH_API_KEY 설정 시 자동 트레이싱 (콜백 불필요)


# for post-processing
def get_chat_model_anthropic():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise MissingConfigError("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
    return ChatAnthropic(
        model="claude-sonnet-4-5-20250929", api_key=api_key
    )


# for pre-processing
def get_chat_model_google():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise MissingConfigError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=api_key,
        max_output_tokens=65536,
        thinking_budget=0,
    )


# for post-processing (translation)
def get_chat_model_google_translation():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise MissingConfigError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        api_key=api_key,
        max_output_tokens=65536,
        thinking_budget=8192,
    )
