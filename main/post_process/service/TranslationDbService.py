# This module provides DB access for the translation post-process (fetch/store sentences).

import sqlite3
from typing import Dict, List, Tuple, Any

from ...exceptions import DatabaseError

# PreProcessingService와 동일: Gemini 기준 대략 4자당 1토큰
DEFAULT_CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str, chars_per_token: int = DEFAULT_CHARS_PER_TOKEN) -> int:
    return max(1, len(text) // chars_per_token)


def get_next_start_pk(db_path: str, author: str, book_title: str) -> int:
    """
    미번역(korean_sentence IS NULL) 문장 중 가장 작은 id를 반환.
    모두 번역되었으면 0을 반환.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT MIN(id) FROM processed_sentences
                WHERE author = ? AND book_title = ?
                AND (korean_sentence IS NULL OR korean_sentence = '')
                """,
                (author, book_title),
            )
            row = cur.fetchone()
            val = row[0] if row else None
            return int(val) if val is not None else 0
    except sqlite3.Error as e:
        raise DatabaseError(f"DB 조회 실패: {db_path}", cause=e) from e


def fetch_german_sentences_within_tokens(
    state: Any,
    max_tokens: int = 5000,
    chars_per_token: int = DEFAULT_CHARS_PER_TOKEN,
) -> Tuple[List[Tuple[int, str]], Dict[str, Any]]:
    """
    state에서 current_pk를 꺼내와, 해당 pk부터 german_sentence를 조회하며
    누적 토큰이 max_tokens 이내가 될 때까지 문장 리스트를 채워 반환한다.

    Returns:
        (items, state_updates): (pk, german_sentence) 튜플 리스트와 state 업데이트 딕셔너리.
        state_updates에 current_pk가 포함되며, 호출측에서 반영한다.
    """
    db_path = state.get("db_path")
    current_pk = state.get("current_pk", 1)
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, german_sentence
                FROM processed_sentences
                WHERE id >= ?
                ORDER BY id
                """,
                (current_pk,),
            )
            rows = cur.fetchall()
    except sqlite3.Error as e:
        raise DatabaseError(f"DB 조회 실패: {db_path}", cause=e) from e

    items: List[Tuple[int, str]] = []
    total_tokens = 0
    next_pk: int | None = None

    for row_id, german_sentence in rows:
        sentence = german_sentence or ""
        chunk_tokens = _estimate_tokens(sentence, chars_per_token)
        total_tokens += chunk_tokens
        if total_tokens > max_tokens and items:
            next_pk = row_id
            break
        items.append((row_id, sentence))
    else:
        if items:
            next_pk = items[-1][0] + 1

    return items, {"current_pk": next_pk}


def save_translations_to_db(
    db_path: str,
    translations: List[Tuple[int, str]],
) -> None:
    """
    번역된 한국어 문장을 processed_sentences 테이블에 업데이트한다.

    Args:
        db_path: SQLite DB 경로
        translations: (pk, korean_sentence) 튜플 리스트
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.executemany(
                """
                UPDATE processed_sentences
                SET korean_sentence = ?, status = 'complete'
                WHERE id = ?
                """,
                [(korean, pk) for pk, korean in translations],
            )
            conn.commit()
    except sqlite3.Error as e:
        raise DatabaseError(f"DB 저장 실패: {db_path}", cause=e) from e
