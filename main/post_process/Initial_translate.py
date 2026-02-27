# This file handles the initial translation of pre-processed German text into Korean

from langchain_core.messages import SystemMessage, HumanMessage
from .prompts import TRANSLATION_PROMPT
from ..models import models
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


def initial_translate(text, author, book_title):
    from ..exceptions import LLMProviderError, TranslaterAIError

    try:
        chat = models.get_chat_model_anthropic()
        system_prompt = TRANSLATION_PROMPT.format(AUTHOR=author, BOOK_TITLE=book_title)
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=text)]
        response = chat.invoke(messages)
        return response.content
    except TranslaterAIError:
        raise
    except Exception as e:
        raise LLMProviderError("Anthropic 번역 API 호출 실패", cause=e) from e
