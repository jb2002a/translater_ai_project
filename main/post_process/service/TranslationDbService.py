# This module provides DB access for the translation post-process (fetch/store sentences).

import sqlite3
from typing import List, Tuple, Any

from ...exceptions import DatabaseError

# PreProcessingService와 동일: Gemini 기준 대략 4자당 1토큰
DEFAULT_CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str, chars_per_token: int = DEFAULT_CHARS_PER_TOKEN) -> int:
    return max(1, len(text) // chars_per_token)


def fetch_german_sentences_within_tokens(
    state: Any,
    max_tokens: int = 5000,
    chars_per_token: int = DEFAULT_CHARS_PER_TOKEN,
) -> Tuple[List[str], int]:
    """
    state에서 current_pk를 꺼내와, 해당 pk부터 german_sentence를 조회하며
    누적 토큰이 max_tokens 이내가 될 때까지 문장 리스트를 채워 반환한다.
    db_path는 state에서 가져온다.

    Returns:
        (german_sentences, next_pk): 가져온 문장 리스트와, 다음 배치 시작할 pk.
    """
    db_path = state.get("db_path")
    current_pk = state.get("current_pk")
    try:
        conn = sqlite3.connect(db_path)
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
        conn.close()
    except sqlite3.Error as e:
        raise DatabaseError(f"DB 조회 실패: {db_path}", cause=e) from e

    items: List[Tuple[int, str]] = []
    total_tokens = 0
    next_pk = current_pk

    for row_id, german_sentence in rows:
        sentence = german_sentence or ""
        chunk_tokens = _estimate_tokens(sentence, chars_per_token)
        if total_tokens + chunk_tokens > max_tokens and items:
            next_pk = row_id
            break
        items.append((row_id, sentence))
        total_tokens += chunk_tokens

    if items and next_pk == current_pk:
        next_pk = items[-1][0] + 1
    german_sentences = [s for _, s in items]
    return german_sentences, next_pk
