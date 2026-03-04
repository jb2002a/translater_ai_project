# This file handles the initial translation of pre-processed German text into Korean

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

import langsmith as ls
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ...exceptions import LLMProviderError, TranslaterAIError
from ...models import models
from ..prompts.prompts import TRANSLATION_PROMPT

logger = logging.getLogger(__name__)

# 병렬 번역 시 최대 동시 LLM 호출 수 (청크 2개 / 워커 2개)
_MAX_PARALLEL_WORKERS = 2
_MIN_REQUEST_INTERVAL = 1.0

_rate_lock = threading.Lock()
_last_request_time: float = 0.0


def _throttle() -> None:
    """API rate limit 고려: 요청 간 최소 간격 유지."""
    global _last_request_time
    with _rate_lock:
        now = time.monotonic()
        elapsed = now - _last_request_time
        if elapsed < _MIN_REQUEST_INTERVAL:
            time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
        _last_request_time = time.monotonic()


class TranslationResult(BaseModel):
    """번역 결과의 구조화된 출력 형식"""

    pk: int = Field(description="번역 대상 문장의 고유 식별자(primary key)")
    text: str = Field(description="번역된 한국어 텍스트")


class BatchTranslationResult(BaseModel):
    """여러 문장의 번역 결과 (입력 순서 유지)"""

    translations: List[TranslationResult] = Field(
        description="번역 결과 목록. 입력 순서와 동일하게 반환한다."
    )


def _translate_single_chunk(
    chunk: List[Tuple[int, str]], author: str, book_title: str
) -> List[Tuple[int, str]]:
    """단일 청크를 한 번의 LLM 호출로 번역."""
    if not chunk:
        return []
    _throttle()
    chat = models.get_chat_model_anthropic()
    structured_chat = chat.with_structured_output(BatchTranslationResult)
    system_prompt = TRANSLATION_PROMPT.format(AUTHOR=author, BOOK_TITLE=book_title)
    parts = [f"---\npk: {pk}\n\n[텍스트]\n{text}" for pk, text in chunk]
    human_message = "\n\n".join(parts)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message),
    ]
    pk_range = f"{chunk[0][0]}..{chunk[-1][0]}" if len(chunk) > 1 else str(chunk[0][0])
    logger.info("initial_translate: 청크 요청 (pk=%s, 문장 %d건)", pk_range, len(chunk))
    with ls.tracing_context(enabled=False):
        result = structured_chat.invoke(messages)
    logger.info("initial_translate: 청크 완료 (pk=%s, 번역 %d건)", pk_range, len(result.translations))
    return [(t.pk, t.text) for t in result.translations]


def initial_translate_batch(
    items: List[List[Tuple[int, str]]], author: str, book_title: str
) -> List[Tuple[int, str]]:
    """
    전처리된 독일어 문장 청크들을 병렬로 한국어 번역.
    각 청크는 한 번의 LLM 호출로 번역된다.
    author, book_title은 시스템 프롬프트에 반영된다.
    """
    if not items:
        return []

    workers = min(_MAX_PARALLEL_WORKERS, len(items))
    results: List[Tuple[int, str]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_translate_single_chunk, chunk, author, book_title)
            for chunk in items
        ]
        for idx, future in enumerate(futures):
            try:
                results.extend(future.result())
            except (TranslaterAIError, LLMProviderError, Exception) as e:
                first_pk = items[idx][0][0] if items[idx] else None
                logger.warning(
                    "청크 번역 실패(건너뜀, 다음 사이클에 재시도). chunk_index=%s, first_pk=%s: %s",
                    idx,
                    first_pk,
                    e,
                    exc_info=True,
                )
    return results
