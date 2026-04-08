from types import GeneratorType
from typing import Any

import streamlit as st
from langchain.messages import AIMessage, AIMessageChunk

from chat_engine.core.tools.patterns import Singleton
from ui.utils import format_html


class StreamlitCallback(metaclass=Singleton):

    def display_content(self, message: Any) -> Any:
        # Placeholder for Streamlit-specific callback logic
        msg_type = type(message).__name__

        formatted_msg = ""
        # Handling different type of message
        if isinstance(message, str):
            formatted_msg = self._update_ui(message)
        elif isinstance(message, (AIMessage, AIMessageChunk)):
            formatted_msg = self._update_ui(message.content)
        elif isinstance(message, (list, GeneratorType)):
            formatted_msg = self._update_ui(message)
        else:
            st.warning(f"Received message of unhandled type: {msg_type}")

        return formatted_msg

    def _update_ui(self, message: Any) -> Any:
        # Internal method for UI updates, can be called by update_ui
        formatted_msg = ""
        msg_placeholder = st.empty()
        if isinstance(message, (list, GeneratorType)):
            full_response = ""
            for chunk in message:
                if isinstance(chunk, str):
                    full_response += format_html(chunk)
                elif isinstance(chunk, (AIMessage, AIMessageChunk)):
                    full_response += format_html(chunk.content)

                msg_placeholder.markdown(format_html(full_response) + "**|**", unsafe_allow_html=True)

            formatted_msg = format_html(full_response)
        elif isinstance(message, str):
            formatted_msg = format_html(message)
            msg_placeholder.markdown(formatted_msg, unsafe_allow_html=True)

        msg_placeholder.write(formatted_msg, unsafe_allow_html=True)
        return formatted_msg
