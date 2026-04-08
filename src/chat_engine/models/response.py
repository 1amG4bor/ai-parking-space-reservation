from enum import Enum

from pydantic import BaseModel, Field


class ResponseStatus(Enum):
    """Enum representing the status of the AI response, which indicates the next step that the UI should take."""

    ANALYZING = "Analyzing the request..."
    REQUEST = "Please provide additional information."
    SEARCHING = "Finding the best parking options..."
    CONFIRMATION = "Could you please confirm your reservation details?"
    STOP = "Conversation finished."

HUMAN_IN_THE_LOOP_STATUSES = {ResponseStatus.REQUEST, ResponseStatus.CONFIRMATION}

class ChatResponse(BaseModel):
    """Model representing the AI response"""

    content: str = Field(default="", description="The content of the AI response")
    status: ResponseStatus = Field(
        default=None,
        description="The status of the response, the next step that the UI will take or STOP if the conversation is finished",
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata related to the response")
