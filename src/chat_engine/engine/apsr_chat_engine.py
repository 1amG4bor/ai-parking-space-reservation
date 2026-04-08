# from asyncio import sleep
import logging
from time import sleep

from chat_engine.core.tools.patterns import Singleton
from chat_engine.models.response import ChatResponse, ResponseStatus

logger = logging.getLogger(__name__)


class ChatEngine(metaclass=Singleton):
    def __init__(self):
        pass

    def chat(self, prompt: str, history: list[dict]) -> str:
        # Placeholder for AI response generation logic
        logger.info(f"Received prompt: {prompt} with history of {len(history)} messages.")
        return "Could you please provide more details?"

    def stream_chat(self, prompt: str, history: list[dict]):
        # Placeholder for streaming AI response generation logic
        logger.info(f"Received prompt: {prompt} with history of {len(history)} messages.")
        yield ChatResponse(status=ResponseStatus.ANALYZING.value)

        # Simulate working
        sleep(1)
        yield ChatResponse(content="Let me check that for you...")
        sleep(3)
        yield ChatResponse(content="Could you please provide more details?", status=ResponseStatus.REQUEST.value)
