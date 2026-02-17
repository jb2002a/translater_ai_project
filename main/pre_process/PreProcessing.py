# This module contains functions for pre-processing text, such as cleaning and formatting, to make it suitable for translation.

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from . import PdfToTextConvert as Convert
from .prompts import GERMAN_OCR_RESTORATION_PROMPT, REFACTORING_PROMPT

chat = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY")
)


def pre_process_text(text):
    # Pre-process the text to make it suitable for translation.

    messages = [
        SystemMessage(content=GERMAN_OCR_RESTORATION_PROMPT),
        HumanMessage(content=text),
    ]

    processed_text = chat.invoke(messages)

    return processed_text.content


def refractor_text(text):
    messages = [
        SystemMessage(content=REFACTORING_PROMPT),
        HumanMessage(content=text),
    ]

    refractored_text = chat.invoke(messages)

    return refractored_text.content
