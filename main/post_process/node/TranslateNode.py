from ..service.Initial_translate import initial_translate
from ..service.TranslationDbService import (
    fetch_german_sentences_within_tokens,
    save_translations_to_db,
)
from ...TranslationState import GraphState
from ...exceptions import InvalidStateError, TranslaterAIError


def _require(state: GraphState, key: str):
    if key not in state:
        raise InvalidStateError(f"필수 state 키 누락: {key}")
    return state[key]


# DB에서 current_pk 기준으로 max_tokens 이내의 독일어 문장을 조회하여 pending_items에 저장
def fetch_sentences_node(state: GraphState):
    try:
        _require(state, "db_path")
        _require(state, "current_pk")
        items, state_updates = fetch_german_sentences_within_tokens(state)
        return {
            "pending_items": items,
            **state_updates,
        }
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e


# pending_items의 독일어 문장을 문장별로 LLM에 번역 요청, translated_items에 저장
def translate_node(state: GraphState):
    try:
        pending_items = _require(state, "pending_items")
        author = _require(state, "author")
        book_title = _require(state, "book_title")

        translated_items = []
        for pk, sentence in pending_items:
            result = initial_translate(
                pk=pk, text=sentence, author=author, book_title=book_title
            )
            translated_items.append((result.pk, result.text))

        return {"translated_items": translated_items}
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e


# translated_items의 번역 결과를 DB에 저장
def save_translations_node(state: GraphState):
    try:
        db_path = _require(state, "db_path")
        translated_items = _require(state, "translated_items")
        save_translations_to_db(db_path, translated_items)
        return
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e
