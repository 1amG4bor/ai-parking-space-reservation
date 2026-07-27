from datetime import datetime
from typing import TypedDict

from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from chat_engine.core.agents.agent_models import APSRState, UseCase, UserIntent
from chat_engine.core.agents.guardrail import ModerationGuardrail
from chat_engine.core.config.logging import logger
from chat_engine.core.prompts import (
    BLOCKED_REQUEST_PROMPT,
    RESERVATION_INFO_AGENT_SYSTEM_PROMPT,
    RESERVATION_MANAGEMENT_AGENT_SYSTEM_PROMPT,
    ROUTER_PROMPT,
    SEARCH_AGENT_SYSTEM_PROMPT,
    SYNTHESIZER_PROMPT,
    USER_INPUT_PROMPT,
    USER_INTENT_PROMPT,
)
from chat_engine.core.utils.agent_tool import (
    database_query_tool,
    reservation_detail_creation_tool,
    reservation_tool,
    retriever_tool,
    user_info_tool,
    websearch_tool,
)
from chat_engine.core.utils.mcp_tool_helper import save_reservation_snapshot_via_mcp

GENERAL_GUARDRAIL_ERROR = "Your request was blocked due to content moderation issue."


class RouterDecision(BaseModel):
    """Structured router output to keep path selection deterministic for graph edges."""

    next_node: str = Field(description="Next node to execute.")
    rationale: str = Field(default="", description="Short reason for the selected next step.")


def _msg_content(message) -> str:
    if isinstance(message, dict):
        return str(message.get("content", ""))
    return str(getattr(message, "content", ""))


def _msg_kind(message) -> str:
    if isinstance(message, dict):
        return str(message.get("role", ""))
    return str(getattr(message, "type", ""))


# ==================== Validator nodes ====================
def guardrail_node(state: APSRState) -> dict:
    """Guardrail node that checks the user's input against moderation rules and updates the state accordingly."""
    latest_prompt = state.messages[-1].content

    guardrail = ModerationGuardrail()
    guardrail_response = guardrail.validate(latest_prompt)
    if guardrail_response.get("blocked"):
        guardrail_issue = guardrail_response.get("reason", GENERAL_GUARDRAIL_ERROR)
        if guardrail_response.get("suggestions"):
            suggestions = "\n".join(guardrail_response.get("suggestions", []))
            guardrail_issue += "\n\n**Suggestions:**\n" + suggestions
        return {"use_case": UseCase(user_intent=UserIntent.BLOCKED, issue_justification=guardrail_issue)}
    use_case = None
    if state.use_case and state.use_case.user_intent is not None:
        use_case = UseCase(user_intent=state.use_case.user_intent)

    # When the guardrail check passes
    response_dict = {"messages": [AIMessage(content="Prompt passed guardrail checks.")]}
    if use_case:
        response_dict["use_case"] = use_case
    return response_dict


def user_intent_classifier_node(state: APSRState) -> dict:
    """A node that classifies the user's intent based on their input and updates the state accordingly."""
    # if state.use_case and state.use_case.user_intent == UserIntent.BLOCKED:
    #     return {}  # Fast forward, blocked requests will be handled in the next step

    llm = init_chat_model(model="gpt-4o-mini", model_provider="openai", temperature=0)
    intent_classifier = llm.with_structured_output(UseCase)
    intent_prompt_template = ChatPromptTemplate.from_template(USER_INTENT_PROMPT, template_format="mustache")
    parsed_conversation = [f"{_msg_kind(msg)}: {_msg_content(msg)}" for msg in state.messages]
    human_like_messages = [msg for msg in state.messages if _msg_kind(msg) in ("human", "user")]
    usr_prompt = _msg_content(human_like_messages[-1] if human_like_messages else state.messages[-1])
    intent = intent_classifier.invoke(
        input=intent_prompt_template.format(user_query=usr_prompt, conversation_history="\n".join(parsed_conversation))
    )
    logger.info(f"User intent classified as: {intent.user_intent}.")
    return {
        "use_case": intent,
        "messages": [AIMessage(content=f"User intent classified as: {intent.user_intent.value}")],
    }


def router_node(state: APSRState) -> dict:
    """Decide the next processing step based on available state information."""
    logger.info(f"Router node: evaluating state. intent={state.use_case.user_intent if state.use_case else None}")

    allowed_next_nodes = {
        "get_reservation_info",
        "search",
        "user_input",
        "reservation_detail_creation_tool",
        "submit_reservation",
        "synthesizer",
        "block",
    }

    router_llm = init_chat_model(model="gpt-4o-mini", model_provider="openai", temperature=0)
    router_chain = router_llm.with_structured_output(RouterDecision)
    intent_prompt_template = ChatPromptTemplate.from_template(ROUTER_PROMPT, template_format="mustache")

    parsed_conversation = [f"{_msg_kind(msg)}: {_msg_content(msg)}" for msg in state.messages]
    last_user_message = next(
        (_msg_content(msg) for msg in reversed(state.messages) if _msg_kind(msg) in ("human", "user")),
        _msg_content(state.messages[-1]) if state.messages else "",
    )

    try:
        prompt = intent_prompt_template.format(
            user_query=last_user_message,
            user_intent=state.use_case.user_intent.value if state.use_case and state.use_case.user_intent else "",
            conversation_history="\n".join(parsed_conversation),
            retrieved_parking_info=state.retrieved_parking_info,
            reservation_details=state.reservation_details,
            pending_reservations=state.pending_reservations,
            booked_reservations=state.booked_reservations,
            completed_reservations=state.completed_reservations,
        )
    except Exception as e:
        logger.exception(f"Router prompt formatting failed: {e}")
        return {"next_step": "block", "messages": [AIMessage(content="Sorry, an internal error occurred.")]}

    decision = None
    attempts, max_attempts = 0, 3
    while not decision and attempts < max_attempts:
        try:
            decision = router_chain.invoke(prompt)
        except Exception as error:
            logger.exception(f"Router decision attempt {attempts+1} failed: {error}")
            attempts += 1
            continue

        if not decision or decision.next_node not in allowed_next_nodes:
            decision = None
            attempts += 1

    if not decision:
        logger.error("Router failed to produce a valid next node after 3 attempts.")
        return {
            "next_step": "block",
            "messages": [AIMessage(content="Sorry, some internal error occurred. Please try again.")],
        }

    logger.info(f"Router selected next node: {decision.next_node}. Reason: {decision.rationale}")
    return {"next_step": decision.next_node, "messages": [AIMessage(content=f"Proceeding to: {decision.rationale}")]}


def router_semaphore(state: APSRState) -> str:
    """Return the next_step for conditional routing; fall back to block if not set."""
    destination = state.next_step
    logger.info(f"router_semaphore: next_step={destination}")
    if not destination:
        logger.error("router_semaphore: next_step is None or empty, routing to block.")
        return "block"
    return destination


def user_input_node(state: APSRState) -> dict:
    """HITL node — pause and ask user for clarification, confirmation, or missing info."""
    try:
        usr_prompt = [msg.content for msg in state.messages if msg.type in ("human", "user")]
        parsed_conversation = [f"{_msg_kind(msg)}: {_msg_content(msg)}" for msg in state.messages]
        info_required = state.messages[-1].content
        user_intent = state.use_case.user_intent.value
    except Exception as e:
        logger.exception(f"Information extraction failed in user_input_node: {e}")
        raise e

    try:
        llm = init_chat_model(model="gpt-4o-mini", model_provider="openai", temperature=0.2)
        chain = ChatPromptTemplate.from_template(USER_INPUT_PROMPT, template_format="mustache") | llm
        llm_inputs = (
            f"User intent: {user_intent}\nUser query: {usr_prompt[0] if usr_prompt else ''}\n"
            f"Conversation history:\n{'\n'.join(parsed_conversation)}\nClarification request: {info_required}"
        )
        llm_response = chain.invoke({"llm_inputs": llm_inputs})
        msg_to_user = llm_response.content
        user_input = interrupt({"type": "user_input", "message": msg_to_user})
    except Exception as e:
        logger.exception(f"Failed to get user input: {e}")
        raise e

    try:
        response_summary_format = TypedDict(
            "ResponseSummary", {"user_intent": str, "user_message": str, "is_confirmed": bool}
        )
        summary_chain = ChatPromptTemplate.from_template(
            USER_INPUT_PROMPT, template_format="mustache"
        ) | llm.with_structured_output(response_summary_format)

        llm_inputs = f"User intent: {user_intent}\nUser's response: {user_input}"
        response_summary = summary_chain.invoke({"llm_inputs": llm_inputs})
        return {
            "messages": [HumanMessage(content=response_summary.get("user_message", user_input))],
            "reservation_confirmed": response_summary.get("is_confirmed", False),
        }
    except Exception as e:
        logger.exception(f"Failed to summarize the user's response: {e}")
        raise e


# ==================== Module-level sub-agents ====================
_search_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    tools=[user_info_tool, retriever_tool, websearch_tool],
    state_schema=APSRState,
    prompt=SEARCH_AGENT_SYSTEM_PROMPT,
)

_reservation_info_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    tools=[database_query_tool, reservation_detail_creation_tool],
    state_schema=APSRState,
    prompt=RESERVATION_INFO_AGENT_SYSTEM_PROMPT.replace("{{current_date}}", str(datetime.now().date())),
)

_reservation_management_agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    tools=[reservation_tool, database_query_tool],
    state_schema=APSRState,
    prompt=RESERVATION_MANAGEMENT_AGENT_SYSTEM_PROMPT,
)


def _get_field(obj, key, default=None):
    """Get a field from either a dict or a Pydantic model."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _invoke_sub_agent(agent, state: APSRState, extra_fields: dict = None) -> dict:
    """Invoke a sub-agent with relevant state fields and return only the fields that may have changed."""
    input_state = {
        "messages": state.messages,
        "remaining_steps": getattr(state, "remaining_steps", 25),
        "session_context": state.session_context,
        "vehicles": state.vehicles,
        "locations": state.locations,
        "preferences": state.preferences,
        "retrieved_parking_info": state.retrieved_parking_info,
        "pending_reservations": state.pending_reservations,
        "booked_reservations": state.booked_reservations,
        "completed_reservations": state.completed_reservations,
        "reservation_details": state.reservation_details,
        "use_case": state.use_case,
    }
    if extra_fields:
        input_state.update(extra_fields)

    result = agent.invoke(input_state)

    return {
        "messages": _get_field(result, "messages", state.messages),
        "remaining_steps": _get_field(result, "remaining_steps", 25),
        "vehicles": _get_field(result, "vehicles", state.vehicles),
        "locations": _get_field(result, "locations", state.locations),
        "preferences": _get_field(result, "preferences", state.preferences),
        "retrieved_parking_info": _get_field(result, "retrieved_parking_info", state.retrieved_parking_info),
        "pending_reservations": _get_field(result, "pending_reservations", state.pending_reservations),
        "booked_reservations": _get_field(result, "booked_reservations", state.booked_reservations),
        "completed_reservations": _get_field(result, "completed_reservations", state.completed_reservations),
        "reservation_details": _get_field(result, "reservation_details", state.reservation_details),
    }


# ==================== Request processing nodes ====================
def search_node(state: APSRState) -> dict:
    """A node that performs search operations — user info, parking retrieval, web search."""
    logger.info("Search node: invoking search agent (user_info + retriever + websearch).")
    return _invoke_sub_agent(_search_agent, state)


def reservation_info_node(state: APSRState) -> dict:
    """A node that retrieves reservation information from the database."""
    logger.info("Reservation info node: invoking reservation info agent (database queries).")
    return _invoke_sub_agent(_reservation_info_agent, state)


def reservation_management_node(state: APSRState) -> dict:
    """A node that manages the reservation process — booking, checking availability, persisting."""
    logger.info("Reservation management node: invoking reservation management agent.")
    return _invoke_sub_agent(_reservation_management_agent, state)


def reservation_persistence_node(state: APSRState) -> dict:
    """A node that persists the reservation snapshot via MCP filesystem."""
    logger.info("Reservation persistence node: saving snapshot via MCP.")
    details = state.reservation_details
    if not details:
        return {"messages": [AIMessage(content="No reservation details found to persist.")]}

    try:
        save_reservation_snapshot_via_mcp(dict(details))
        return {
            "messages": [AIMessage(content="Reservation snapshot persisted successfully.")],
            "reservation_details": None,  # Clear reservation details after persisting
            "reservation_confirmed": False,  # Reset confirmation status after persisting
        }
    except Exception as err:
        logger.exception(f"Failed to persist reservation snapshot: {err}")
        return {"messages": [AIMessage(content=f"Failed to persist reservation snapshot: {err}")]}


def block_node(state: APSRState) -> dict:
    """Block node that stops the conversation if the user's input is blocked by the guardrail."""
    use_case_label = state.use_case.user_intent.value if state.use_case and state.use_case.user_intent else ""
    reason = state.use_case.issue_justification
    parsed_conversation = "\n".join(f"{_msg_kind(m)}: {_msg_content(m)}" for m in state.messages)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = ChatPromptTemplate.from_template(BLOCKED_REQUEST_PROMPT, template_format="mustache") | llm
    response = chain.invoke(
        {
            "user_intent": use_case_label,
            "issue_justification": reason,
            "conversation_history": parsed_conversation,
        }
    )

    return {"messages": [AIMessage(content=response.content)]}


def synthesizer_node(state: APSRState) -> dict:
    """A node that synthesizes the final response to the user based on the collected information."""
    logger.info("Synthesizer node: formatting final response.")

    parsed_conversation = "\n".join(f"{_msg_kind(m)}: {_msg_content(m)}" for m in state.messages)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    chain = ChatPromptTemplate.from_template(SYNTHESIZER_PROMPT, template_format="mustache") | llm

    use_case_label = state.use_case.user_intent.value if state.use_case and state.use_case.user_intent else "UNKNOWN"

    response = chain.invoke(
        {
            "conversation_history": parsed_conversation,
            "use_case": use_case_label,
            "retrieved_parking_info": str(state.retrieved_parking_info),
            "reservation_details": str(state.reservation_details),
        }
    )

    return {"messages": [AIMessage(content=response.content)]}
