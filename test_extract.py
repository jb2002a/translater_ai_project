"""
extract 단계만 실행해, PDF에서 텍스트가 어떻게 추출되었는지 확인합니다.
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from main.TranslationState import GraphState
from main.pre_process.node.ExtractNode import extract_node
import config

DEFAULT_PDF = config.DEFAULT_PDF_PATH


def show_extract(pdf_path: str):
    state: GraphState = {
        "pdf_path": pdf_path,
        "author": "",
        "book_title": "",
        "raw_text": "",
        "raw_chunks": [],
        "cleaned_text": "",
        "sentences": [],
    }
    out = extract_node(state)
    raw_text = out.get("raw_text", "")

    print("=" * 60)
    print("[Extract 결과]")
    print("=" * 60)
    print(f"  PDF: {pdf_path}")
    print(f"  추출 문자 수: {len(raw_text)}")
    print()

    if not raw_text or not raw_text.strip():
        print("  (추출된 텍스트 없음)")
        return

    print("  --- 앞 500자 ---")
    print(raw_text[:500])
    print()

    if len(raw_text) > 1000:
        print("  --- 500~1000자 ---")
        print(raw_text[500:1000])
        print()

    print(f"  줄바꿈(\\n) 개수: {raw_text.count(chr(10))}")
    print("=" * 60)


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    if not Path(pdf_path).exists():
        print(f"파일 없음: {pdf_path}")
        print("사용법: python test_extract.py [PDF경로]")
        sys.exit(1)
    show_extract(pdf_path)
