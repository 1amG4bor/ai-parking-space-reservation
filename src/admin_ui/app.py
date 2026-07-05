"""Admin UI Interface for parking space reservation request approval."""

import streamlit as st
from dotenv import load_dotenv

from admin_ui.ui import page_setup
from admin_ui.utils import get_reservation_data, get_reservation_in_html, update_reservation

# Mimic authenticated user
AUTH_CONTEXT = {"authenticated": True, "username": "ADMIN"}

# 1. INITIAL SETUP: Only runs once per session
if "initialized" not in st.session_state:
    load_dotenv()  # Load environment variables from .env file

    st.session_state.all_reservations = []
    st.session_state.filtered_reservations = []
    st.session_state.selected_reservation = None
    st.session_state.reservation_status_finalized = True

    st.session_state.refreshing = False
    st.session_state.last_refreshed = None
    st.session_state.search_input = ""
    get_reservation_data()
    st.session_state.initialized = True


page_setup()

st.markdown("## Reservations Overview")

st.write("Select a reservation to view details and approve or reject the request.")
reservation_data = st.session_state.filtered_reservations
event = st.dataframe(
    reservation_data, width="stretch", height="stretch", selection_mode="single-cell", on_select="rerun"
)

if event.selection and event.selection.cells:
    if reservation_data.empty:
        st.write("No reservations found.")
    with st.container(
        border=True,
    ):
        st.markdown("### Reservation Details")
        idx = event.selection.cells[0][0]
        selected_reservation = reservation_data.iloc[idx]

        with st.container(horizontal=True, horizontal_alignment="left", gap="small"):

            is_status_finalized = selected_reservation["status"].upper() != "PENDING"
            st.session_state.reservation_status_finalized = is_status_finalized
            st.button(
                "Approve",
                key="success-btn",
                disabled=is_status_finalized,
                on_click=lambda: update_reservation(selected_reservation["reservation_id"], "Booked"),
            )
            st.button(
                "Reject",
                key="danger-btn",
                disabled=is_status_finalized,
                on_click=lambda: update_reservation(selected_reservation["reservation_id"], "Cancelled"),
            )

        reservation_details_placeholder = st.container(
            border=True, width="stretch", height="stretch", gap="small", key="reservation-details"
        )
        reservation_details_placeholder.markdown(get_reservation_in_html(selected_reservation), unsafe_allow_html=True)
