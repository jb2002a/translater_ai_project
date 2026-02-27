# This module contains functions for pre-processing text, such as cleaning and formatting, to make it suitable for translation.

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import langsmith
from langchain_core.messages import SystemMessage, HumanMessage
from ..prompts.prompts import GERMAN_OCR_RESTORATION_PROMPT
import sqlite3
from ...models import models
from ...exceptions import (
    CleanupChunkError,
    DatabaseError,
    LLMProviderError,
    TranslaterAIError,
)

load_dotenv()

# Gemini 기준 대략 4자당 1토큰 (배치 용도 추정)
DEFAULT_CHARS_PER_TOKEN = 4


def _estimate_tokens(text: str, chars_per_token: int = DEFAULT_CHARS_PER_TOKEN) -> int:
    return max(1, len(text) // chars_per_token)


def rebatch_chunks_by_tokens(
    raw_chunks: list[str],
    max_tokens: int = 50_000,
    chars_per_token: int = DEFAULT_CHARS_PER_TOKEN,
) -> list[str]:
    """
    raw_chunks를 토큰 수 기준으로 묶어, 배치당 max_tokens 이하인 문자열 리스트로 반환.
    순서 유지, 그리디 first-fit. 반환값은 배치별로 '\n'.join된 문자열 리스트.
    """
    if not raw_chunks:
        return []
    batches: list[list[str]] = []
    current_batch: list[str] = []
    current_tokens = 0

    for chunk in raw_chunks:
        chunk_tokens = _estimate_tokens(chunk, chars_per_token)
        if current_tokens + chunk_tokens > max_tokens and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0
        current_batch.append(chunk)
        current_tokens += chunk_tokens

    if current_batch:
        batches.append(current_batch)

    return ["\n".join(batch) for batch in batches]


# 단일 텍스트 cleanup (LLM 호출). LangSmith는 env 설정으로 자동 트레이싱.
def cleanup_text(text):
    messages = [
        SystemMessage(content=GERMAN_OCR_RESTORATION_PROMPT),
        HumanMessage(content=text),
    ]
    try:
        chat = models.get_chat_model_google()
        processed_text = chat.invoke(messages)
        return processed_text.content
    except TranslaterAIError:
        raise
    except Exception as e:
        raise LLMProviderError("Google LLM cleanup 호출 실패", cause=e) from e


def cleanup_chunks_parallel(raw_chunks: list[str]) -> list[str]:
    """
    청크 리스트를 병렬로 cleanup한 뒤, 원본 순서대로 정리된 문자열 리스트를 반환.

    - 목적: 전체 raw_text를 한 번에 LLM에 넣으면 출력 토큰 제한으로 잘리므로,
      chunking_node에서 문장 단위로 나눈 raw_chunks를 청크별로 병렬 cleanup.
    - 동작: 각 청크에 대해 cleanup_text(탈하이픈, 정서법, 노이즈 제거 등)를
      ThreadPoolExecutor로 동시에 호출하고, 원본 순서를 유지한 리스트로 반환.
    - 반환: 청크 순서대로 정리된 문자열 리스트. cleanup_node에서 그대로
      state["sentences"]로 넣고 save_db_node에서 사용.
    """
    if not raw_chunks:
        return []
    cleaned_list = [None] * len(raw_chunks)

    def process(i: int, chunk: str):
        return i, cleanup_text(chunk)

    # cleanup 노드는 1회 실행되며, 내부에서 청크별 cleanup_text(LLM)를 병렬 호출.
    # LangSmith: 이 구간은 트레이싱 제외 (랭그래프만 추적)
    with langsmith.tracing_context(enabled=False):
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process, i, c): i for i, c in enumerate(raw_chunks)}
            for fut in as_completed(futures):
                try:
                    i, content = fut.result()
                    cleaned_list[i] = content
                except Exception as e:
                    idx = futures.get(fut)
                    raise CleanupChunkError(
                        f"청크 cleanup 실패 (chunk_index={idx})",
                        chunk_index=idx,
                        cause=e,
                    ) from e
    return cleaned_list


# 데이터베이스에 저장하는 함수
def save_to_db(pdf_path, author, book_title, sentences):
    try:
        conn = sqlite3.connect("philosophy_translation.db")
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_sentences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_path TEXT,
                author TEXT,
                book_title TEXT,
                german_sentence TEXT,
                status TEXT DEFAULT 'pending'
            )
        """
        )

        data = [(pdf_path, author, book_title, s) for s in sentences]
        cur.executemany(
            """
            INSERT INTO processed_sentences (pdf_path, author, book_title, german_sentence)
            VALUES (?, ?, ?, ?)
        """,
            data,
        )

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise DatabaseError("DB 저장 실패 (philosophy_translation.db)", cause=e) from e
