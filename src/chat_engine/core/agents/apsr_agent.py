from datetime import datetime

from langchain.agents import AgentState, create_agent
from langchain_core.prompts import SystemMessagePromptTemplate
from langgraph.checkpoint.memory import InMemorySaver

from chat_engine.core.agents.agent_models import ApsrSessionContext, APSRState
from chat_engine.core.agents.middleware import credit_card_guard, email_guard
from chat_engine.core.config.config import ConfigManager
from chat_engine.core.config.logging import logger
from chat_engine.core.prompts import APSR_SYSTEM_PROMPT
from chat_engine.core.utils.agent_tool import database_query_tool, retriever_tool, user_info_tool, websearch_tool


class APSRAgent:
    """This is the coordinator agent for the APSR system.
    It manages the interaction between the user and various tools, ensuring that queries are processed efficiently
    and responses are accurate and relevant.
    """

    def __init__(self):
        self._cfg_manager = ConfigManager()
        sys_prompt = SystemMessagePromptTemplate.from_template(APSR_SYSTEM_PROMPT, template_format="mustache")
        rendered_system_prompt = sys_prompt.format(current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.agent = create_agent(
            model=self._cfg_manager.get_config("COORDINATOR_AGENT_MODEL", "gpt-5-nano"),
            system_prompt=rendered_system_prompt,
            tools=[user_info_tool, retriever_tool, websearch_tool, database_query_tool],
            middleware=[email_guard, credit_card_guard],
            context_schema=ApsrSessionContext,
            checkpointer=InMemorySaver(),
            state_schema=APSRState,
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
