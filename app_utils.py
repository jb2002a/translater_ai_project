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
