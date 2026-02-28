from pathlib import Path
import sys

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from main.pre_process.service.Utils import read_from_db

DB_PATH = "philosophy_translation.db"

if __name__ == "__main__":
    sentences = read_from_db(DB_PATH)
    print(f"\n[DB 조회 결과] 저장된 문장 수: {len(sentences)}")
    for i, s in enumerate(sentences[:30], 1):
        print(f"  {i}. {s}")
