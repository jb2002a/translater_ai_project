from pathlib import Path
import sys

# main/main.py 직접 실행 시 프로젝트 루트에서 config 로드
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
import config

from langgraph.graph import StateGraph, END
from .pre_process.node.ExtractNode import extract_node
from .pre_process.node.PreProcessingNode import (
    cleanup_node,
    chunking_node,
    save_db_node,
)
from .TranslationState import GraphState
from .pre_process.service.Utils import read_from_db, generate_text_file_du
from .models import models


def create_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("extract", extract_node)
    workflow.add_node("cleanup", cleanup_node)
    workflow.add_node("chunking", chunking_node)
    workflow.add_node("save_db", save_db_node)

    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "chunking")
    workflow.add_edge("chunking", "cleanup")
    workflow.add_edge("cleanup", "save_db")
    workflow.add_edge("save_db", END)

    return workflow.compile()


# Example Usage:
if __name__ == "__main__":
    app = create_workflow()

    initial_state = {
        "pdf_path": config.DEFAULT_PDF_PATH,
        "author": "Dilthey, Wilhelm",
        "book_title": "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. Versuch einer Grundlegung für das Studium der Gesellschaft und der Geschichte. Bd. 1. Leipzig, 1883",
    }

    # Run the workflow (Langfuse로 전체 파이프라인 트레이싱)
    langfuse_handler = models.get_langfuse_handler()
    final_output = app.invoke(initial_state, config={"callbacks": [langfuse_handler]} if langfuse_handler else {})
    print(f"Workflow Status: {final_output.get('db_status')}")


