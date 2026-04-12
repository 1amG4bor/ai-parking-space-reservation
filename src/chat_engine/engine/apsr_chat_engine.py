import re
from types import GeneratorType

from chat_engine.core.agents.agent import ReservationAgent
from chat_engine.core.agents.guardrail import ModerationGuardrail
from chat_engine.core.config.logging import logger
from chat_engine.core.utils.patterns import Singleton
from chat_engine.models.response import ChatResponse, ResponseStatus


class ChatEngine(metaclass=Singleton):
    def __init__(self):
        self.agent = ReservationAgent()
        self._guardrail = ModerationGuardrail()

    def stream_chat(self, prompt: str, history: list[dict], session_context: dict):
        # Placeholder for streaming AI response generation logic
        logger.info(f"Received prompt: '{prompt}' with history of {len(history)-1} message(s).")
        yield ChatResponse(status=ResponseStatus.ANALYZING)

        # Run guardrail checks on the prompt before processing
        guardrail_response = self._guardrail.validate(prompt)
        if guardrail_response.get("blocked"):
            template = "Sorry, we cannot process your request because: '{}'.\n**Suggestion:**\n{}"
            suggestions = "\n".join(guardrail_response.get("suggestions", []))
            error_message = template.format(guardrail_response.get("reason"), suggestions)

            yield ChatResponse(content=error_message, status=ResponseStatus.BLOCKED)
            return

        yield ChatResponse(status=ResponseStatus.SEARCHING)

        stream_response = self.agent.invoke(prompt=prompt, history=history, session_context=session_context)

        logger.info("Response is ready to be streamed.")
        if isinstance(stream_response, str):
            # Mimic streaming processing by yielding one chunk at a time.
            splitted_response = re.split(r"(?=[\s,.!?])", stream_response)
            for chunk in splitted_response:
                yield ChatResponse(content=chunk, status=ResponseStatus.STREAMING)
        elif isinstance(stream_response, list):
            for item in stream_response:
                yield ChatResponse(content=str(item), status=ResponseStatus.GENERATING)
        elif isinstance(stream_response, GeneratorType):
            yield ChatResponse(content=stream_response, status=ResponseStatus.STREAMING)
        else:
            yield ChatResponse(content=stream_response, status=ResponseStatus.GENERATING)

        # Indicate completion of the response stream
        logger.info("Request processing completed.")
        yield ChatResponse(status=ResponseStatus.STOP)
