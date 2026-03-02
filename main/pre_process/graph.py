"""
전처리 그래프: PDF 추출 → 청킹 → cleanup → flatten → DB 저장
"""
from pathlib import Path
import sys

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from langgraph.graph import StateGraph, END

from main.TranslationState import GraphState
from main.exceptions import TranslaterAIError
from main.pre_process.node.ExtractNode import extract_node
from main.pre_process.node.PreProcessingNode import (
    cleanup_node,
    chunking_node,
    flatten_sentences_node,
    re_chunking_node,
    save_db_node,
)


def create_preprocessing_workflow():
    """전처리 전용 워크플로우 생성."""
    workflow = StateGraph(GraphState)

    workflow.add_node("extract", extract_node)
    workflow.add_node("chunking", chunking_node)
    workflow.add_node("re_chunking", re_chunking_node)
    workflow.add_node("cleanup", cleanup_node)
    workflow.add_node("flatten_sentences", flatten_sentences_node)
    workflow.add_node("save_db", save_db_node)

    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "chunking")
    workflow.add_edge("chunking", "re_chunking")
    workflow.add_edge("re_chunking", "cleanup")
    workflow.add_edge("cleanup", "flatten_sentences")
    workflow.add_edge("flatten_sentences", "save_db")
    workflow.add_edge("save_db", END)

    return workflow.compile()


if __name__ == "__main__":
    import config

    app = create_preprocessing_workflow()

    initial_state: GraphState = {
        "pdf_path": config.DEFAULT_PDF_PATH,
        "author": "Dilthey, Wilhelm",
        "book_title": "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. Versuch einer Grundlegung für das Studium der Gesellschaft und der Geschichte. Bd. 1. Leipzig, 1883",
        "db_path": "philosophy_translation.db",
    }

    # Run the workflow (LangSmith: LANGCHAIN_TRACING_V2=true 시 자동 트레이싱)
    try:
        final_output = app.invoke(initial_state)
    except TranslaterAIError as e:
        print(f"전처리 실패: {e}", file=sys.stderr)
        raise SystemExit(1)

    # flatten_sentences 결과 청크(german_sentences) 상위 100개 idx : value 형식으로 텍스트 파일 저장
    chunks = final_output.get("german_sentences", [])
    out_path = Path(__file__).resolve().parent.parent.parent / "flatten_sentences_top100.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# flatten_sentences 결과 청크 수: {len(chunks)}, 상위 100개\n\n")
        for idx, value in enumerate(chunks[100:200]):
            f.write(f"{idx} : {value}\n")
