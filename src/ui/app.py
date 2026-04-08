import streamlit as st

from chat_engine.engine import ChatEngine
from chat_engine.models.response import ResponseStatus, HUMAN_IN_THE_LOOP_STATUSES
from ui import callback
from ui.constants import Avatar
from ui.components.page import page_setup


CHAT = ChatEngine()
APP_STATE = {"chunks": [], "reservation_data": {}}


# Page setup and initial state configuration
page_setup()

callback = callback.StreamlitCallback()

# MESSAGES = st.chat_message("assistant", avatar=Avatar.AI.value)
if hasattr(st.session_state, "chat_history") and len(st.session_state.chat_history) == 0:
    st.session_state.chat_history.extend(st.session_state.greeting)

# Display chat messages from history on app rerun
if st.session_state.chat_history:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


if prompt := st.chat_input("Ask me anything about parking reservations:"):
    with st.chat_message("user", avatar=Avatar.USER.value):
        # Display and store the user's message
        msg = {"role": Avatar.USER.value, "content": prompt}
        st.markdown(prompt, unsafe_allow_html=True)
        st.session_state.chat_history.append(msg)

    
    with st.chat_message("assistant", avatar=Avatar.AI.value):
        status_bar = st.status(label="Thinking...", state="running", expanded=False)
        msg_placeholder = st.empty()
        full_formatted_msg = ""  # Accumulator for the full response content
        
        try:
            # Streaming response handling
            stream_response = CHAT.stream_chat(prompt, st.session_state.chat_history)
            for chunk in stream_response:
                # Update the processing status
                if hasattr(chunk, "status") and chunk.status:
                    new_status = chunk.status.value
                    is_complete = chunk.status in HUMAN_IN_THE_LOOP_STATUSES
                    status_bar.update(label=chunk.status.value, state="complete" if is_complete else "running")
                
                # Display and store the response chunks
                if hasattr(chunk, "content") and chunk.content:
                    formatted_chunk = callback.display_content(chunk.content)
                    full_formatted_msg += formatted_chunk
        except Exception as error:
            st.error(f"An error occurred while processing your request: {error}")
            st.write(st.session_state.error)
            

        if full_formatted_msg:
            st.session_state.chat_history.append({"role": Avatar.AI.value, "content": full_formatted_msg})
        
        if status_bar.label == ResponseStatus.STOP.value:
            status_bar.update(label="Done", state="complete", expanded=False)
