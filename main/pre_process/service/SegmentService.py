# PySBD 기반 문장 경계 분리
from typing import List
import pysbd


def segment_raw_to_list(text: str) -> List[str]:
    """raw_text를 문장 단위로 나누어 청크 리스트로 반환 (청킹 → 병렬 cleanup용)."""
    if not text or not text.strip():
        return []
    seg = pysbd.Segmenter(language="de", clean=False)
    return seg.segment(text)


def segment_cleaned_text(text: str) -> str:
    """독일어 cleaned_text를 문장 단위로 나누어 한 문장 per line 문자열로 반환."""
    chunks = segment_raw_to_list(text)
    return "\n".join(chunks) if chunks else ""
