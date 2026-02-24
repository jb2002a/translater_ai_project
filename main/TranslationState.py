from typing import TypedDict, List


class GraphState(TypedDict):
    pdf_path: str
    author: str
    book_title: str
    raw_text: str
    cleaned_text: str
    refractored_text: str
