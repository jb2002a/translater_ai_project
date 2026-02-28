from typing import TypedDict, List


class GraphState(TypedDict, total=False):
    pdf_path: str
    author: str
    book_title: str
    raw_text: str
    raw_chunks: List[str]
    batched_chunks: List[str]
    cleaned_batches: List[str]
    sentences: List[str]
    db_status: str
    db_path: str
    translation_status: str
    translated_count: int
