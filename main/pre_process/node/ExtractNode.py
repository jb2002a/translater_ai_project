from ..service.ExtractService import extract_text
from ...TranslationState import GraphState


def extract_node(state: GraphState):
    doc_path = state["pdf_path"]
    extracted_text = extract_text(doc_path)
    return {"raw_text": extracted_text}
