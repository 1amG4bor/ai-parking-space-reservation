import time

import pandas as pd
import streamlit as st

from chat_engine.core.utils.db_tool import DatabaseService
from chat_engine.models.enums import ReservationStatus


def get_reservation_data():
    """Fetch reservation data from the database."""

    with st.spinner("Loading reservations......", show_time=True):
        # Clear the existing data
        st.session_state.all_reservations = []
        st.session_state.filtered_reservations = []
        # st.rerun()  # Trigger a rerun to update the UI with the loading state
        time.sleep(1)  # Simulate loading time

        db_service = DatabaseService()
        reservation_data = db_service.get_all_reservations()

        parsed_data = []
        columns = [
            "status",
            "reservation_id",
            "reservation_time",
            "username",
            "parking_lot_id",
            "parking_space_category",
            "start_time",
            "end_time",
            "vehicle_model",
            "vehicle_type",
            "license_plate",
            "fuel_type",
        ]
        for reservation in reservation_data:
            parsed_data.append(
                {
                    "status": reservation.status.value,
                    "reservation_id": reservation.reservation_id,
                    "reservation_time": reservation.reservation_time,
                    "username": reservation.user.username,
                    "parking_lot_id": reservation.parking_lot_id,
                    "parking_space_category": reservation.parking_space_category,
                    "start_time": reservation.start_time,
                    "end_time": reservation.end_time,
                    "vehicle_model": reservation.vehicle.model,
                    "vehicle_type": reservation.vehicle.type.value,
                    "license_plate": reservation.vehicle.license_plate,
                    "fuel_type": reservation.vehicle.fuel_type.value,
                }
            )
        reservation_df = pd.DataFrame(data=parsed_data, columns=columns)
        st.session_state.last_refreshed = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        st.session_state.all_reservations = reservation_df
        search_and_filter_reservations()  # Apply current filters/search to the new data


def search_and_filter_reservations():
    """Search & Filter reservations based on the status and search query."""
    status_filter = st.session_state.get("status_filter", "ALL")
    search_query = st.session_state.get("search_input", "").strip()

    print(f"Filtering reservations by status: {status_filter}")
    if status_filter not in [rs.value for rs in ReservationStatus]:
        filtered_df = st.session_state.all_reservations
    else:
        all_df = st.session_state.all_reservations
        filtered_df = all_df[all_df["status"] == status_filter]

    if search_query:
        search_query_lower = search_query.lower()
        filtered_df = filtered_df[
            filtered_df.apply(
                lambda row: search_query_lower in str(row["username"]).lower()
                or search_query_lower in str(row["parking_lot_id"]).lower(),
                axis=1,
            )
        ]
    st.session_state.filtered_reservations = filtered_df


def get_reservation_in_html(reservation):
    """Display details of the selected reservation."""
    status_colors = {
        "Pending": ["orange", "black"],
        "Booked": ["lightgreen", "black"],
        "Cancelled": ["white", "black"],
        "Completed": ["green", "white"],
    }

    return f"""
### Reservation Details
<div class="reservation-status" style="
    background-color: {status_colors.get(reservation['status'], ['black', 'white'])[0]};
    color: {status_colors.get(reservation['status'], ['black', 'white'])[1]};
">
    STATUS: {reservation['status']}
</div>
<ul>
    <li><strong>Reservation ID</strong>: {reservation['reservation_id']}</li>
    <li><strong>Username</strong>: {reservation['username']}</li>
    <li><strong>Parking Lot ID</strong>: {reservation['parking_lot_id']}</li>
    <li><strong>Parking Space Category</strong>: {reservation['parking_space_category']}</li>
    <li><strong>Start Time</strong>: {reservation['start_time']}</li>
    <li><strong>End Time</strong>: {reservation['end_time']}</li>
    <li><strong>Vehicle Model</strong>: {reservation['vehicle_model']}</li>
    <li><strong>Vehicle Type</strong>: {reservation['vehicle_type']}</li>
    <li><strong>License Plate</strong>: {reservation['license_plate']}</li>
    <li><strong>Fuel Type</strong>: {reservation['fuel_type']}</li>
</ul>
"""


def update_reservation(reservation_id, new_status):
    """Update the status of a reservation."""
    with st.spinner("Updating reservations......", show_time=True):
        st.session_state.refreshing = True
        if new_status == "Booked":
            status = ReservationStatus.BOOKED
        elif new_status == "Cancelled":
            status = ReservationStatus.CANCELLED
        else:
            st.warning(f"Unsupported status update: {new_status}")
            return

        db_service = DatabaseService()
        db_service.update_reservation_status(reservation_id, status)
        # Refresh data after update
        get_reservation_data()
        st.session_state.refreshing = False
