from pathlib import Path
import sys

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import sqlite3

DB_PATH = "philosophy_translation.db"
OUTPUT_TXT = _root / "db_sentences.txt"

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 컬럼명으로 접근 가능하게
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM processed_sentences WHERE id BETWEEN 1 AND 100 ORDER BY id"
    )
    rows = cur.fetchall()
    columns = [d[0] for d in cur.description]

    print("\n[DB 조회 결과] pk 1~100 전체 컬럼 출력")
    print("=" * 80)
    print(f"컬럼: {', '.join(columns)}")
    print("=" * 80)

    for row in rows:
        print(f"\n--- id={row['id']} ---")
        for col in columns:
            val = row[col] if row[col] is not None else "(NULL)"
            print(f"  {col}: {val}")

    conn.close()
