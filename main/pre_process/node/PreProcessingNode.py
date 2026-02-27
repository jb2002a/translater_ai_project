from ..service.PreProcessingService import (
    cleanup_chunks_parallel,
    rebatch_chunks_by_tokens,
    save_to_db,
)
from ..service.SegmentService import segment_raw_to_list
from ...TranslationState import GraphState
from ...exceptions import InvalidStateError, TranslaterAIError


def _require(state: GraphState, key: str):
    if key not in state:
        raise InvalidStateError(f"필수 state 키 누락: {key}")
    return state[key]


# SoMaJo로 raw_text를 문장 단위 청크 리스트로 분리 (cleanup 병렬화를 위해 선행)
def chunking_node(state: GraphState):
    try:
        raw_text = _require(state, "raw_text")
        raw_chunks = segment_raw_to_list(raw_text)
        return {"raw_chunks": raw_chunks}
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e


# 청크 재정립(5만 토큰 단위) 후 병렬 cleanup → sentences 리스트 그대로
def cleanup_node(state: GraphState):
    try:
        raw_chunks = _require(state, "raw_chunks")
        batched_chunks = rebatch_chunks_by_tokens(raw_chunks, max_tokens=50_000)
        sentences = cleanup_chunks_parallel(batched_chunks)
        return {"sentences": sentences}
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e


# 데이터베이스 저장 노드
def save_db_node(state: GraphState):
    try:
        pdf_path = _require(state, "pdf_path")
        author = _require(state, "author")
        book_title = _require(state, "book_title")
        sentences = _require(state, "sentences")
        save_to_db(pdf_path, author, book_title, sentences)
        return {"db_status": "saved"}
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e
