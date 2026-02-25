from typing import TypedDict, List


class GraphState(TypedDict):
    pdf_path: str
    author: str
    book_title: str
    raw_text: str
    raw_chunks: List[str]
    cleaned_text: str
    sentences: List[str]
