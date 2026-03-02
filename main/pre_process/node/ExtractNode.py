from ..service.ExtractService import extract_text
from ...TranslationState import GraphState
from ...exceptions import InvalidStateError


def extract_node(state: GraphState):
    doc_path = state.get("pdf_path")
    if doc_path is None or doc_path == "":
        raise InvalidStateError("필수 state 키 누락: pdf_path")
    extracted_text = extract_text(doc_path)
    return {"raw_text": extracted_text}
