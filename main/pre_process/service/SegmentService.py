# SoMaJo 기반 문장 경계 분리 (독일어 de_CMC)
from typing import List
from somajo import SoMaJo

from ...exceptions import SegmentError


def segment_raw_to_list(text: str) -> List[str]:
    """raw_text를 문장 단위로 나누어 청크 리스트로 반환 (청킹 → 병렬 cleanup용).
    청킹 단위 사이에 \\n을 넣어 반환하며, 줄바꿈 정규화는 extract 단계에서 이미 적용된 raw_text를 받습니다."""
    if not text or not text.strip():
        return []
    try:
        tokenizer = SoMaJo(language="de_CMC", split_camel_case=False)
        # 문단 구분: 빈 줄 기준으로 나누고, 없으면 전체를 한 문단으로
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()] or [text]
        sentences = []
        for sentence_tokens in tokenizer.tokenize_text(paragraphs):
            sentence_str = " ".join(t.text for t in sentence_tokens)
            if sentence_str.strip():
                sentences.append(sentence_str + "\n")
        if sentences:
            sentences[-1] = sentences[-1].rstrip("\n")
        return sentences
    except Exception as e:
        raise SegmentError("SoMaJo 문장 분리 실패", cause=e) from e
