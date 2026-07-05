# pylint: disable=too-many-arguments, too-many-positional-arguments, wrong-import-position
"""This is the DEV UI for testing and development purposes. It is not meant for production use."""

import traceback
import warnings


def warn_with_traceback(message, category, filename, lineno, file=None, line=None):
    """Custom warning handler that prints the full stack trace for warnings."""
    log = traceback.format_stack()
    print(
        f"Warning triggered: {message}\nCategory: {category}\nFile: {file}, Filename: {filename}, "
        f"Line: {line}, Linenumber: {lineno}\nTraceback:\n{''.join(log)}"
    )


# Force all warnings to dump a full stack trace
warnings.showwarning = warn_with_traceback


from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv

from chat_engine.models.response import HUMAN_IN_THE_LOOP_STATUSES
from ui import callback
from ui.constants import Avatar
from ui.helper import (
    disable_chat_input,
    enable_chat_input,
    initialize_chat_engine,
    page_setup,
    repaint_message_history,
    setup_defaults,
)

# Mimic authenticated user
AUTH_CONTEXT = {"authenticated": True, "username": "john.doe"}

# 1. INITIAL SETUP: Only runs once per session
if "initialized" not in st.session_state:
    load_dotenv()  # Load environment variables from .env file
    # Initial state configuration
    setup_defaults()

    # Set authentication context for the session (in a real app, this would come from your auth system)
    st.session_state.session_context.authenticated = AUTH_CONTEXT["authenticated"]
    st.session_state.session_context.username = AUTH_CONTEXT["username"]
    st.session_state.session_context.thread_id = str(uuid4())  # Unique identifier for the chat session/thread

    st.session_state.initialized = True


# 2. SETUP LAYER: General page setup and configuration (runs on every page load)
page_setup(AUTH_CONTEXT)
CHAT = initialize_chat_engine()


# 3. INTERACTION LAYER: Runs on every user interaction
callback = callback.StreamlitCallback()
with st.container(border=True, width="stretch", height="stretch", gap="small", key="chat-container"):

    # Display chat messages from history
    messages_box = st.container(border=True, width="stretch", height="stretch", gap="small", key="messages_box")

    repaint_message_history(messages_box, st.session_state.chat_history)

    # React to user input
    ai_response_placeholder = st.empty()

    if prompt := st.chat_input(
        "Ask me anything about parking reservations!",
        disabled=st.session_state.processing,
        on_submit=disable_chat_input,
        key="chat-input",
    ):
        st.session_state.processing = True  # Disable input while processing the current request
        ai_response_placeholder = ""

        # Store and display the user's query
        msg = {"role": "user", "content": prompt}
        st.session_state.chat_history.append(msg)
        repaint_message_history(messages_box, [msg])  # Repaint history to include the new user message

        with st.chat_message("assistant", avatar=Avatar.ASSISTANT.value):
            status_bar = st.status(label="Thinking...", state="running", expanded=False)
            msg_placeholder = st.empty()
            full_formatted_msg = ""  # Accumulator for the full response content

            try:
                # Streaming response handling
                stream_response = CHAT.stream_chat(
                    prompt=prompt,
                    history=st.session_state.chat_history[:-1],  # Exclude the current user message from history
                    session_context=st.session_state.session_context,
                )
                for chunk in stream_response:
                    # Update the processing status
                    chunk_status = getattr(chunk, "status", None)
                    chunk_content = getattr(chunk, "content", None)
                    if chunk_status:
                        new_status = chunk.status.value
                        is_complete = chunk.status in HUMAN_IN_THE_LOOP_STATUSES
                        status_bar.update(label=chunk.status.value, state="complete" if is_complete else "running")

                    # Display and store the response chunks
                    if chunk_content:
                        formatted_chunk = callback.display_content(chunk_content, mode=chunk_status.name)
                        full_formatted_msg += formatted_chunk
            except Exception as error:  # pylint: disable=broad-except
                st.error(f"An error occurred while processing your request: {error}")
                st.write(st.session_state.default_msg.get(error))

            if full_formatted_msg:
                st.session_state.chat_history.append({"role": "assistant", "content": full_formatted_msg})

            status_bar.update(label="Done", state="complete", expanded=False)

        enable_chat_input()
        st.rerun()  # Refresh the app to reflect the updated state
