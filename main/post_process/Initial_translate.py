# This file handles the initial translation of pre-processed German text into Korean

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from .prompts import TRANSLATION_PROMPT
from dotenv import load_dotenv
import os


load_dotenv()  # Load environment variables from .env file


def initial_translate(text, author, book_title):
    # Initialize the Anthropic chat model
    chat = ChatAnthropic(
        model="claude-sonnet-4-5-20250929", api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # Define the system prompt for translation
    system_prompt = TRANSLATION_PROMPT.format(AUTHOR=author, BOOK_TITLE=book_title)

    # Create the messages for the chat model
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=text)]

    # Call the chat model with the messages
    response = chat.invoke(messages)

    return response.content
