from pathlib import Path
import sys

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from main.pre_process.service.Utils import read_from_db

DB_PATH = "philosophy_translation.db"
OUTPUT_TXT = _root / "db_sentences.txt"

if __name__ == "__main__":
    sentences = read_from_db(DB_PATH)
    total_chars = sum(len(s) for s in sentences)
    print(f"\n[DB 조회 결과] 저장된 문장 수: {len(sentences)}, 전체 글자수: {total_chars}")


    # txt 파일로 저장 (idx:value 순)
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        lines = [f"{i}:{s}" for i, s in enumerate(sentences, 1)]
        f.write("\n".join(lines))
    print(f"\n저장 완료: {OUTPUT_TXT}")
