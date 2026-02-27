import sqlite3

from ...exceptions import DatabaseError, FileWriteError


# 텍스트 파일로 저장하는 함수
def generate_text_file_du(text):
    try:
        with open("output_du.txt", "w", encoding="utf-8") as f:
            f.write(text)
    except OSError as e:
        raise FileWriteError("output_du.txt 쓰기 실패", cause=e) from e


def generate_text_file_ko(text):
    try:
        with open("output_ko.txt", "w", encoding="utf-8") as f:
            f.write(text)
    except OSError as e:
        raise FileWriteError("output_ko.txt 쓰기 실패", cause=e) from e


# read from db
def read_from_db(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT german_sentence FROM processed_sentences")
        sentences = [row[0] for row in cursor.fetchall()]
        conn.close()
        return sentences
    except sqlite3.Error as e:
        raise DatabaseError(f"DB 읽기 실패: {db_path}", cause=e) from e
