import streamlit as st

from chat_engine.core.agents.agent_models import ApsrSessionContext
from chat_engine.core.utils.db_tool import DatabaseService
from chat_engine.engine.apsr_chat_engine import ChatEngine  # pylint: disable=no-name-in-module
from ui.constants import Avatar, parking_preferences


def page_setup(context: dict = None):
    """Set up the Streamlit page configuration."""

    st.set_page_config(
        page_title="AI Parking Reservation",
        page_icon="🅿️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ========== UI Styling ==========
    chat_input_display_style = "none" if st.session_state.processing is True else "block"
    st.html(f"""
<style>
.stAppHeader {{ background-color: #559FF2dd; color: white; }}
.st-key-chat-input {{ display: {chat_input_display_style}; }}
</style>
""")

    # ========== Main page content ==========
    st.title("AI Parking Reservation", anchor="main-title", width="stretch", text_alignment="center")
    st.markdown(
        """
    **Welcome to the AI Parking Reservation System!**<br>
    Let me help you find the perfect parking spot based on your target destination and preferences.""",
        unsafe_allow_html=True,
    )

    # ========== Sidebar settings ==========
    set_sidebar(context)


def set_sidebar(context):
    _user_data = get_user_data(context)
    st.sidebar.header("Settings")
    st.sidebar.markdown("_The following settings help the AI to give you more accurate recommendations._")
    st.sidebar.markdown(f"---\n> **Logged in as:** {context['username']}")

    vehicle_options = {
        f"{vehicle.model} - {vehicle.license_plate} | {vehicle.type.value} ({vehicle.fuel_type.value})": vehicle.id
        for vehicle in _user_data.vehicles
    }
    vehicle_selection = st.sidebar.selectbox(
        "Select the used vehicle:",
        options=list(vehicle_options.keys()),
        index=0,
    )
    st.sidebar.button("Add new vehicle", disabled=True)  # Placeholder for future functionality

    location_selection = st.sidebar.selectbox(
        "Select your departure location:",
        options=[f"{l.address}, {l.city} {l.zip_code}" for l in _user_data.locations],
        index=0,
    )
    st.sidebar.button("Add new location", disabled=True)  # Placeholder for future functionality

    parking_preferences_selection = st.sidebar.multiselect(
        "Select your parking preferences:",
        options=parking_preferences,
        default=[pref.type.value for pref in _user_data.preferences],
        placeholder="Choose your preferences",
    )

    st.session_state.session_context.vehicle_id = vehicle_options.get(vehicle_selection)
    st.session_state.session_context.selected_vehicle = vehicle_selection
    st.session_state.session_context.selected_location = location_selection
    st.session_state.session_context.selected_preferences = parking_preferences_selection


def setup_defaults():
    """Set up default values for the session state."""
    # Define default messages
    default_messages = {
        "greeting": {"role": "assistant", "content": "Hello! How can I help you today? 🙂"},
        "confirmation": {"role": "assistant", "content": "Your reservation need to be confirmed, please wait."},
        "confirmed": {"role": "assistant", "content": "Your parking spot has been reserved!"},
        # TBD: Add more default messages
        "error": {"role": "system", "content": "Sorry, something went wrong. Please try again."},
    }
    st.session_state.default_msg = {}
    for key, message in default_messages.items():
        st.session_state.default_msg.setdefault(key, message)

    st.session_state.session_context = ApsrSessionContext()
    st.session_state.processing = False
    st.session_state.chat_history = []
    st.session_state.chat_history.append(default_messages["greeting"])


@st.cache_resource(show_spinner="Loading the chat engine...")
def initialize_chat_engine():
    """Initialize the ChatEngine instance as a cached resource."""
    return ChatEngine()


@st.cache_resource(show_spinner="Collecting user data...")
def get_user_data(context: dict):
    """Fetch user data from the database based on the provided context."""
    db_service = DatabaseService()
    user_data = db_service.get_user_by_username(context["username"])
    return user_data


# ========== Helper functions ==========
def disable_chat_input():
    """Utility function to disable the chat input widget."""
    st.session_state.processing = True


def enable_chat_input():
    """Utility function to enable the chat input widget."""
    st.session_state.processing = False


def repaint_message_history(messages_box, messages):
    """Utility function to repaint the chat history with additional messages."""
    message_list = messages if isinstance(messages, list) else [messages]
    with messages_box:
        for message in message_list:
            role = message["role"]
            avatar = Avatar.parse(role)
            with st.chat_message(role, avatar=avatar.value if avatar else None):
                st.markdown(message["content"], unsafe_allow_html=True)
