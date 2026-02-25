# This module contains functions for pre-processing text, such as cleaning and formatting, to make it suitable for translation.

import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from ..prompts.prompts import GERMAN_OCR_RESTORATION_PROMPT, REFACTORING_PROMPT
import sqlite3
from ...models import models

load_dotenv()


# 전처리 함수와 리펙터링 함수는 pre_prcess의 prompts.py에 정의된 프롬프트를 사용.


# 전처리 함수
def pre_process_text(text):
    messages = [
        SystemMessage(content=GERMAN_OCR_RESTORATION_PROMPT),
        HumanMessage(content=text),
    ]

    chat = models.get_chat_model_google()

    processed_text = chat.invoke(messages)

    return processed_text.content


# 리펙터링 함수
def refractor_text(text):
    messages = [
        SystemMessage(content=REFACTORING_PROMPT),
        HumanMessage(content=text),
    ]
    chat = models.get_chat_model_google()
    refractored_text = chat.invoke(messages)
    return refractored_text.content


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
