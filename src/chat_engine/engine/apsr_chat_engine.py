from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from chat_engine.core.agents.agent_models import ApsrSessionContext, APSRState
from chat_engine.core.config.logging import logger
from chat_engine.core.graph.workflow import build_state_graph
from chat_engine.core.utils.patterns import Singleton
from chat_engine.models.response import ChatResponse, ResponseStatus

_INTERRUPT_KEY = "__interrupt__"


class ChatEngine(metaclass=Singleton):
    def __init__(self):
        self._graph: CompiledStateGraph | None = None
        self._resume_threads: set[str] = set()

    def _get_graph(self) -> CompiledStateGraph:
        if self._graph is None:
            self._graph = build_state_graph()
        return self._graph

    # pylint: disable=too-many-branches
    def stream_chat(self, prompt: str, history: list[dict], session_context: ApsrSessionContext):
        logger.info(f"Received prompt: '{prompt}' with history of {len(history)-1} message(s).")

        thread_id = session_context.thread_id or "default"
        config = {"configurable": {"thread_id": thread_id}}
        graph = self._get_graph()

        if thread_id in self._resume_threads:
            # Continue the previously interrupted graph execution that was waiting for user input to continue.
            logger.info("Resuming thread %s with user input.", thread_id)
            self._resume_threads.discard(thread_id)
            yield ChatResponse(status=ResponseStatus.SEARCHING)
            try:
                result = graph.invoke(Command(resume=prompt), config)
            except Exception:
                logger.exception("Graph execution failed on resume")
                raise
        else:
            history.append({"role": "user", "content": prompt})
            yield ChatResponse(status=ResponseStatus.SEARCHING)
            try:
                result = graph.invoke(input={"messages": history, "session_context": session_context}, config=config)
            except Exception:
                logger.exception("Graph execution failed")
                raise

        logger.info("Response is ready to be streamed.")

        interrupts = result.get(_INTERRUPT_KEY) if isinstance(result, dict) else None
        if interrupts:
            interrupt_value = interrupts[0].value
            if isinstance(interrupt_value, dict):
                msg = interrupt_value.get("message", str(interrupt_value))
            else:
                msg = str(interrupt_value)
            self._resume_threads.add(thread_id)
            logger.info("Graph interrupted, waiting for user input on thread %s.", thread_id)
            yield ChatResponse(content=msg, status=ResponseStatus.AWAITING_INPUT)
            return

        if isinstance(result, dict):
            messages = result.get("messages", [])
        elif isinstance(result, APSRState):
            messages = result.messages
        else:
            messages = []

        if messages:
            last_msg = messages[-1]
            content = getattr(last_msg, "content", str(last_msg))
        else:
            content = str(result)

        if content:
            yield ChatResponse(content=content, status=ResponseStatus.STREAMING)

        logger.info("Request processing completed.")
        yield ChatResponse(status=ResponseStatus.STOP)
