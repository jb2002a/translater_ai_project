# This module contains functions for pre-processing text, such as cleaning and formatting, to make it suitable for translation.

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from ..prompts.prompts import GERMAN_OCR_RESTORATION_PROMPT
import sqlite3
from ...models import models

load_dotenv()


# 전처리 함수 (단일 텍스트)
# config가 있으면 그래프에서 내려온 콜백 사용(중복 트레이싱 방지), 없으면 여기서 핸들러 생성
def pre_process_text(text, config=None):
    messages = [
        SystemMessage(content=GERMAN_OCR_RESTORATION_PROMPT),
        HumanMessage(content=text),
    ]

    chat = models.get_chat_model_google()
    if config is None:
        h = models.get_langfuse_handler()
        config = {"callbacks": [h]} if h else {}

    processed_text = chat.invoke(messages, config=config)

    return processed_text.content


def pre_process_chunks_parallel(raw_chunks: list[str], config=None) -> str:
    """
    청크 리스트를 병렬로 전처리한 뒤, 한 문장 per line 문자열로 반환.

    - 목적: 전체 raw_text를 한 번에 LLM에 넣으면 출력 토큰 제한으로 잘리므로,
      chunking_node에서 문장 단위로 나눈 raw_chunks를 청크별로 병렬 cleanup.
    - 동작: 각 청크에 대해 pre_process_text(탈하이픈, 정서법, 노이즈 제거 등)를
      ThreadPoolExecutor로 동시에 호출하고, 원본 순서를 유지한 채 이어 붙임.
    - 반환: 청크 순서대로 정리된 문자열(줄바꿈 구분). cleanup_node에서 split하여
      state["sentences"]로 넣고 save_db_node에서 사용.
    - config: 그래프에서 내려온 RunnableConfig. 넘기면 같은 콜백으로 트레이싱(중복 방지).
    """
    if not raw_chunks:
        return ""
    cleaned_list = [None] * len(raw_chunks)

    def process(i: int, chunk: str):
        return i, pre_process_text(chunk, config=config)  # 청크별 LLM 호출

    # cleanup 노드는 1회 실행되며, 내부에서 청크별 pre_process_text(LLM)를 병렬 호출
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process, i, c): i for i, c in enumerate(raw_chunks)}
        for fut in as_completed(futures):
            i, content = fut.result()
            cleaned_list[i] = content
    return "\n".join(cleaned_list)


# 데이터베이스에 저장하는 함수
def save_to_db(pdf_path, author, book_title, sentences):
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
