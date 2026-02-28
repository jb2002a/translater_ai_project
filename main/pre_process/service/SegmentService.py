# SoMaJo 기반 문장 경계 분리 (독일어 de_CMC)
from typing import List
from somajo import SoMaJo

from ...exceptions import SegmentError

# SoMaJo 기반 문장 경계 분리
def segment_raw_to_list(text: str) -> List[str]:
    # LLM 등에서 list가 넘어올 수 있음: 한 문자열로 정규화
    if isinstance(text, list):
        text = " ".join(str(t) for t in text)
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
                sentences.append(sentence_str)
        return sentences
    except Exception as e:
        raise SegmentError("SoMaJo 문장 분리 실패", cause=e) from e
