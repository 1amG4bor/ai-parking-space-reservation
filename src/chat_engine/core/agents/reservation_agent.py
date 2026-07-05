import json

from jinja2 import Template
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from chat_engine.core.agents.agent_models import ApsrSessionContext, ReservationAgentState, ReservationDetails
from chat_engine.core.config.config import ConfigManager
from chat_engine.core.config.logging import logger
from chat_engine.core.prompts import RESERVATION_SYSTEM_PROMPT
from chat_engine.core.utils.agent_tool import database_tool, reservation_tool

REFINED_PROMPT_TEMPLATE = Template("""
Fulfill the user's request based on the provided reservation details. If the request is unclear or incomplete, ask for clarification.

User Prompt: {{prompt}}

ReservationDetails:
{{reservation_details}}
""")


class ReservationAgent:
    """This agent is responsible for handling all reservation-related queries and actions.
    It interacts with the reservation tool as well as the administrator who confirm/refuse the reservations.
    """

    def __init__(self):
        self._cfg_manager = ConfigManager()
        self.agent = create_agent(
            model=self._cfg_manager.get_config("RESERVATION_AGENT_MODEL", "gpt-5-nano"),
            system_prompt=RESERVATION_SYSTEM_PROMPT,
            tools=[database_tool, reservation_tool],
            checkpointer=InMemorySaver(),
            context_schema=ApsrSessionContext,
            state_schema=ReservationAgentState,
        )

    def invoke(
        self,
        prompt: str,
        session_context: ApsrSessionContext,
        reservation_details: ReservationDetails,
    ) -> dict:
        """Invoke the reservation agent to submit a reservation request or ask about reservations.

        Returns a dict with:
            - "response" (str): The content of the agent's response.
            - "error_message" (str, optional): The error message if an error occurred.
        """
        logger.info(f"Request received by ReservationAgent with prompt: '{prompt}'.")
        reservation_details.user_name = session_context.username
        reservation_details.vehicle_id = session_context.vehicle_id

        refined_prompt = REFINED_PROMPT_TEMPLATE.render(
            prompt=prompt, reservation_details=json.dumps(reservation_details.model_dump(mode="json"))
        )
        try:
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": refined_prompt}]},
                context=session_context,
                config={"configurable": {"thread_id": f"RA-{session_context.thread_id}"}},
            )
        except Exception as e:
            logger.exception(f"Error invoking ReservationAgent: {e}")
            return {
                "response": "",
                "error_message": f"There was an error processing reservation request. Error: {e}. Please try again.",
            }

        return {
            "response": result,
            "error_message": None,
        }
