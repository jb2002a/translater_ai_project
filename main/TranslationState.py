from typing import List, Tuple, TypedDict


class GraphState(TypedDict, total=False):
    """전처리(Pre-processing) 그래프 전용 state."""
    pdf_path: str
    db_path: str
    author: str
    book_title: str
    raw_text: str
    raw_chunks: List[str]
    batched_chunks: List[str]
    cleaned_batches: List[str]
    german_sentences: List[str]


class PostTranslationState(TypedDict, total=False):
    """후처리(번역) 그래프 전용 state."""
    db_path: str
    author: str
    book_title: str
    pending_items: List[Tuple[int, str]]
    translated_items: List[Tuple[int, str]]
    last_saved_count: int
