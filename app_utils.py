"""앱 공통 유틸리티"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "philosophy_translation.db"
PAGE_SIZE = 20


def get_db_connection():
    """SQLite DB 연결"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def fetch_books(conn: sqlite3.Connection) -> list[tuple[str, str, int]]:
    """(author, book_title, 문장 수) 목록 조회"""
    cur = conn.cursor()
    cur.execute("""
        SELECT author, book_title, COUNT(*) as cnt
        FROM processed_sentences
        GROUP BY author, book_title
        ORDER BY author, book_title
    """)
    return cur.fetchall()


def fetch_sentences(
    conn: sqlite3.Connection,
    author: str,
    book_title: str,
    offset: int,
    limit: int,
) -> list[tuple[int, str, str]]:
    """선택한 책의 문장 쌍 조회. (id, german_sentence, korean_sentence)"""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, german_sentence, korean_sentence
        FROM processed_sentences
        WHERE author = ? AND book_title = ?
        ORDER BY id
        LIMIT ? OFFSET ?
        """,
        (author, book_title, limit, offset),
    )
    return cur.fetchall()


def count_sentences(conn: sqlite3.Connection, author: str, book_title: str) -> int:
    """선택한 책의 총 문장 수"""
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM processed_sentences WHERE author = ? AND book_title = ?",
        (author, book_title),
    )
    return cur.fetchone()[0]


def get_offset_by_id(
    conn: sqlite3.Connection, author: str, book_title: str, sentence_id: int
) -> int | None:
    """해당 책에서 sentence_id의 0-based 순서(offset). 없으면 None."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) FROM processed_sentences
        WHERE author = ? AND book_title = ? AND id < ?
        """,
        (author, book_title, sentence_id),
    )
    count = cur.fetchone()[0]
    cur.execute(
        """
        SELECT 1 FROM processed_sentences
        WHERE author = ? AND book_title = ? AND id = ?
        """,
        (author, book_title, sentence_id),
    )
    if cur.fetchone() is None:
        return None
    return count


def check_duplicate_book(
    conn: sqlite3.Connection, author: str, book_title: str
) -> bool:
    """동일 author + book_title 조합이 이미 DB에 있는지 확인."""
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM processed_sentences WHERE author = ? AND book_title = ? LIMIT 1",
        (author, book_title),
    )
    return cur.fetchone() is not None


def delete_book(
    conn: sqlite3.Connection, author: str, book_title: str
) -> int:
    """해당 책의 모든 문장을 삭제하고 삭제된 행 수를 반환."""
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM processed_sentences WHERE author = ? AND book_title = ?",
        (author, book_title),
    )
    conn.commit()
    return cur.rowcount
