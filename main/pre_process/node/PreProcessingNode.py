from ..service.ExtractService import extract_text
from ..service.PreProcessingService import (
    cleanup_chunks_parallel,
    rebatch_chunks_by_tokens,
    save_to_db,
)
from ..service.SegmentService import segment_raw_to_list
from ...TranslationState import GraphState


# PySBD로 raw_text를 문장 단위 청크 리스트로 분리 (cleanup 병렬화를 위해 선행)
def chunking_node(state: GraphState):
    raw_text = state["raw_text"]
    raw_chunks = segment_raw_to_list(raw_text)
    return {"raw_chunks": raw_chunks}


# 청크 재정립(5만 토큰 단위) 후 병렬 cleanup → sentences 리스트 그대로
def cleanup_node(state: GraphState):
    raw_chunks = state["raw_chunks"]
    batched_chunks = rebatch_chunks_by_tokens(raw_chunks, max_tokens=50_000)
    sentences = cleanup_chunks_parallel(batched_chunks)
    return {"sentences": sentences}


# 데이터베이스 저장 노드
def save_db_node(state: GraphState):
    pdf_path = state["pdf_path"]
    author = state["author"]
    book_title = state["book_title"]
    sentences = state["sentences"]
    save_to_db(pdf_path, author, book_title, sentences)
    return {"db_status": "saved"}
