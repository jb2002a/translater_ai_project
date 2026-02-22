from typing import TypedDict, List


class GraphState(TypedDict):
    pdf_path: str
    author: str
    book_title: str
    raw_text: str
    cleaned_text: str
    sentences: List[str]  # 문장 단위로 나눈 텍스트
