from typing import List

from pydantic import BaseModel, Field


class ApsrSessionContext(BaseModel):
    """Context schema for the ReservationAgent, contains information about the user's session and preferences."""

    authenticated: bool = Field(default=False, description="Indicates whether the user is authenticated.")
    username: str = Field(default=None, description="The username of the authenticated user.")
    thread_id: str = Field(default=None, description="Unique identifier for the chat session/thread.")
    vehicle_id: int | None = Field(
        default=None, description="The ID of the vehicle selected by the user for reservation."
    )
    selected_vehicle: str = Field(
        default=None, description="Short description of the user's selected vehicle for the reservation."
    )
    selected_location: str = Field(
        default="", description="The user's selected departure location as the starting point of their trip."
    )
    selected_preferences: List[str] = Field(
        default_factory=list,
        description="List of preferences chosen by the user for the current search and reservation process.",
    )


class ReservationAgentState(BaseModel):
    """State schema for the ReservationAgent, contains all the important information during the agent's operation."""

    # Permanent user data
    locations: List[dict] = Field(default_factory=list, description="List of locations associated with the user.")
    vehicles: List[dict] = Field(default_factory=list, description="List of vehicles associated with the user.")
    preferences: List[dict] = Field(
        default_factory=list, description="List of user preferences that may influence reservation suggestions."
    )
    reservation_history: List[dict] = Field(
        default_factory=list, description="List of past reservations made by the user."
    )
    # Session-specific data
    retrieved_parking_info: List[dict] = Field(
        default_factory=list, description="List of retrieved parking information relevant to the user's query."
    )
    current_reservation_details: dict = Field(
        default_factory=dict, description="Details of the current reservation being processed."
    )
