from datetime import datetime
from enum import Enum
from typing import Annotated, Any, List, Optional

from langchain.messages import AnyMessage
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

from chat_engine.core.config.logging import logger


def merge_dicts(left: dict | None, right: dict | None) -> dict:
    """Merges two dictionaries, updating existing keys and adding new ones.
    Handle initial empty states safely
    """
    if right is not None and not isinstance(right, dict):
        logger.exception(f"merge_dicts received non-dict right operand: {type(right).__name__}")
        raise TypeError(f"merge_dicts expected dict, got {type(right).__name__}")
    current_dict = dict(left) if left else {}
    update_dict = dict(right) if right else {}
    current_dict.update(update_dict)
    return current_dict


class UserIntent(Enum):
    """Enumeration for mapping the user's intent to specific actions that the system can handle."""

    PARKING_INFO = "PARKING_INFO"
    # Providing parking information, such as available parking spaces, locations, or costs.
    RESERVATION = "RESERVATION"
    # Make a reservation for a parking space.
    RESERVATION_HISTORY = "RESERVATION_HISTORY"
    # Check previous/existing reservations.
    RESERVATION_CHANGE = "RESERVATION_CHANGE"
    # Apply changes to an existing reservation, such as modifying or canceling it.
    NEED_FOR_CLARIFICATION = "NEED_FOR_CLARIFICATION"
    # Unclear or ambiguous request, require clarification to get more information.
    UNSUPPORTED = "UNSUPPORTED"
    # Requests that are not supported by the system or do not match any of the above use cases.
    BLOCKED = "BLOCKED"
    # Requests that are blocked due to content moderation checks, such as inappropriate or malicious content.


class UseCase(BaseModel):
    """Schema for the user's intent, including the action they want to perform and any relevant details."""

    user_intent: UserIntent = Field(
        None, description="The intent of the user's query, indicating the action that needs to be performed."
    )
    missing_info: Optional[List[str]] = Field(
        default=[], description="List of information required to fulfill the user's request, if applicable."
    )
    issue_justification: Optional[str] = Field(
        default="",
        description="The justification to the users, "
        "why a request was rejected or what kind of clarification their request requires.",
    )


# ===== Agentic Graph State Schemas =====
class ApsrSessionContext(BaseModel):
    """Context schema containing information about the user's session and preferences."""

    thread_id: str = Field(default=None, description="Unique identifier for the chat session/thread.")
    username: str = Field(default=None, description="The username of the authenticated user.")
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
            thread_id=data.get("thread_id", None),
            username=data.get("username", None),
            vehicle_id=data.get("vehicle_id", None),
            selected_vehicle=data.get("selected_vehicle", ""),
            selected_location=data.get("selected_location", ""),
            selected_preferences=data.get("selected_preferences", []),
        )


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


class APSRState(BaseModel):
    """Overall state schema for the APSR system — flat fields matching tool Command updates."""

    session_context: ApsrSessionContext = Field(
        default_factory=ApsrSessionContext,
        description="The session context containing session information.",
    )

    # User data — written by user_info_tool
    vehicles: List[dict] = Field(default_factory=list, description="List of vehicles associated with the user.")
    locations: List[dict] = Field(default_factory=list, description="List of locations associated with the user.")
    preferences: List[dict] = Field(
        default_factory=list,
        description="List of user preferences that may influence reservation suggestions.",
    )

    # Parking data — written by retriever_tool
    retrieved_parking_info: List[dict] = Field(
        default_factory=list,
        description="List of retrieved parking information relevant to the user's query.",
    )

    # Reservation data — written by reservation_tool
    pending_reservations: Annotated[dict, merge_dicts] = Field(
        default_factory=dict,
        description="Reservations booked but not yet confirmed by the admin.",
    )
    booked_reservations: Annotated[dict, merge_dicts] = Field(
        default_factory=dict,
        description="Reservations confirmed by the admin.",
    )
    completed_reservations: Annotated[dict, merge_dicts] = Field(
        default_factory=dict,
        description="Completed/cancelled reservations.",
    )
    reservation_details: Optional[ReservationDetails] = Field(
        default=None,
        description="Details of the current reservation being processed.",
    )
    reservation_confirmed: Optional[bool] = Field(
        default=False,
        description="Indicates whether the current reservation has been confirmed by the user.",
    )

    # System
    use_case: UseCase = Field(
        default_factory=UseCase,
        description="General information about the user's intent and the action to be performed.",
    )
    next_step: str = Field(
        default=None,
        description="The next step in the processing pipeline, determined by the router node.",
    )
    remaining_steps: int = Field(
        default=25,
        description="Remaining steps for the agent (used by create_agent for recursion budget).",
    )
    messages: Annotated[list[AnyMessage | dict[str, Any]], add_messages] = Field(
        default_factory=list,
        description="Agent conversation state (user, assistant, and tool messages).",
    )

    def __setattr__(self, name: str, value):
        try:
            super().__setattr__(name, value)
        except Exception:
            logger.exception(f"APSRState field '{name}' rejected {type(value).__name__}")
            raise

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __setitem__(self, key: str, value):
        setattr(self, key, value)
