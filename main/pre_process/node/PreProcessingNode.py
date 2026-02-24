from ..service.ExtractService import extract_text
from ..service.PreProcessingService import pre_process_text, refractor_text, save_to_db
from ...TranslationState import GraphState


# 불필요한 공백 제거, OCR 오류 수정 등 텍스트를 번역하기 적합한 형태로 가공하는 노드
def cleanup_node(state: GraphState):
    raw_text = state["raw_text"]
    cleaned_text = pre_process_text(raw_text)
    return {"cleaned_text": cleaned_text}


# 리펙터링 노드
def refractor_node(state: GraphState):
    cleaned_text = state["cleaned_text"]
    refractored_text = refractor_text(cleaned_text)
    return {"refractored_text": refractored_text}


# 데이터베이스 저장 노드
def save_db_node(state: GraphState):
    pdf_path = state["pdf_path"]
    author = state["author"]
    book_title = state["book_title"]
    sentences = state["refractored_text"].split("\n")
    save_to_db(pdf_path, author, book_title, sentences)
    return {"db_status": "saved"}
