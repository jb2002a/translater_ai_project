from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

# LangSmith: LANGCHAIN_TRACING_V2=true, LANGSMITH_API_KEY 설정 시 자동 트레이싱 (콜백 불필요)


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
