"""
extract_node -> chunking_node -> cleanup_node 흐름 테스트.
PDF에서 텍스트 추출 후 PySBD로 문장 단위 청킹, 청크별 병렬 cleanup이 잘 되는지 확인합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langgraph.graph import StateGraph, END

from main.TranslationState import GraphState
from main.pre_process.node.ExtractNode import extract_node
from main.pre_process.node.PreProcessingNode import chunking_node, cleanup_node

import config

# main.py 예시와 동일한 기본 state 값
DEFAULT_STATE = {
    "pdf_path": config.DEFAULT_PDF_PATH,
    "author": "Dilthey, Wilhelm",
    "book_title": "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. Versuch einer Grundlegung für das Studium der Gesellschaft und der Geschichte. Bd. 1. Leipzig, 1883",
}


def create_extract_chunking_workflow():
    """extract -> chunking -> cleanup 워크플로우."""
    workflow = StateGraph(GraphState)
    workflow.add_node("extract", extract_node)
    workflow.add_node("chunking", chunking_node)
    workflow.add_node("cleanup", cleanup_node)
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "chunking")
    workflow.add_edge("chunking", "cleanup")
    workflow.add_edge("cleanup", END)
    return workflow.compile()


def run_test(pdf_path: str = None, author: str = None, book_title: str = None):
    app = create_extract_chunking_workflow()
    initial_state: GraphState = {
        "pdf_path": pdf_path or DEFAULT_STATE["pdf_path"],
        "author": author if author is not None else DEFAULT_STATE["author"],
        "book_title": book_title if book_title is not None else DEFAULT_STATE["book_title"],
        "raw_text": "",
        "raw_chunks": [],
        "cleaned_text": "",
        "sentences": [],
    }
    out = app.invoke(initial_state)

    raw_text = out.get("raw_text", "")
    raw_chunks = out.get("raw_chunks", [])
    sentences = out.get("sentences", [])

    print("=" * 60)
    print("[1] 추출(raw_text)")
    print("=" * 60)
    print(f"  길이: {len(raw_text)} 문자")
    print(f"  미리보기(앞 300자):\n  {raw_text[:300]!r}\n")

    print("=" * 60)
    print("[2] 청킹(raw_chunks)")
    print("=" * 60)
    print(f"  청크 개수: {len(raw_chunks)}")
    if not raw_chunks:
        print("  경고: 청크가 없습니다. (raw_text가 비었거나 문장 구분 실패)")
        return False

    # 청킹 검증
    for i, chunk in enumerate(raw_chunks[:10]):
        preview = chunk[:80] + "..." if len(chunk) > 80 else chunk
        print(f"  [{i}] ({len(chunk)}자) {preview!r}")
    if len(raw_chunks) > 10:
        print(f"  ... 외 {len(raw_chunks) - 10}개 청크")

    # 각 청크가 비어 있지 않은지, 문자열인지 확인
    non_empty = sum(1 for c in raw_chunks if isinstance(c, str) and c.strip())
    assert non_empty == len(raw_chunks), "일부 청크가 비어 있거나 문자열이 아님"
    print("\n  [OK] 모든 청크가 비어 있지 않은 문자열입니다.")

    print("=" * 60)
    print("[3] cleanup(sentences)")
    print("=" * 60)
    print(f"  문장 개수: {len(sentences)}")
    if not sentences:
        print("  경고: cleanup 결과 문장이 없습니다.")
        return False
    for i, sent in enumerate(sentences[:10]):
        preview = sent[:80] + "..." if len(sent) > 80 else sent
        print(f"  [{i}] ({len(sent)}자) {preview!r}")
    if len(sentences) > 10:
        print(f"  ... 외 {len(sentences) - 10}개 문장")
    non_empty_sent = sum(1 for s in sentences if isinstance(s, str) and s.strip())
    assert non_empty_sent == len(sentences), "일부 문장이 비어 있거나 문자열이 아님"
    print("\n  [OK] cleanup 완료, 모든 문장이 유효합니다.")
    return True


def run_chunking_only_test():
    """PDF 없이 샘플 raw_text로 청킹만 검증 (SegmentService 단위 테스트)."""
    from main.pre_process.service.SegmentService import segment_raw_to_list

    sample = (
        "Das ist der erste Satz. Das ist der zweite Satz! "
        "Ist das der dritte Satz? Ja, das ist er."
    )
    chunks = segment_raw_to_list(sample)
    print("=" * 60)
    print("[단위 테스트] segment_raw_to_list (PDF 없음)")
    print("=" * 60)
    print(f"  입력: {sample!r}")
    print(f"  청크 개수: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"  [{i}] {c!r}")
    ok = len(chunks) >= 2 and all(isinstance(c, str) for c in chunks)
    print("\n  [OK]" if ok else "\n  [FAIL]")
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "unit":
        sys.exit(0 if run_chunking_only_test() else 1)

    # main.py와 동일한 기본값 사용
    pdf_path = DEFAULT_STATE["pdf_path"]
    author = DEFAULT_STATE["author"]
    book_title = DEFAULT_STATE["book_title"]
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    # 필요 시 인자 2, 3으로 author, book_title 오버라이드 가능

    if not Path(pdf_path).exists():
        print(f"파일 없음: {pdf_path}")
        print("사용법: python test_preprocess.py [PDF경로]")
        print("       python test_preprocess.py unit   # PDF 없이 청킹만 테스트")
        sys.exit(1)

    success = run_test(pdf_path=pdf_path, author=author, book_title=book_title)
    sys.exit(0 if success else 1)
