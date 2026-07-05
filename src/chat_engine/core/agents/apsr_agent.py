from datetime import datetime
from typing import Annotated

from langchain.agents import AgentState, create_agent
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.prompts import SystemMessagePromptTemplate
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from chat_engine.core.agents.agent_models import ApsrSessionContext, CoordinatorAgentState, ReservationDetails
from chat_engine.core.agents.middleware import (
    credit_card_guard,
    email_guard,
)
from chat_engine.core.agents.reservation_agent import ReservationAgent
from chat_engine.core.config.config import ConfigManager
from chat_engine.core.config.logging import logger
from chat_engine.core.prompts import APSR_SYSTEM_PROMPT
from chat_engine.core.utils.agent_tool import database_tool, retriever_tool, user_info_tool, websearch_tool


def _build_reservation_agent_tool(reservation_agent: ReservationAgent):
    """Create an adapter tool with a stable schema for delegating to ReservationAgent."""

    def reservation_agent_tool(
        runtime: ToolRuntime[ApsrSessionContext, CoordinatorAgentState],
        prompt: str,
        reservation_details: ReservationDetails,
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        result = reservation_agent.invoke(
            prompt=prompt,
            session_context=runtime.context,
            reservation_details=reservation_details,
        )
        content = result.get("response", "")
        is_error = "Error:" in content
        return Command(
            update={
                "current_reservation_details": reservation_details.model_dump(mode="json"),
                "messages": [
                    ToolMessage(content=content, status="error" if is_error else "success", tool_call_id=tool_call_id)
                ],
            },
        )

    return tool(name_or_callable=reservation_agent_tool, description=RESERVATION_AGENT_TOOL_DESC)


RESERVATION_AGENT_TOOL_DESC = """
A tool to interact with the reservation agent for handling reservation-related queries.

Usecases:
- Submitting a new reservation request on behalf of the user.
- Asking about existing reservations for the user.
- Modifying or canceling existing reservations for the user.
- Providing reservation details to the user.
- Asking about reservation status or history for the user.

Input:
- `prompt` (str): The reservation-specific instruction to execute.
- `reservation_details` (ReservationDetails): Details of the reservation to be processed.
- `session_context` (ApsrSessionContext, automatically injected): The session context containing user information and preferences.

Output:
- A dict with:
    - `content` (str): The response message from the reservation agent after processing the request
    - `messages` (list[AgentState]): The new messages generated during the reservation agent's processing, which will be added to the coordinator's state for context in future interactions.


Context:
- User/session context is injected automatically by the runtime and does not need to be provided in tool args.
- Sub-agent chat history is managed automatically via the coordinator's state.

Example Queries (messages content):
- "Book a parking space for the user 'jack_sparrow' with the atteched reservation details."
- "What reservations does the user 'mia' have?"
- "What is the status of the reservation for the user 'oliver_twist' which details are attached?"
- "Cancel the reservation for the user 'timmy21' with the details in the attachment."
- "Modify the reservation for the user 'jimmy_page' with the details in the attachment."
- "Provide the reservation history for the last month for the user 'jane_doe'."
"""


class APSRAgent:
    """This is the coordinator agent for the APSR system.
    It manages the interaction between the user and various tools, ensuring that queries are processed efficiently
    and responses are accurate and relevant.
    """

    def __init__(self, reservation_agent: ReservationAgent):
        self.reservation_agent = reservation_agent
        reservation_agent_tool = _build_reservation_agent_tool(self.reservation_agent)

        self._cfg_manager = ConfigManager()
        sys_prompt = SystemMessagePromptTemplate.from_template(APSR_SYSTEM_PROMPT, template_format="mustache")
        rendered_system_prompt = sys_prompt.format(current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.agent = create_agent(
            model=self._cfg_manager.get_config("COORDINATOR_AGENT_MODEL", "gpt-5-nano"),
            system_prompt=rendered_system_prompt,
            tools=[user_info_tool, retriever_tool, websearch_tool, database_tool, reservation_agent_tool],
            middleware=[email_guard, credit_card_guard],
            context_schema=ApsrSessionContext,
            checkpointer=InMemorySaver(),
            state_schema=CoordinatorAgentState,
        )

    @staticmethod
    def _build_messages(prompt: str, history: list[dict], thread_id: str | None) -> list[AgentState]:
        """Use checkpointed thread state as the source of truth when available."""
        combined_history = (
            [{"role": "user", "content": prompt}] if thread_id else history + [{"role": "user", "content": prompt}]
        )
        return [AgentState(role=msg["role"], content=msg["content"]) for msg in combined_history]

    def invoke(self, prompt: str, history: list[dict], session_context: dict | ApsrSessionContext) -> str:
        """Invoke the reservation agent to process the user's query and provide a response."""
        logger.info(f"Request received by APSRAgent with prompt: '{prompt}'.")
        try:
            if isinstance(session_context, dict):
                aspr_context = ApsrSessionContext.from_dict(session_context)
            else:
                aspr_context = session_context

            history = self._build_messages(prompt=prompt, history=history, thread_id=aspr_context.thread_id)
            history_size = len(history)
        except Exception as e:
            logger.error(f"Error preparing context for APSRAgent: {e}")
            return "Sorry, there was an error processing your request. Please try again."

        try:
            result = self.agent.invoke(
                {"messages": history},
                context=aspr_context,
                config={"configurable": {"thread_id": aspr_context.thread_id}},
            )
        except Exception as e:
            logger.exception(f"Error invoking APSRAgent: {e}")
            return "Sorry, there was an error processing your request. Please try again."

        try:
            if isinstance(result, dict) and "messages" in result and result["messages"]:
                messages = result["messages"]
                for i, msg in enumerate(messages[history_size:], start=history_size):  # Process only new messages
                    logger.debug(f"{i}. message: [{msg.type}] {msg.content}")  # Debugging internal messages
                last = result["messages"][-1]
                return getattr(last, "content", str(last))

            return str(result)
        except Exception as e:
            logger.error(f"Error processing APSRAgent result: {e}")
            return "Sorry, there was an error processing your request. Please try again."
