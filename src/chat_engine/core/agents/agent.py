from langchain.agents import AgentState, create_agent
from langgraph.checkpoint.memory import InMemorySaver

from chat_engine.core.agents.agent_models import AgentContext
from chat_engine.core.config.config import ConfigManager
from chat_engine.core.prompts import SYSTEM_PROMPT
from chat_engine.core.utils.agent_tool import retriever_tool, websearch_tool, reservation_tool
from chat_engine.core.agents.middleware import email_guard, credit_card_guard

from chat_engine.core.config.logging import logger


class ReservationAgent:
    def __init__(self):
        self._cfg_manager = ConfigManager()
        self.agent = create_agent(
            model=self._cfg_manager.get_config("RESERVATION_AGENT_MODEL", "gpt-5-nano"),
            system_prompt=SYSTEM_PROMPT,
            tools=[retriever_tool, websearch_tool, reservation_tool],
            middleware=[email_guard, credit_card_guard],
            context_schema=AgentContext,
            checkpointer=InMemorySaver(),
        )

    def guardrail(self, prompt: str) -> bool:
        """A guardrail function to check the user's query before processing it.
        The goal is to prevent exposure of sensitive data and/or avoid any inappropriate or malicious act."""
        self.logger.info(f"Guardrail check for the user's query: {prompt}")
        result = self.agent.invoke_tool("guardrail_tool", {"query": prompt})

    def invoke(self, prompt: str, history: list[dict], session_context: dict = []) -> str:
        """Invoke the reservation agent to process the user's query and provide a response."""
        # Convert chat history to AgentState format
        history = [AgentState(role=msg["role"], content=msg["content"]) for msg in history]
        history_size = len(history)

        agent_context = AgentContext(
            authenticated=session_context.get("authenticated", False),
            username=session_context.get("username"),
            selected_vehicle=session_context.get("vehicle_id"),
            selected_location=session_context.get("location"),
            preferences=session_context.get("preferences", []),
        )

        result = self.agent.invoke(
            {"messages": history},
            context=agent_context,
            config={"configurable": {"thread_id": session_context.get("thread_id")}},
        )

        # Typical create_agent output contains updated messages
        if isinstance(result, dict) and "messages" in result and result["messages"]:
            messages = result["messages"]
            for i, msg in enumerate(messages[history_size:], start=history_size):  # Process only new messages
                logger.debug(f"{i}. message: [{msg.type}] {msg.content}")  # Debugging internal messages
            last = result["messages"][-1]
            return getattr(last, "content", str(last))

        return str(result)
