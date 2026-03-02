# This file handles the initial translation of pre-processed German text into Korean

from typing import List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ...exceptions import LLMProviderError, TranslaterAIError
from ...models import models
from ..prompts.prompts import TRANSLATION_PROMPT


class TranslationResult(BaseModel):
    """번역 결과의 구조화된 출력 형식"""

    pk: int = Field(description="번역 대상 문장의 고유 식별자(primary key)")
    text: str = Field(description="번역된 한국어 텍스트")


class BatchTranslationResult(BaseModel):
    """여러 문장의 번역 결과 (입력 순서 유지)"""

    translations: List[TranslationResult] = Field(
        description="번역 결과 목록. 입력 순서와 동일하게 반환한다."
    )


def initial_translate_batch(
    items: List[Tuple[int, str]], author: str, book_title: str
) -> List[Tuple[int, str]]:
    """
    전처리된 독일어 문장 리스트를 한국어로 일괄 번역.
    author, book_title은 시스템 프롬프트에 반영된다.
    한 번의 LLM 호출로 전체 리스트를 번역한다.
    """
    if not items:
        return []

    try:
        chat = models.get_chat_model_google_translation()
        structured_chat = chat.with_structured_output(BatchTranslationResult)
        system_prompt = TRANSLATION_PROMPT.format(AUTHOR=author, BOOK_TITLE=book_title)
        parts = []
        for pk, text in items:
            parts.append(f"---\npk: {pk}\n\n[텍스트]\n{text}")
        human_message = "\n\n".join(parts)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_message),
        ]
        result = structured_chat.invoke(messages)
        return [(t.pk, t.text) for t in result.translations]
    except TranslaterAIError:
        raise
    except Exception as e:
        raise LLMProviderError("Gemini 번역 API 호출 실패", cause=e) from e
