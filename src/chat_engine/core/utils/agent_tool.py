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

from chat_engine.core.agents.agent_models import ApsrSessionContext
from chat_engine.core.config.logging import logger
from chat_engine.core.rag.retriever import ParkingInfoRetriever
from chat_engine.core.utils.db_tool import DatabaseService
from chat_engine.models.db_entities import ReservationEntity
from chat_engine.models.enums import ReservationStatus


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
    username = runtime.context.username
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


@tool
def database_tool(query: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> str:
    """
    A tool for executing read-only queries on the database to retrieve user information, preferences, and other relevant data for personalized parking space recommendations.
    **Note**:
    - The database is postgres with version 15.17; provide queries with the correct syntax and supported features on Postgres 15.17.
    - This tool is strictly for data retrieval (read-only). **DO NOT** use it to modify, update, or delete any database records.

    Args:
        - query (str): A SQL-like query string to retrieve specific information from the database.
        - tool_call_id (str): The unique identifier for the tool call.
    Returns:
        - str: The query result as a string, or an error message if the query fails.

    Example:
        - To fetch all parking reservations for a user: `SELECT * FROM reservations WHERE user_id = '12345';`
    """
    logger.info(f"Executing database query: '{query}'")
    try:
        db_service = DatabaseService()
        executable_query = sqlalchemy.text(query)
        result = db_service.execute_query(executable_query)
        logger.info("Database query executed successfully.")
        return ToolMessage(content=result, status="success", tool_call_id=tool_call_id)
    except Exception as err:
        logger.warning(f"Database tool failed: {err}")
        return ToolMessage(
            content=f"Database query failed due to an error: {err}, please try again with a valid query.",
            status="error",
            tool_call_id=tool_call_id,
        )


@tool
def reservation_tool(
    runtime: ToolRuntime[ApsrSessionContext, Any],
    tool_call_id: Annotated[str, InjectedToolCallId],
    parking_lot_id: str,
    category: str,
    reservation_time: dict,
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
    username = runtime.context.username
    selected_vehicle_id = runtime.context.vehicle_id
    logger.info(
        f"Making reservation for user '{username}' at parking lot {parking_lot_id} ({category}) from {reservation_time['start']} to {reservation_time['end']}"
    )
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
            reservation_id=f"res_hu_{month}{year}_{seq_id}",
            reservation_time=now,
            parking_lot_id=parking_lot_id,
            parking_space_category=category,
            start_time=reservation_time["start"],
            end_time=reservation_time["end"],
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
        return Command(
            update={
                "inactive_reservations": {result["reservation_id"]: result},
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
