from langgraph.graph import StateGraph, END
from .pre_process.node.ExtractNode import extract_node
from .pre_process.node.PreProcessingNode import (
    cleanup_node,
    refractor_node,
    save_db_node,
)
from .TranslationState import GraphState
from .pre_process.service.Utils import read_from_db, generate_text_file_du


def create_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("extract", extract_node)
    workflow.add_node("cleanup", cleanup_node)
    workflow.add_node("refractor", refractor_node)
    workflow.add_node("save_db", save_db_node)

    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "cleanup")
    workflow.add_edge("cleanup", "refractor")
    workflow.add_edge("refractor", "save_db")
    workflow.add_edge("save_db", END)

    return workflow.compile()


# Example Usage:
if __name__ == "__main__":
    app = create_workflow()

    initial_state = {
        "pdf_path": "D:\\Pdf\\test.pdf",
        "author": "Dilthey, Wilhelm",
        "book_title": "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. Versuch einer Grundlegung für das Studium der Gesellschaft und der Geschichte. Bd. 1. Leipzig, 1883",
    }

    # Run the workflow
    final_output = app.invoke(initial_state)
    print(f"Workflow Status: {final_output.get('db_status')}")


