from datetime import datetime
from typing import Annotated, Any, List

from langchain.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


def merge_dicts(left: dict | None, right: dict | None) -> dict:
    """Merges two dictionaries, updating existing keys and adding new ones.
    Handle initial empty states safely
    """
    current_dict = dict(left) if left else {}
    update_dict = dict(right) if right else {}
    current_dict.update(update_dict)
    return current_dict


class ReservationDetails(BaseModel):
    """Schema with the details needed for any reservation."""

    user_name: str = Field(..., description="The username of the user making the reservation.")
    vehicle_id: int = Field(..., description="The ID of the vehicle for which the reservation is being made.")
    parking_lot_id: str = Field(..., description="The ID of the parking lot where the reservation is being made.")
    parking_space_category: str = Field(..., description="The category of the parking space being reserved.")
    start_time: datetime = Field(..., description="The start time of the reservation in ISO format.")
    end_time: datetime = Field(..., description="The end time of the reservation in ISO format.")
    reservation_id: str = Field(default=None, description="The unique identifier for the reservation.")
    registration_time: datetime = Field(default=None, description="The time when the reservation was registered.")


class ApsrSessionContext(BaseModel):
    """Context schema for the ReservationAgent, contains information about the user's session and preferences."""

    authenticated: bool = Field(default=False, description="Indicates whether the user is authenticated.")
    username: str = Field(default=None, description="The username of the authenticated user.")
    thread_id: str = Field(default=None, description="Unique identifier for the chat session/thread.")
    vehicle_id: int | None = Field(
        default=None, description="The ID of the vehicle selected by the user for reservation."
    )
    selected_vehicle: str = Field(
        default="", description="Short description of the user's selected vehicle for the reservation."
    )
    selected_location: str = Field(
        default="", description="The user's selected departure location as the starting point of their trip."
    )
    selected_preferences: List[str] = Field(
        default_factory=list,
        description="List of preferences chosen by the user for the current search and reservation process.",
    )

    @classmethod
    def from_dict(cls, data: dict):
        """Create ApsrSessionContext instance from a dictionary."""
        return cls(
            authenticated=data.get("authenticated", False),
            username=data.get("username", None),
            thread_id=data.get("thread_id", None),
            vehicle_id=data.get("vehicle_id", None),
            selected_vehicle=data.get("selected_vehicle", ""),
            selected_location=data.get("selected_location", ""),
            selected_preferences=data.get("selected_preferences", []),
        )


class CoordinatorAgentState(BaseModel):
    """State schema for the CoordinatorAgent, contains all the important information during the agent's operation."""

    # Reservation specific user data
    locations: List[dict] = Field(default_factory=list, description="List of locations associated with the user.")
    vehicles: List[dict] = Field(default_factory=list, description="List of vehicles associated with the user.")
    preferences: List[dict] = Field(
        default_factory=list, description="List of user preferences that may influence reservation suggestions."
    )
    # Session-specific data
    retrieved_parking_info: List[dict] = Field(
        default_factory=list, description="List of retrieved parking information relevant to the user's query."
    )
    current_reservation_details: dict = Field(
        default_factory=dict, description="Details of the current reservation being processed."
    )
    messages: Annotated[list[AnyMessage | dict[str, Any]], add_messages] = Field(
        default_factory=list,
        description="Agent conversation state (user, assistant, and tool messages).",
    )


class ReservationAgentState(BaseModel):
    """State schema for the ReservationAgent, contains all the important information during the agent's operation."""

    completed_reservations: Annotated[dict, merge_dicts] = Field(
        default_factory=dict, description="A collection of reservations that are already completed."
    )

    active_reservations: Annotated[dict, merge_dicts] = Field(
        default_factory=dict, description="A collection of reservations that are booked and confirmed by the admin."
    )

    inactive_reservations: Annotated[dict, merge_dicts] = Field(
        default_factory=dict, description="A collection of reservations that are booked but not confirmed by the admin."
    )
    messages: Annotated[list[AnyMessage | dict[str, Any]], add_messages] = Field(
        default_factory=list,
        description="Conversation state between the main APSRAgent and the ReservationAgent.",
    )
