# This file handles the initial translation of pre-processed German text into Korean

from langchain_core.messages import SystemMessage, HumanMessage
from .prompts import TRANSLATION_PROMPT
from ..models import models
from dotenv import load_dotenv
import os


load_dotenv()  # Load environment variables from .env file


# config가 있으면 그래프에서 내려온 콜백 사용(중복 트레이싱 방지), 없으면 여기서 핸들러 생성
def initial_translate(text, author, book_title, config=None):
    chat = models.get_chat_model_anthropic()
    if config is None:
        h = models.get_langfuse_handler()
        config = {"callbacks": [h]} if h else {}

    system_prompt = TRANSLATION_PROMPT.format(AUTHOR=author, BOOK_TITLE=book_title)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=text)]

    response = chat.invoke(messages, config=config)

    return response.content
