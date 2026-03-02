"""
후처리(번역) 그래프: DB에서 미번역 문장 조회 → LLM 번역 → DB 저장
"""
from pathlib import Path
import sys

_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from langgraph.graph import StateGraph, END

from main.TranslationState import PostTranslationState
from main.post_process.service.TranslationDbService import has_untranslated_sentences
from main.post_process.node.TranslateNode import (
    fetch_sentences_node,
    translate_node,
    save_translations_node,
)


def _route_after_fetch(state: PostTranslationState) -> str:
    return "translate" if state.get("pending_items") else END


def create_translation_workflow():
    workflow = StateGraph(PostTranslationState)

    workflow.add_node("fetch_sentences", fetch_sentences_node)
    workflow.add_node("translate", translate_node)
    workflow.add_node("save_translations", save_translations_node)

    workflow.set_entry_point("fetch_sentences")
    workflow.add_conditional_edges(
        "fetch_sentences",
        _route_after_fetch,
        {"translate": "translate", END: END},
    )
    workflow.add_edge("translate", "save_translations")
    workflow.add_edge("save_translations", "fetch_sentences")

    return workflow.compile()


if __name__ == "__main__":
    import config

    app = create_translation_workflow()

    db_path = getattr(config, "DEFAULT_DB_PATH", "philosophy_translation.db")
    author = "Dilthey, Wilhelm"
    book_title = "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. Versuch einer Grundlegung für das Studium der Gesellschaft und der Geschichte. Bd. 1. Leipzig, 1883"

    if not has_untranslated_sentences(db_path, author, book_title):
        print("미번역 문장이 없습니다.")
        raise SystemExit(0)

    initial_state: PostTranslationState = {
        "db_path": db_path,
        "author": author,
        "book_title": book_title,
    }

    final_output = app.invoke(initial_state)
    print(f"번역 완료. 마지막 배치 저장 수: {final_output.get('last_saved_count', 'N/A')}")
