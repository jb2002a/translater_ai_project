from ..service.ExtractService import extract_text
from ...TranslationState import GraphState


def extract_node(state: GraphState):
    doc = state["pdf_doc"]
    extracted_text = extract_text(doc)
    return {"raw_text": extracted_text}
