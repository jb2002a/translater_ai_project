import logging
from typing import List, Tuple

from ..service.Initial_translate import initial_translate_batch
from ..service.TranslationDbService import (
    fetch_german_sentences_within_tokens,
    save_translations_to_db,
)
from ...TranslationState import PostTranslationState
from ...exceptions import InvalidStateError

logger = logging.getLogger(__name__)


def _require(state: PostTranslationState, key: str):
    if key not in state:
        raise InvalidStateError(f"필수 state 키 누락: {key}")
    return state[key]


# 5000토큰 내의 미번역 독일어 문장 조회 (id 순)
# DB 오류 시 빈 목록 반환 → 그래프가 END로 정상 종료됨
def fetch_sentences_node(state: PostTranslationState) -> dict:
    db_path = _require(state, "db_path")
    author = _require(state, "author")
    book_title = _require(state, "book_title")

    try:
        items = fetch_german_sentences_within_tokens(
            db_path=db_path,
            author=author,
            book_title=book_title,
            max_chunks=2,
        )
        return {"pending_items": items}
    except Exception as e:
        logger.warning("미번역 문장 조회 실패(그래프 종료): %s", e, exc_info=True)
        return {"pending_items": []}


# pending_items의 독일어 청킹을 LLM에 번역 요청, translated_items에 저장
# 오류 시 로그 후 빈 결과 반환 → 그래프는 계속 순환하고, 실패한 문장은 다음 사이클에 재시도됨
def translate_node(state: PostTranslationState) -> dict:
    pending_items: List[List[Tuple[int, str]]] = _require(state, "pending_items")
    author = _require(state, "author")
    book_title = _require(state, "book_title")

    try:
        translated_items = initial_translate_batch(
            items=pending_items, author=author, book_title=book_title
        )
        return {"translated_items": translated_items}
    except Exception as e:
        logger.warning(
            "번역 노드 오류(그래프 계속 진행, 해당 배치는 다음 사이클에 재시도): %s",
            e,
            exc_info=True,
        )
        return {"translated_items": []}


# translated_items의 번역 결과를 DB에 저장
# DB 오류 시 로그 후 계속 진행 → 해당 문장은 DB에 미저장 상태로 남아 다음 사이클에 재번역·재저장 시도
def save_translations_node(state: PostTranslationState) -> dict:
    db_path = _require(state, "db_path")
    translated_items: List[Tuple[int, str]] = _require(state, "translated_items")

    try:
        save_translations_to_db(db_path, translated_items)
        return {
            "translated_items": [],
            "last_saved_count": len(translated_items),
        }
    except Exception as e:
        logger.warning(
            "DB 저장 실패(그래프 계속 진행, 해당 번역은 다음 사이클에 재시도): %s",
            e,
            exc_info=True,
        )
        return {"translated_items": [], "last_saved_count": 0}
