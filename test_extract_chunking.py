"""
extract_node -> chunking_node 만 실행하는 테스트.
PDF 추출 후 PySBD 청킹 결과만 확인합니다 (cleanup 없음).
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langgraph.graph import StateGraph, END

from main.TranslationState import GraphState
from main.pre_process.node.ExtractNode import extract_node
from main.pre_process.node.PreProcessingNode import chunking_node
from main.models import models
import config

DEFAULT_PDF = config.DEFAULT_PDF_PATH


def create_extract_chunking_only_workflow():
    """extract -> chunking 만 있는 워크플로우."""
    workflow = StateGraph(GraphState)
    workflow.add_node("extract", extract_node)
    workflow.add_node("chunking", chunking_node)
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "chunking")
    workflow.add_edge("chunking", END)
    return workflow.compile()


def run_test(pdf_path: str):
    app = create_extract_chunking_only_workflow()
    initial_state: GraphState = {
        "pdf_path": pdf_path,
        "author": "",
        "book_title": "",
        "raw_text": "",
        "raw_chunks": [],
        "cleaned_text": "",
        "sentences": [],
    }
    langfuse_handler = models.get_langfuse_handler()
    out = app.invoke(initial_state, config={"callbacks": [langfuse_handler]} if langfuse_handler else {})

    raw_text = out.get("raw_text", "")
    raw_chunks = out.get("raw_chunks", [])

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
        print("  경고: 청크가 없습니다.")
        return

    for i, chunk in enumerate(raw_chunks[:15]):
        preview = chunk[:80] + "..." if len(chunk) > 80 else chunk
        print(f"  [{i}] ({len(chunk)}자) {preview!r}")
    if len(raw_chunks) > 15:
        print(f"  ... 외 {len(raw_chunks) - 15}개 청크")
    print("=" * 60)


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    if not Path(pdf_path).exists():
        print(f"파일 없음: {pdf_path}")
        print("사용법: python test_extract_chunking.py [PDF경로]")
        sys.exit(1)
    run_test(pdf_path)
