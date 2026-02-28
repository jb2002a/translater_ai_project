# 번역 워크플로우 노드: pending 조회 → 배치 번역 → 1:1 매칭 → DB 저장

from typing import List, Tuple

from ...TranslationState import GraphState
from ...exceptions import InvalidStateError, TranslaterAIError
from ...pre_process.service.PreProcessingService import (
    ensure_korean_sentence_column,
)
from ..service.TranslationDbService import (
    fetch_pending_sentences,
    save_translations_batch,
)
from ..service.Initial_translate import initial_translate

DEFAULT_DB_PATH = "philosophy_translation.db"
CHARS_PER_TOKEN = 4
MAX_BATCH_TOKENS = 15_000


def _estimate_tokens(text: str, chars_per_token: int = CHARS_PER_TOKEN) -> int:
    return max(1, len(text) // chars_per_token)


def _batch_by_tokens(
    items: List[Tuple[int, str]],
    max_tokens: int = MAX_BATCH_TOKENS,
) -> List[List[Tuple[int, str]]]:
    """(id, sentence) 리스트를 토큰 수 제한으로 배치로 나눔."""
    if not items:
        return []
    batches: List[List[Tuple[int, str]]] = []
    current: List[Tuple[int, str]] = []
    current_tokens = 0
    for item in items:
        sid, sent = item
        add_tokens = _estimate_tokens(sent)
        if current_tokens + add_tokens > max_tokens and current:
            batches.append(current)
            current = []
            current_tokens = 0
        current.append(item)
        current_tokens += add_tokens
    if current:
        batches.append(current)
    return batches


def _require(state: GraphState, key: str):
    if key not in state:
        raise InvalidStateError(f"필수 state 키 누락: {key}")
    return state[key]


def translate_node(state: GraphState) -> dict:
    """
    DB에서 pending 문장 조회 → 토큰 단위 배치 구성 → initial_translate 호출
    → 출력을 줄 단위로 분리해 원문 id와 1:1 매칭 → DB에 korean_sentence 저장.
    """
    try:
        db_path = state.get("db_path") or DEFAULT_DB_PATH
        author = _require(state, "author")
        book_title = _require(state, "book_title")

        ensure_korean_sentence_column(db_path)
        pending = fetch_pending_sentences(
            db_path, author=author, book_title=book_title
        )
        if not pending:
            return {"translation_status": "done", "translated_count": 0}

        batches = _batch_by_tokens(pending)
        all_translations: List[Tuple[int, str]] = []

        for batch in batches:
            batch_ids = [sid for sid, _ in batch]
            batch_text = "\n".join(s for _, s in batch)
            translated_text = initial_translate(batch_text, author, book_title)
            if not isinstance(translated_text, str):
                translated_text = str(translated_text)
            lines = [s.strip() for s in translated_text.strip().split("\n") if s.strip()]
            # 1:1 매칭: 줄 수가 맞지 않으면 앞에서부터 min(len)만큼만 매칭
            n = min(len(batch_ids), len(lines))
            if n < len(batch_ids):
                # 줄 부족 시 나머지는 원문 그대로 저장하지 않고 스킵하거나, 재시도 로직 가능
                pass
            for i in range(n):
                all_translations.append((batch_ids[i], lines[i]))

        save_translations_batch(db_path, all_translations)
        return {
            "translation_status": "done",
            "translated_count": len(all_translations),
        }
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e
