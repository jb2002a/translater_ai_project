"""
후처리(번역) 그래프: DB에서 미번역 문장 조회 → LLM 번역 → DB 저장 (반복)
"""
from pathlib import Path
import sys

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from langgraph.graph import StateGraph, END

from main.TranslationState import PostTranslationState
from main.post_process.node.TranslateNode import (
    fetch_sentences_node,
    translate_node,
    save_translations_node,
)


def _route_after_fetch(state: PostTranslationState) -> str:
    """fetch_sentences 후: pending_items가 있으면 translate, 없으면 종료"""
    if state.get("pending_items"):
        return "translate"
    return "__end__"


def create_translation_workflow():
    workflow = StateGraph(PostTranslationState)

    workflow.add_node("fetch_sentences", fetch_sentences_node)
    workflow.add_node("translate", translate_node)
    workflow.add_node("save_translations", save_translations_node)

    workflow.set_entry_point("fetch_sentences")
    workflow.add_conditional_edges(
        "fetch_sentences",
        _route_after_fetch,
        {"translate": "translate", "__end__": END},
    )
    workflow.add_edge("translate", "save_translations")
    workflow.add_edge("save_translations", "fetch_sentences")

    return workflow.compile()


if __name__ == "__main__":
    import config

    app = create_translation_workflow()

    initial_state: PostTranslationState = {
        "db_path": getattr(config, "DEFAULT_DB_PATH", "philosophy_translation.db"),
        "author": "Dilthey, Wilhelm",
        "book_title": "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. Versuch einer Grundlegung für das Studium der Gesellschaft und der Geschichte. Bd. 1. Leipzig, 1883",
        "current_pk": 1,
    }

    final_output = app.invoke(initial_state)
    print(f"번역 완료. last_saved_count: {final_output.get('last_saved_count', 'N/A')}")
