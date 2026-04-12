from types import GeneratorType
from typing import Any

import streamlit as st
from langchain.messages import AIMessage, AIMessageChunk

from chat_engine.core.utils.patterns import Singleton
from ui.utils import format_html

from chat_engine.core.config.logging import logger

class StreamlitCallback(metaclass=Singleton):

    def __init__(self):
        self.msg_placeholder = None
        self.last_write_mode = None
        self.full_response = None


    def display_content(self, message: Any, mode: str, placeholder: Any = None) -> Any:
        msg_type = type(message).__name__
        if placeholder:
            self.msg_placeholder = placeholder

        formatted_msg = ""
        # Handling different type of message
        if isinstance(message, str):
            formatted_msg = self._update_ui(message, mode)
        elif isinstance(message, (AIMessage, AIMessageChunk)):
            formatted_msg = self._update_ui(message.content, mode)
        elif isinstance(message, (list, GeneratorType)):
            formatted_msg = self._update_ui(message, mode)
        else:
            st.warning(f"Received message of unhandled type: {msg_type}")

        return formatted_msg

    def _update_ui(self, message: Any, mode: str = "GENERATING") -> Any:
        # Internal method for UI updates, can be called by update_ui
        if not self.msg_placeholder:
            self.msg_placeholder = st.empty()
        full_response = self.full_response or ""

        if isinstance(message, (list, GeneratorType)):
            msg_chunks = ""
            for chunk in message:
                if isinstance(chunk, str):
                    msg_chunks += format_html(chunk)
                elif isinstance(chunk, (AIMessage, AIMessageChunk)):
                    msg_chunks = format_html(msg_chunks +chunk.content)
                self.msg_placeholder.markdown(format_html(full_response + msg_chunks) + "┃", unsafe_allow_html=True)

            formatted_msg = msg_chunks
        elif isinstance(message, str):
            formatted_msg = format_html(message)
            formatted_msg = formatted_msg.replace("\n", "<br>")
            self.msg_placeholder.markdown(format_html(full_response + formatted_msg) + "┃", unsafe_allow_html=True)
        
        
        self.full_response = full_response + formatted_msg
        self.last_write_mode = mode

        return formatted_msg
