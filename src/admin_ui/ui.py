# pylint: disable=unnecessary-lambda
import streamlit as st

from admin_ui.css import get_custom_style
from admin_ui.utils import get_reservation_data, search_and_filter_reservations
from chat_engine.models.enums import ReservationStatus


def page_setup():
    """Set up the Streamlit page configuration."""

    st.set_page_config(
        page_title="APSR - Admin UI",
        page_icon="👷",
        layout="wide",
    )

    # ========== UI Styling ==========
    st.html(get_custom_style())

    # ========== Main page content ==========
    st.title("APSR - Admin UI", anchor="main-title", width="stretch", text_alignment="center")

    st.subheader("AI Parking Space Reservation System", divider="gray", width="stretch")
    st.markdown("##### **⚠️ For authorized personnel only ⚠️**", unsafe_allow_html=True)
    st.write(
        "> This admin interface allows you to review and manage parking space reservation requests.<br>"
        "Please ensure that you have the necessary permissions to access this page.",
        unsafe_allow_html=True,
    )

    # ========== Sidebar content ==========
    st.sidebar.title("Admin Controls")
    st.sidebar.markdown(
        "Use the controls below to search and filter the reservation requests and view system analytics.<br>"
        "Make sure to refresh the data regularly to see the latest reservation requests.",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    st.sidebar.button("Refresh Data", on_click=lambda: get_reservation_data())
    refresh_date = f"_Last refreshed: {st.session_state.get('last_refreshed', 'N/A')}_"
    st.sidebar.markdown(
        f":grey[{refresh_date}]",
    )

    st.sidebar.markdown("---")
    st.sidebar.selectbox(
        "**Filter by Status:**",
        options=["- All statuses -"] + [rs.value for rs in ReservationStatus],
        on_change=lambda: search_and_filter_reservations(),
        key="status_filter",
    )

    st.sidebar.text_input(
        "**Search by 'username' or 'parking_lot_id':**",
        key="search_input",
        on_change=lambda: search_and_filter_reservations(),
    )
