# This module provides DB access for the translation post-process (fetch/store sentences).

import sqlite3
from typing import List, Tuple

from ...exceptions import DatabaseError

# PreProcessingService와 동일: Gemini 기준 대략 4자당 1토큰
DEFAULT_CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str, chars_per_token: int = DEFAULT_CHARS_PER_TOKEN) -> int:
    return max(1, len(text) // chars_per_token)


def has_untranslated_sentences(db_path: str, author: str, book_title: str) -> bool:
    """
    미번역(korean_sentence IS NULL 또는 '') 문장이 있는지 확인.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM processed_sentences
                WHERE author = ? AND book_title = ?
                  AND (korean_sentence IS NULL OR korean_sentence = '')
                LIMIT 1
                """,
                (author, book_title),
            )
            return cur.fetchone() is not None
    except sqlite3.Error as e:
        raise DatabaseError(f"DB 조회 실패: {db_path}", cause=e) from e


def fetch_german_sentences_within_tokens(
    db_path: str,
    author: str,
    book_title: str,
    max_tokens: int = 10000,
    chars_per_token: int = DEFAULT_CHARS_PER_TOKEN,
) -> List[List[Tuple[int, str]]]:
    """
    미번역(korean_sentence IS NULL) 문장을 id 순으로 조회하며,
    max_tokens 이내로 묶은 청크들의 리스트를 반환한다.
    """
    chunks: List[List[Tuple[int, str]]] = []
    current_chunk: List[Tuple[int, str]] = []
    total_tokens = 0

    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, german_sentence
                FROM processed_sentences
                WHERE author = ? AND book_title = ?
                  AND (korean_sentence IS NULL OR korean_sentence = '')
                ORDER BY id
                """,
                (author, book_title),
            )

            for row_id, german_sentence in cur:
                sentence = german_sentence or ""
                chunk_tokens = _estimate_tokens(sentence, chars_per_token)

                if total_tokens + chunk_tokens > max_tokens and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    total_tokens = 0

                total_tokens += chunk_tokens
                current_chunk.append((row_id, sentence))

        if current_chunk:
            chunks.append(current_chunk)

    except sqlite3.Error as e:
        raise DatabaseError(f"DB 조회 실패: {db_path}", cause=e) from e

    return chunks


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
