from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file


# for post-processing
def get_chat_model_anthropic():
    return ChatAnthropic(
        model="claude-sonnet-4-5-20250929", api_key=os.getenv("ANTHROPIC_API_KEY")
    )


# for pre-processing
def get_chat_model_google():
    chat = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro", api_key=os.getenv("GOOGLE_API_KEY")
    )
