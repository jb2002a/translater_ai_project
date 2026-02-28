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


# SoMaJo로 raw_text를 문장 단위 청크 리스트로 분리, 청크 끝에 \n 추가
def chunking_node(state: GraphState):
    try:
        raw_text = _require(state, "raw_text")
        raw_chunks = segment_raw_to_list(raw_text)
        return {"raw_chunks": raw_chunks}
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e


# 청크 재정립: clean-up을 위해 5만 토큰 단위로 배치 묶기
def re_chunking_node(state: GraphState):
    try:
        raw_chunks = _require(state, "raw_chunks")
        batched_chunks = rebatch_chunks_by_tokens(raw_chunks, max_tokens=50_000)
        return {"batched_chunks": batched_chunks}
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e


# re_chunking_node에서 나온 배치별 문장 리스트를 병렬로 cleanup
def cleanup_node(state: GraphState):
    try:
        batched_chunks = _require(state, "batched_chunks")
        cleaned_batches = cleanup_chunks_parallel(batched_chunks)
        return {"cleaned_batches": cleaned_batches}
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e


# cleaned_batches를 합친 뒤 \n 기준으로 재청킹 → 문장 단위 리스트
def flatten_sentences_node(state: GraphState):
    try:
        cleaned_batches = _require(state, "cleaned_batches")
        merged = "".join(cleaned_batches)
        sentences = [s for s in merged.split("\n") if s]
        return {"sentences": sentences}
    except TranslaterAIError:
        raise
    except KeyError as e:
        raise InvalidStateError(f"필수 state 키 누락: {e}") from e


# flatten_sentences_node에서 나온 문장 리스트를 데이터베이스에 저장
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
