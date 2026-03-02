from typing import List, Tuple
from ..service.Initial_translate import initial_translate_batch
from ..service.TranslationDbService import (
    fetch_german_sentences_within_tokens,
    save_translations_to_db,
)
from ...TranslationState import PostTranslationState
from ...exceptions import InvalidStateError


def _require(state: PostTranslationState, key: str):
    if key not in state:
        raise InvalidStateError(f"필수 state 키 누락: {key}")
    return state[key]


# 5000토큰 내의 미번역 독일어 문장 조회 (id 순)
def fetch_sentences_node(state: PostTranslationState) -> dict:
    db_path = _require(state, "db_path")
    author = _require(state, "author")
    book_title = _require(state, "book_title")

    items = fetch_german_sentences_within_tokens(
        db_path=db_path,
        author=author,
        book_title=book_title,
    )
    return {"pending_items": items}


# pending_items의 독일어 청킹을 LLM에 번역 요청, translated_items에 저장
def translate_node(state: PostTranslationState) -> dict:
    pending_items: List[Tuple[int, str]] = _require(state, "pending_items")
    author = _require(state, "author")
    book_title = _require(state, "book_title")

    # (pk, sentence) 튜플로 이루어진 리스트를 한 번에 번역
    translated_items = initial_translate_batch(
        items=pending_items, author=author, book_title=book_title
    )
    return {"translated_items": translated_items}


# translated_items의 번역 결과를 DB에 저장
def save_translations_node(state: PostTranslationState) -> dict:
    db_path = _require(state, "db_path")
    translated_items: List[Tuple[int, str]] = _require(state, "translated_items")
    save_translations_to_db(db_path, translated_items)

    # 상태 업데이트: 번역 완료 표시 및 처리된 항목 수 반환
    return {
        "translated_items": [],  # 처리 완료 후 초기화
        "last_saved_count": len(translated_items),
    }
