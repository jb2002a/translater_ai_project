from pathlib import Path
import sys

# main/main.py 직접 실행 시 프로젝트 루트에서 config 로드
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
import config

from langgraph.graph import StateGraph, END
from main.pre_process.node.ExtractNode import extract_node
from main.pre_process.node.PreProcessingNode import (
    cleanup_node,
    chunking_node,
    flatten_sentences_node,
    re_chunking_node,
    save_db_node,
)
from main.TranslationState import GraphState
from main.pre_process.service.Utils import generate_text_file_du


def create_workflow():
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


# Example Usage:
if __name__ == "__main__":
    app = create_workflow()

    initial_state = {
        "pdf_path": config.DEFAULT_PDF_PATH,
        "author": "Dilthey, Wilhelm",
        "book_title": "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. Versuch einer Grundlegung für das Studium der Gesellschaft und der Geschichte. Bd. 1. Leipzig, 1883",
        "db_path": "philosophy_translation.db",
    }

    # Run the workflow (LangSmith: LANGCHAIN_TRACING_V2=true 시 자동 트레이싱)
    final_output = app.invoke(initial_state)

    # flatten_sentences 결과 청크(german_sentences) 상위 100개 idx : value 형식으로 텍스트 파일 저장
    chunks = final_output.get("german_sentences", [])
    out_path = Path(__file__).resolve().parent.parent / "flatten_sentences_top100.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# flatten_sentences 결과 청크 수: {len(chunks)}, 상위 100개\n\n")
        for idx, value in enumerate(chunks[100:200]):
            f.write(f"{idx} : {value}\n")


