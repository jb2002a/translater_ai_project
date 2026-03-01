# This file handles the initial translation of pre-processed German text into Korean

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from ...exceptions import LLMProviderError, TranslaterAIError
from ...models import models
from ..prompts.prompts import TRANSLATION_PROMPT


class TranslationResult(BaseModel):
    """번역 결과의 구조화된 출력 형식"""

    pk: int = Field(description="번역 대상 문장의 고유 식별자(primary key)")
    text: str = Field(description="번역된 한국어 텍스트")


def initial_translate(
    pk: int, text: str, author: str, book_title: str
) -> TranslationResult:
    """
    전처리된 독일어 문장(또는 배치)을 한국어로 번역.
    author, book_title은 시스템 프롬프트에 반영된다.
    pk는 번역 결과와 함께 구조화된 출력으로 반환된다.
    """
    try:
        chat = models.get_chat_model_anthropic()
        structured_chat = chat.with_structured_output(TranslationResult)
        system_prompt = TRANSLATION_PROMPT.format(AUTHOR=author, BOOK_TITLE=book_title)
        human_message = f"pk: {pk}\n\n[번역 대상 텍스트]\n{text}"
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message),
        ]
        result = structured_chat.invoke(messages)
        return result
    except TranslaterAIError:
        raise
    except Exception as e:
        raise LLMProviderError("Anthropic 번역 API 호출 실패", cause=e) from e
