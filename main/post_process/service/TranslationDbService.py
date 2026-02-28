# DB에서 pending 문장 조회 및 번역 결과 저장

import sqlite3
from typing import List, Tuple

from ...exceptions import DatabaseError


def fetch_pending_sentences(
    db_path: str,
    *,
    author: str,
    book_title: str,
    limit: int | None = None,
) -> List[Tuple[int, str]]:
    """
    status='pending'인 문장들을 (id, german_sentence) 형태로 id 순으로 조회.
    author, book_title으로 필터링.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        sql = (
            "SELECT id, german_sentence FROM processed_sentences "
            "WHERE status = ? AND author = ? AND book_title = ?"
        )
        params: list = ["pending", author, book_title]
        sql += " ORDER BY id"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()
        return [(row["id"], row["german_sentence"]) for row in rows]
    except sqlite3.Error as e:
        raise DatabaseError(f"DB 조회 실패: {db_path}", cause=e) from e


def save_translation(
    db_path: str,
    sentence_id: int,
    korean_sentence: str,
) -> None:
    """특정 id의 korean_sentence를 UPDATE하고 status를 'translated'로 변경(덮어쓰기)."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE processed_sentences
            SET korean_sentence = ?, status = 'translated'
            WHERE id = ?
            """,
            (korean_sentence, sentence_id),
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise DatabaseError(f"DB 저장 실패: {db_path}", cause=e) from e


def approve_translation(db_path: str, sentence_id: int) -> None:
    """특정 id의 status를 'approved'로 변경, 사용자의 번역 승인 처리."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE processed_sentences
            SET status = 'approved'
            WHERE id = ?
            """,
            (sentence_id,),
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise DatabaseError(f"DB 상태 업데이트 실패: {db_path}", cause=e) from e


def save_translations_batch(
    db_path: str,
    translations: List[Tuple[int, str]],
) -> None:
    """여러 건 일괄 UPDATE. translations = [(sentence_id, korean_sentence), ...] (덮어쓰기)."""
    if not translations:
        return
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.executemany(
            """
            UPDATE processed_sentences
            SET korean_sentence = ?, status = 'translated'
            WHERE id = ?
            """,
            [(ko, sid) for sid, ko in translations],
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise DatabaseError(f"DB 일괄 저장 실패: {db_path}", cause=e) from e
