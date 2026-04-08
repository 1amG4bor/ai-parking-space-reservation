import streamlit as st

from ui.constants import Avatar

chat_defaults = {
    "greeting": [{"role": Avatar.AI.value, "content": "Hello! How can I help you today?"}],
    "thinking": [{"role": Avatar.AI.value, "content": "Let me think and check it for you."}],
    # TBD: Add more default messages
    "error": [{"role": Avatar.AI.value, "content": "Sorry, something went wrong. Please try again."}],
    "chat_history": [],
}

for id, message in chat_defaults.items():
    st.session_state.setdefault(id, message)

def page_setup():
    """Set up the Streamlit page configuration."""
    st.set_page_config(
        page_title="AI Parking Reservation",
        page_icon="🅿️",
        layout="centered",
        initial_sidebar_state="expanded",
    )

    # Sidebar settings
    st.sidebar.header("Settings")
    DESTINATION = st.sidebar.text_input(
        "Enter your target destination:",
        value="",
        placeholder="e.g., Budapest Airport, Train Station",
    )

    st.title("AI Parking Reservation", anchor="main-title")
    st.markdown(
        """
    > Welcome to the AI Parking Reservation System!<br>
    Let me help you find the perfect parking spot based on your target destination and preferences.""",
        unsafe_allow_html=True,
    )