from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file


def get_langfuse_handler():
    """Langfuse 콜백 핸들러. LLM invoke 시 config={"callbacks": [get_langfuse_handler()]} 로 전달하면 트레이싱됨.
    LANGFUSE_SECRET_KEY가 없으면 None을 반환해 트레이싱 없이 동작(401 방지)."""
    if not os.getenv("LANGFUSE_SECRET_KEY"):
        return None
    return LangfuseCallbackHandler()


# for post-processing
def get_chat_model_anthropic():
    return ChatAnthropic(
        model="claude-sonnet-4-5-20250929", api_key=os.getenv("ANTHROPIC_API_KEY")
    )


# for pre-processing
def get_chat_model_google():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY")
    )
