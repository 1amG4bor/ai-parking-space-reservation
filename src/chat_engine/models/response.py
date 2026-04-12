from enum import Enum

from pydantic import BaseModel, Field


class ResponseStatus(Enum):
    """Enum representing the status of the AI response, which indicates the next step that the UI should take."""

    ANALYZING = "Analyzing the request..."
    BLOCKED = "Your query was blocked by guardrails."
    SEARCHING = "Finding the best parking options..."
    REQUEST = "Please provide additional information."
    CONFIRMATION = "Could you please confirm your reservation details?"
    GENERATING = "Generating the response..."
    STREAMING = "Streaming the response..."
    STOP = "Conversation finished."


HUMAN_IN_THE_LOOP_STATUSES = {ResponseStatus.REQUEST, ResponseStatus.CONFIRMATION}


class ChatResponse(BaseModel):
    """Model representing the AI response"""

    content: str = Field(default="", description="The content of the AI response")
    status: ResponseStatus = Field(
        default=None,
        description="Describe the next step that the AI will take to fulfill the user's request.",
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata related to the response")
