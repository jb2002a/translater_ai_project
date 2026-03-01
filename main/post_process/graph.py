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
from main.post_process.service.TranslationDbService import get_next_start_pk
from main.post_process.node.TranslateNode import (
    fetch_sentences_node,
    translate_node,
    save_translations_node,
)


def create_translation_workflow():
    workflow = StateGraph(PostTranslationState)

    workflow.add_node("fetch_sentences", fetch_sentences_node)
    workflow.add_node("translate", translate_node)
    workflow.add_node("save_translations", save_translations_node)

    workflow.set_entry_point("fetch_sentences")
    workflow.add_edge("fetch_sentences", "translate")
    workflow.add_edge("translate", "save_translations")
    workflow.add_edge("save_translations", END)

    return workflow.compile()


if __name__ == "__main__":
    import config

    app = create_translation_workflow()

    db_path = getattr(config, "DEFAULT_DB_PATH", "philosophy_translation.db")
    author = "Dilthey, Wilhelm"
    book_title = "Dilthey, Wilhelm: Einleitung in die Geisteswissenschaften. Versuch einer Grundlegung für das Studium der Gesellschaft und der Geschichte. Bd. 1. Leipzig, 1883"

    start_pk = get_next_start_pk(db_path, author, book_title)
    if start_pk == 0:
        print("미번역 문장이 없습니다.")
        raise SystemExit(0)

    initial_state: PostTranslationState = {
        "db_path": db_path,
        "author": author,
        "book_title": book_title,
        "current_pk": start_pk,
    }

    final_output = app.invoke(initial_state)
    print(f"번역 완료. last_saved_count: {final_output.get('last_saved_count', 'N/A')}")
