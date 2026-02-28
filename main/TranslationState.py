from typing import TypedDict, List


class GraphState(TypedDict, total=False):
    pdf_path: str
    db_path: str
    author: str
    book_title: str
    raw_text: str
    raw_chunks: List[str]
    batched_chunks: List[str]
    cleaned_batches: List[str]
    german_sentences: List[str]
    current_pk : int = 1