# This file handles the initial translation of pre-processed German text into Korean

from langchain_core.messages import SystemMessage, HumanMessage

from ...exceptions import LLMProviderError, TranslaterAIError
from ...models import models
from ..prompts.prompts import TRANSLATION_PROMPT


def initial_translate(text: str, author: str, book_title: str) -> str:
    """
    전처리된 독일어 문장(또는 배치)을 한국어로 번역.
    author, book_title은 시스템 프롬프트에 반영된다.
    """
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
