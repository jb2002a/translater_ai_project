from typing import List, Tuple
from ..service.Initial_translate import initial_translate
from ..service.TranslationDbService import (
    fetch_german_sentences_within_tokens,
    save_translations_to_db,
)
from ...TranslationState import PostTranslationState
from ...exceptions import InvalidStateError, TranslaterAIError


def _require(state: PostTranslationState, key: str):
    if key not in state:
        raise InvalidStateError(f"필수 state 키 누락: {key}")
    return state[key]


# 5000토큰 내의 독일어 문장 청킹
def fetch_sentences_node(state: PostTranslationState) -> dict:
    try:
        _require(state, "db_path")
        items, state_updates = fetch_german_sentences_within_tokens(state)
        # state 업데이트 pending_items, current_pk(state_updates)
        return {
            "pending_items": items,
            **state_updates,
        }
    except TranslaterAIError:
        raise


# pending_items의 독일어 청킹을 LLM에 번역 요청, translated_items에 저장
def translate_node(state: PostTranslationState) -> dict:
    try:
        pending_items: List[Tuple[int, str]] = _require(state, "pending_items")
        author = _require(state, "author")
        book_title = _require(state, "book_title")

        translated_items: List[Tuple[int, str]] = []
        # (pk, sentence) 튜플로 이루어진 리스트를 순회하여 각 문장 번역
        for pk, sentence in pending_items:
            result = initial_translate(
                pk=pk, text=sentence, author=author, book_title=book_title
            )
            translated_items.append((result.pk, result.text))

        return {"translated_items": translated_items}
    except TranslaterAIError:
        raise


# translated_items의 번역 결과를 DB에 저장
def save_translations_node(state: PostTranslationState) -> dict:
    try:
        db_path = _require(state, "db_path")
        translated_items: List[Tuple[int, str]] = _require(state, "translated_items")
        save_translations_to_db(db_path, translated_items)

        # 상태 업데이트: 번역 완료 표시 및 처리된 항목 수 반환
        return {
            "translated_items": [],  # 처리 완료 후 초기화
            "last_saved_count": len(translated_items),
        }
    except TranslaterAIError:
        raise
