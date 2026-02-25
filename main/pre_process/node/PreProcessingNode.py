from ..service.ExtractService import extract_text
from ..service.PreProcessingService import pre_process_chunks_parallel, save_to_db
from ..service.SegmentService import segment_raw_to_list
from ...TranslationState import GraphState


# PySBD로 raw_text를 문장 단위 청크 리스트로 분리 (cleanup 병렬화를 위해 선행)
def chunking_node(state: GraphState):
    raw_text = state["raw_text"]
    raw_chunks = segment_raw_to_list(raw_text)
    return {"raw_chunks": raw_chunks}


# 청크별 병렬 cleanup → sentences (한 문장 per line → 리스트)
def cleanup_node(state: GraphState):
    raw_chunks = state["raw_chunks"]
    refactored_text = pre_process_chunks_parallel(raw_chunks)
    sentences = refactored_text.split("\n") if refactored_text else []
    return {"sentences": sentences}


# 데이터베이스 저장 노드
def save_db_node(state: GraphState):
    pdf_path = state["pdf_path"]
    author = state["author"]
    book_title = state["book_title"]
    sentences = state["sentences"]
    save_to_db(pdf_path, author, book_title, sentences)
    return {"db_status": "saved"}
