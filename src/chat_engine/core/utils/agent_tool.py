# pylint: disable=line-too-long
import os
import random
from datetime import UTC, datetime
from typing import Annotated, Any

import sqlalchemy
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.types import Command
from tavily import TavilyClient

from chat_engine.core.agents.agent_models import ApsrSessionContext, ReservationDetails
from chat_engine.core.config.logging import logger
from chat_engine.core.rag.retriever import ParkingInfoRetriever
from chat_engine.core.utils.db_tool import DatabaseService
from chat_engine.core.utils.mcp_tool_helper import save_reservation_snapshot_via_mcp
from chat_engine.models.db_entities import ReservationEntity
from chat_engine.models.enums import ReservationStatus


def _session_field(runtime: ToolRuntime, field: str):
    """Extract a field from session_context via ToolRuntime state."""
    state = runtime.state
    if isinstance(state, dict):
        sc = state.get("session_context")
    else:
        sc = getattr(state, "session_context", None)
    if sc is None:
        return None
    if isinstance(sc, dict):
        return sc.get(field)
    return getattr(sc, field, None)


@tool
def user_info_tool(
    tool_call_id: Annotated[str, InjectedToolCallId],
    runtime: ToolRuntime[ApsrSessionContext, Any],
) -> Command:
    """
    A tool for retrieving user information, including vehicles, locations, and parking preferences, to support personalized parking recommendations.

    Use Cases:
    - Use this tool when you need to retrieve the user's vehicle information, locations, or parking preferences to personalize recommendations.
    - Use this tool if you need to confirm or update your context with the latest user data before making a reservation.
    - Use this tool when the user's preferences or details are not already available in your current context.

    Args:
        - tool_call_id (str): The unique identifier for the tool call.
        - runtime (ToolRuntime): The runtime context for accessing user and conversation information.

    Returns:
        - dict: A dictionary containing the user's locations, vehicles, preferences, and reservation history.
    Raises:
        - HTTPException: If the user is not authenticated or if there is an error fetching user data from the database.
    """
    logger.info("Getting user preferences.")
    username = _session_field(runtime, "username")
    if not username:
        return ToolMessage(content="User is not authenticated.", status="error", tool_call_id=tool_call_id)

    # Fetch user preferences from the database.
    try:
        db_service = DatabaseService()
        logger.info(f"Fetching user data for: '{username}'.")
        user_data = db_service.get_user_by_username(username)
        if not user_data:
            return ToolMessage(content=f"User '{username}' does not exist.", status="error", tool_call_id=tool_call_id)

    except Exception as err:
        logger.error(f"Failed to fetch user data: {err}")
        return ToolMessage(
            content=f"Failed to fetch user data due to an error: {err}", status="error", tool_call_id=tool_call_id
        )

    return Command(
        update={
            "locations": [i.to_dict() for i in user_data.locations],
            "vehicles": [i.to_dict() for i in user_data.vehicles],
            "preferences": [i.to_dict() for i in user_data.preferences],
            "messages": [
                ToolMessage(
                    content="User data has been loaded into the internal state.",
                    status="success",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )


@tool
def retriever_tool(
    tool_call_id: Annotated[str, InjectedToolCallId],
    query: str,
    top_k: int = 5,
) -> Command:
    """
    A tool for retrieving relevant parking information from the vector database.

    Purpose:
        - Retrieve up-to-date parking lot details, features, policies, and pricing for personalized recommendations.

    Use Cases:
        - Use when the user requests parking information not already in context.

    Args:
        - tool_call_id (str): The unique identifier for the tool call.
        - query (str): The user's query for which relevant parking information needs to be retrieved.
        - top_k (int): The number of relevant parking lot information to retrieve from the vector database.

    Returns:
        - Command: {
            "retrieved_parking_info": [ ... ],
            "messages": "ToolMessage that describes the retrieved information or an error message if retrieval fails."
        }
        - Returns an error message if the query fails.
    """
    logger.info(f"Retrieving parking information for query: '{query}' with top_k: {top_k}")
    try:
        retriever = ParkingInfoRetriever(top_k=top_k)
        parking_info_list = retriever.retrieve(query)
        logger.info(f"Retriever tool completed successfully and returns '{len(parking_info_list)}' items.")
        return Command(
            update={
                "retrieved_parking_info": parking_info_list,
                "messages": [
                    ToolMessage(
                        content=f"The retrieved parking information: {parking_info_list}",
                        status="success",
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )
    except Exception as err:
        logger.error(f"Retriever tool failed: {err}")
        return ToolMessage(
            content=f"Failed to retrieve parking information due to an error: {err}",
            status="error",
            tool_call_id=tool_call_id,
        )


@tool
def websearch_tool(search_query: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> dict:
    """
    A tool that performs a web search using the provided query to retrieve up-to-date information relevant to parking space reservations or user inquiries.

    Use Cases:
        - Use when the required parking information is not available in the internal database or context.
        - Use to check for real-time events, news, traffic information, or external parking options.
        - Use to supplement recommendations with the latest web data.
        - Do not use for information already available or when privacy is a concern.

    Security:
        - Only use this tool when necessary and do not send sensitive or personal information in the search query.

    Example:
        - "free parking lots near Central Station"
        - "current traffic conditions around downtown"

    Args:
        search_query (str): The query for a websearch to gather additional information from the web.
        tool_call_id (str): The unique identifier for the tool call.

    Returns:
        dict: The result of the websearch operation, or an error message if the websearch operation failed.
        - query: The exact string you sent to the API.
        - answer: A brief LLM-generated summary of the results (only populated if you set include_answer=True).
        - follow_up_questions: Suggested next queries based on your search (only if requested).
        - images: A list of image URLs found during the search (only if requested).
        - results: A list of search results, where each result includes:
            - title: The name of the page.
            - url: The direct link to the source.
            - content: A cleaned snippet of the page text (ideal for RAG/context).
            - score: A relevancy score (higher is better).
            - raw_content: The full page content (only populated if you set include_raw_content=True).
    """
    if not search_query:
        logger.warning("Websearch tool invoked with an empty search query.")
        return ToolMessage(
            content="Search query cannot be empty. Please provide a valid query to perform a websearch.",
            status="error",
            tool_call_id=tool_call_id,
        )

    logger.info(f"Performing websearch with the query: {search_query}")
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY").replace("'", "").replace('"', "")
        tavily_client = TavilyClient(api_key=tavily_api_key)
        result = tavily_client.search(search_query)
        logger.info(f"Websearch result is {len(result)} character long that returned.")
        return ToolMessage(content=result, status="success", tool_call_id=tool_call_id)
    except Exception as err:
        logger.error(f"Websearch tool failed: {err}")
        return ToolMessage(
            content=f"Failed to perform websearch due to an error: {err}",
            status="error",
            tool_call_id=tool_call_id,
        )


def _classify_reservations(reservations):
    """Split a list of reservation dicts into pending, booked, completed."""
    pending = [r for r in reservations if r["status"] == ReservationStatus.PENDING.value.upper()]
    booked = [r for r in reservations if r["status"] == ReservationStatus.BOOKED.value.upper()]
    completed = [
        r
        for r in reservations
        if r["status"] in [ReservationStatus.COMPLETED.value.upper(), ReservationStatus.CANCELLED.value.upper()]
    ]
    return pending, booked, completed


def _summarize_reservations(items):
    """Format a list of reservation dicts into a short human-readable string."""
    return "; ".join(
        f"{r.get('reservation_id')} ({r.get('parking_lot_id')}, {str(r.get('start_time'))} to {str(r.get('end_time'))})"
        for r in items
    )


def _safe_replace(query, replacements: dict):
    """Safely replace placeholders in a query string with provided values."""
    result = query
    for field, value in replacements.items():
        result = result.replace(field, str(value) if field in result else result)
    return result


def _format_reservation_content(pending, booked, completed, username):
    """Build a human-readable summary string for the LLM from categorized reservations."""
    parts = []
    if pending:
        parts.append(f"PENDING ({len(pending)}): {_summarize_reservations(pending)}")
    if booked:
        parts.append(f"BOOKED ({len(booked)}): {_summarize_reservations(booked)}")
    if completed:
        parts.append(f"COMPLETED/CANCELLED ({len(completed)}): {_summarize_reservations(completed)}")
    if parts:
        return f"Reservations for '{username}':\n{'; '.join(parts)}"
    return f"No reservations found for '{username}'."


@tool
def database_query_tool(
    runtime: ToolRuntime[ApsrSessionContext, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    action: str,
    reservation_id: str = None,
) -> dict:
    """
    A tool for retrieving or cancelling reservations from the database using prepared actions.

    Args:
        - action (str): The action to perform. Options:
            - GET_RESERVATIONS: Fetch ALL reservations (pending, booked, completed, cancelled) for the current user.
            - CANCEL_RESERVATION: Cancel a pending reservation by reservation_id. Requires `reservation_id`.
        - reservation_id (str, optional): Required only for CANCEL_RESERVATION.
        - runtime (ToolRuntime): The runtime context, providing access to the current user's session.
        - tool_call_id (str): The unique identifier for the tool call.
    Returns:
        - Command: Updates the agent state with reservation data and adds a ToolMessage to the conversation.

    Examples:
        - action='GET_RESERVATIONS' → fetches all reservations for the logged-in user.
        - action='CANCEL_RESERVATION', reservation_id='res_hu_0726_1234' → cancels that reservation.
    """
    logger.info(f"Executing database query for the action: '{action}'")
    if action == "CANCEL_RESERVATION" and not reservation_id:
        return ToolMessage(
            content="Reservation ID is required to cancel a reservation. Please provide a valid reservation ID.",
            status="error",
            tool_call_id=tool_call_id,
        )

    query_template = ""
    match action:
        case "GET_RESERVATIONS":
            query_template = (
                "SELECT * FROM reservations r INNER JOIN users u ON r.user_id = u.id WHERE u.username = '<username>';"
            )
        case "CANCEL_RESERVATION":
            query_template = f"UPDATE reservations SET status = 'CANCELLED' WHERE reservation_id = '{reservation_id}';"

    try:
        db_service = DatabaseService()
        username = _session_field(runtime, "username")
        vehicle_id = _session_field(runtime, "vehicle_id")
        final_query = _safe_replace(
            query_template,
            {"<username>": username, "<vehicle_id>": str(vehicle_id), "<reservation_id>": str(reservation_id)},
        )
        result = db_service.execute_query(sqlalchemy.text(final_query))
        reservations = [item._asdict() for item in result]

        logger.info("Database query executed successfully.")
        pending_reservations, booked_reservations, completed_reservations = _classify_reservations(reservations)
        if action == "GET_RESERVATIONS":
            content = _format_reservation_content(
                pending_reservations, booked_reservations, completed_reservations, username
            )
            return Command(
                update={
                    "pending_reservations": {r["reservation_id"]: r for r in pending_reservations},
                    "booked_reservations": {r["reservation_id"]: r for r in booked_reservations},
                    "completed_reservations": {r["reservation_id"]: r for r in completed_reservations},
                    "messages": [
                        ToolMessage(
                            content=content,
                            status="success",
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )
        if action == "CANCEL_RESERVATION":
            logger.info(f"Reservation with ID '{reservation_id}' has been cancelled successfully.")
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            content=f"Reservation with ID '{reservation_id}' has been cancelled successfully.",
                            status="success",
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )
        return ToolMessage(content=result, status="success", tool_call_id=tool_call_id)
    except Exception as err:
        logger.exception(f"Database tool failed: {err}")
        return ToolMessage(
            content=f"Database query failed due to an error: {err}, please try again with a valid query.",
            status="error",
            tool_call_id=tool_call_id,
        )


@tool
def reservation_detail_creation_tool(
    runtime: ToolRuntime[ApsrSessionContext, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    parkinglot_id: str,
    parking_place_category: str,
    start_time: datetime,
    end_time: datetime,
) -> Command:
    """
    A tool for creating a new reservation detail object in the internal state.
    Use this tool to collect all necessary information for a reservation that needs to be submitted later.
    This tool does not submit the reservation; it only prepares and saves the reservation details in the internal state.

    Args:
        runtime (ToolRuntime): The runtime context for the tool, providing access to the current user's session and other runtime information.
        tool_call_id (str): The unique identifier for the tool call.
        parkinglot_id (str): The ID of the parking lot for the reservation.
        parking_place_category (str): The category of the parking lot like "Open-air", "Multi-storey", "Ground-level", or "Underground".
        start_time (datetime): The start time of the parking reservation.
        end_time (datetime): The end time of the parking reservation.

    Returns:
        Command: A command to update the internal state with the new reservation details.
    """
    logger.info("Creating reservation detail in internal state.")
    try:
        reservation_details = ReservationDetails(
            user_name=_session_field(runtime, "username"),
            vehicle_id=_session_field(runtime, "vehicle_id"),
            parking_lot_id=parkinglot_id,
            parking_space_category=parking_place_category,
            start_time=start_time,
            end_time=end_time,
        )
        return Command(
            update={
                "reservation_details": reservation_details,
                "messages": [
                    ToolMessage(
                        content="Reservation details have been created in the internal state.",
                        status="success",
                        tool_call_id=tool_call_id,
                    )
                ],
            }
        )
    except Exception as err:
        logger.warning(f"Failed to create reservation detail: {err}")
        return ToolMessage(
            content=f"Failed to create reservation detail due to an error: {err}",
            status="error",
            tool_call_id=tool_call_id,
        )


@tool
def reservation_tool(
    runtime: ToolRuntime[ApsrSessionContext, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    reservation_details: ReservationDetails,
) -> Command | ToolMessage:
    """
    A tool for creating a new parking space reservation in the specified parking lot for the user and time period provided.
    This tool will interact with the database to create a new reservation entry.

    Use Cases:
        - Use this tool when the user has selected a parking lot and time for reservation and you need to create the reservation in the system.

    Args:
        runtime (ToolRuntime): The runtime context for the tool, providing access to the current user's session and other runtime information.
        tool_call_id (str): The unique identifier for the tool call.
        parking_lot_id (str): The ID of the parking lot where the reservation is to be made.
        category (str): The category of the parking lot like "Open-air", "Multi-storey", "Ground-level", or "Underground".
        reservation_time (dict): A dictionary containing the "start" and "end" time of the reservation.

    Returns:
        dict: A dictionary containing the result of the reservation attempt.
            - "success" (bool): True if the reservation was successful, False otherwise.
            - "error" (str): An error message if the reservation failed.
            - "details" (dict): A dictionary with reservation details if the reservation was successful, including:
                - "created" (bool): True if the reservation was created successfully.
                - "status" (str): The status of the reservation.
                - "reservation_id" (str): The reservation ID.
                - "username" (str): The username of the user who made the reservation.
    """
    logger.info("Reservation tool called.")
    if not reservation_details:
        return ToolMessage(
            content="Reservation details are missing. Please provide the required data to make a reservation.",
            status="error",
            tool_call_id=tool_call_id,
        )

    username = _session_field(runtime, "username")
    # Silent session detail refinement
    selected_vehicle_id = _session_field(runtime, "vehicle_id")
    if username != reservation_details.user_name:
        reservation_details.user_name = username
    if selected_vehicle_id != reservation_details.vehicle_id:
        reservation_details.vehicle_id = selected_vehicle_id

    reservation_fields = ["user_name", "parking_lot_id", "parking_space_category", "start_time", "end_time"]
    username, parking_lot_id, category, start_time, end_time = [
        getattr(reservation_details, attr) for attr in reservation_fields
    ]
    reservation_msg = "Reservation details: user_name={}, parking_lot_id={}, category={}, start_time={}, end_time={}"
    logger.info(reservation_msg.format(username, parking_lot_id, category, start_time, end_time))
    try:
        if selected_vehicle_id is None:
            return ToolMessage(
                content="No selected_vehicle_id provided. Please provide the required data to make a reservation.",
                status="error",
                tool_call_id=tool_call_id,
            )

        db_service = DatabaseService()
        now = datetime.now(UTC)
        year, month = now.year, now.month
        seq_id = random.randint(1, 9999)
        reservation_data = ReservationEntity(
            vehicle_id=selected_vehicle_id,
            reservation_id=f"res_hu_{year}{month:02d}_{seq_id}",
            reservation_time=now,
            parking_lot_id=parking_lot_id,
            parking_space_category=category,
            start_time=start_time,
            end_time=end_time,
            status=ReservationStatus.PENDING,
        )

        result = db_service.create_reservation(username, reservation_data)
        if not result:
            logger.error(f"❌ Failed to create reservation for user {username} at parking lot {parking_lot_id}.")
            return ToolMessage(
                content=f"Failed to create reservation for user {username} at parking lot {parking_lot_id}.",
                status="error",
                tool_call_id=tool_call_id,
            )

        logger.info(f"✅ Reservation created successfully for user {username} at parking lot {parking_lot_id}.")
        updated_reservation_details = {**reservation_data.to_dict(), "user_name": username}
        return Command(
            update={
                "reservation_details": updated_reservation_details,
                "pending_reservations": {**runtime.state.pending_reservations, result["reservation_id"]: result},
                "messages": [
                    ToolMessage(
                        content=f"Reservation created successfully with the id of: {result['reservation_id']}",
                        status="success",
                        tool_call_id=tool_call_id,
                    )
                ],
            },
        )
    except Exception as err:
        logger.error(f"Reservation tool failed: {err}")
        return ToolMessage(
            content=f"Failed to create reservation due to an error: {err}", status="error", tool_call_id=tool_call_id
        )


@tool
def reservation_persistence_tool(
    runtime: ToolRuntime[ApsrSessionContext, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    reservation_data: ReservationDetails,
    status: str,
) -> ToolMessage:
    """Persist a reservation snapshot into local JSON files via Filesystem MCP server.
    Use this always when a new reservation is created to ensure you have a local file copy for auditing, traceability.

    Args:
        runtime (ToolRuntime): The runtime context to access the current user's session and other runtime information.
        tool_call_id (str): The unique identifier for the tool call.
        reservation_data (ReservationDetails): The reservation details to be persisted.
        status (str): The status of the reservation.
    """
    username = _session_field(runtime, "username")
    selected_vehicle_id = _session_field(runtime, "vehicle_id")

    try:
        result = save_reservation_snapshot_via_mcp(
            {
                "reservation_id": reservation_data.reservation_id,
                "username": username,
                "vehicle_id": selected_vehicle_id,
                "parking_lot_id": reservation_data.parking_lot_id,
                "category": reservation_data.parking_space_category,
                "start_time": str(reservation_data.start_time),
                "end_time": str(reservation_data.end_time),
                "status": status.upper(),
                "created_at": reservation_data.registration_time.isoformat(),
            }
        )
        return ToolMessage(
            content=(f"Reservation snapshot persisted successfully, available at location: {result.get('path')}."),
            status="success",
            tool_call_id=tool_call_id,
        )
    except Exception as err:
        logger.warning(f"Failed to persist reservation snapshot for {reservation_data.reservation_id}: {err}")
        return ToolMessage(
            content=f"Failed to persist reservation snapshot via MCP: {err}",
            status="error",
            tool_call_id=tool_call_id,
        )
