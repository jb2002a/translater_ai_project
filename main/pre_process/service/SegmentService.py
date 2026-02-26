# SoMaJo 기반 문장 경계 분리 (독일어 de_CMC)
from typing import List
from somajo import SoMaJo


def segment_raw_to_list(text: str) -> List[str]:
    """raw_text를 문장 단위로 나누어 청크 리스트로 반환 (청킹 → 병렬 cleanup용).
    줄바꿈 정규화는 extract 단계에서 이미 적용된 raw_text를 받습니다."""
    if not text or not text.strip():
        return []
    tokenizer = SoMaJo(language="de_CMC", split_camel_case=False)
    # 문단 구분: 빈 줄 기준으로 나누고, 없으면 전체를 한 문단으로
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()] or [text]
    sentences = []
    for sentence_tokens in tokenizer.tokenize_text(paragraphs):
        sentence_str = " ".join(t.text for t in sentence_tokens)
        if sentence_str.strip():
            sentences.append(sentence_str)
    return sentences


def segment_cleaned_text(text: str) -> str:
    """독일어 cleaned_text를 문장 단위로 나누어 한 문장 per line 문자열로 반환."""
    chunks = segment_raw_to_list(text)
    return "\n".join(chunks) if chunks else ""
