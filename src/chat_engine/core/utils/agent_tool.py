from datetime import datetime, UTC
import os
import random

from langchain.tools import tool, ToolRuntime
from tavily import TavilyClient

from chat_engine.core.rag.retriever import ParkingInfoRetriever
from chat_engine.core.config.logging import logger
from fastapi import HTTPException

from chat_engine.core.utils.db_tool import DatabaseService
from chat_engine.models.db_entities import ReservationEntity
from chat_engine.models.enums import ReservationStatus


@tool
def user_info_tool(runtime: ToolRuntime) -> dict:
    """
    A tool for getting information about the users, like their vehicles, locations, and their preferences.
    Use this tool to get the user's information and preferences that can assist you in providing personalized recommendations for parking spaces.

    Examples:
    - If a user has a preference for underground parking, the agent can prioritize suggesting underground parking lots when providing recommendations.
    - If a user has multiple vehicles, the agent can consider the suggest other vehicle that can fit into the parking lot requirement when searching for parking spaces.
    - If a user has multiple locations, the agent can consider the location of the user when searching for parking spaces, and prioritize parking lots that are closer to the user's location.

    Args:
        runtime (ToolRuntime): The runtime context provided by the agent when invoking the tool, which can be used to access relevant information about the user and the conversation.
    """
    logger.info(f"Getting user preferences.")
    username = runtime.context.username
    if not username:
        raise HTTPException(status_code=401, detail="User is not authenticated.")

    # Fetch user preferences from the database.
    try:
        db_service = DatabaseService()
        user_data = db_service.get_user_by_username(username)
        if not user_data:
            return {}
    except Exception as err:
        logger.error(f"Failed to fetch user data: {err}")
        return "Failed to fetch user data. Please try again."

    user_info = {
        "vehicles": user_data.vehicles,
        "location": user_data.location,
        # "preferences": user_data.preferences,
    }
    return user_info


@tool
def retriever_tool(query: str, top_k: int = 5) -> str:
    """
    A tool for retrieving relevant parking information from the vector database based on the user's query.
    Use this tool to get relevant parking lot information, parking space features, reservation policies, pricing and payment options, operating hours, and any restrictions that can assist you in providing accurate and personalized recommendations for parking spaces.

    Args:
        query (str): The user's query for which relevant parking information needs to be retrieved.
        top_k (int): The number of relevant parking lot information to retrieve from the vector database.

    Returns:
        str: The retrieved parking information relevant to the user's query, or an error message if the retrieval operation failed.
    """
    logger.info(f"Retrieving parking information for query: '{query}' with top_k: {top_k}")
    try:
        retriever = ParkingInfoRetriever(top_k=top_k)
        parking_info = retriever.retrieve(query)
        logger.info(f"Retriever tool succeeded.")
    except Exception as err:
        logger.error(f"Retriever tool failed: {err}")
        return f"Failed to retrieve parking information. Please try again. Error: {err}"

    return parking_info


@tool
def websearch_tool(search_query: str) -> str:
    """
    A tool for performing a websearch operation based on the user's query.
    Use this tool to gather additional information from the web to assist you with providing information or their parking space reservation.

    Args:
        search_query (str): The query for a websearch so that the agent can gather additional information from the web to assist the user with providing information or their parking space reservation.

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
        return "Search query cannot be empty. Please provide a valid query to perform a websearch."

    logger.info(f"Performing websearch with the query: {search_query}")
    try:
        tavily_api_key = os.getenv("TAVILY_API_KEY").replace("'", "").replace('"', "")
        tavily_client = TavilyClient(api_key=tavily_api_key)
        result = tavily_client.search(search_query)
        logger.info(f"Websearch result is {len(result)} character long.")
        return result
    except Exception as err:
        logger.error(f"Websearch tool failed: {err}")
        return f"Failed to perform websearch. Please try again. Error: {err}"


@tool
def reservation_tool(runtime: ToolRuntime, parking_lot_id: str, category: str, reservation_time: dict) -> bool:
    """
    A tool for making a reservation for a parking space.
    Use this tool to make a reservation for a parking space based on the provided information about the parking lot, user, and reservation time.
    This tool will interact with the database to create a new reservation entry.

    Args:
        runtime (ToolRuntime): The runtime context for the tool, providing access to the current user's session and other runtime information.
        parking_lot_id (str): The ID of the parking lot where the reservation is to be made.
        category (str): The category of the parking lot like "general", "underground", "ground", or "multi_storey".
        reservation_time (dict): A dictionary containing the "start" and "end" time of the reservation.

    Returns:
        bool: True if the reservation was successful, False otherwise.
        str: An error message if the reservation failed.
    """
    # Placeholder for reservation logic
    username = runtime.context.username
    selected_vehicle_id = runtime.context.selected_vehicle
    logger.info(
        f"Making reservation for user '{username}' at parking lot {parking_lot_id} ({category}) from {reservation_time['start']} to {reservation_time['end']}"
    )
    try:
        if selected_vehicle_id is None:
            raise ValueError("No vehicle selected for the reservation.")

        db_service = DatabaseService()
        now = datetime.now(UTC)
        year, month = now.year, now.month
        id = random.randint(1, 9999)
        reservation_data = ReservationEntity(
            vehicle_id=selected_vehicle_id,
            reservation_id=f"res_hu_{month}{year}_{id}",
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
            return False
        logger.info(f"✅ Reservation created successfully for user {username} at parking lot {parking_lot_id}.")
        return True
    except Exception as err:
        logger.error(f"Reservation tool failed: {err}")
        return f"Failed to create reservation. Please try again. Error: {err}"


@tool
def database_tool(query: str) -> str:
    """
    A tool for interacting with the database to fetch user information, preferences, and relevant data that can assist in providing personalized recommendations for parking spaces.
    Use this tool to execute a query on the database to fetch relevant information that can assist you in providing accurate and personalized recommendations for parking spaces.
    Important! This tool can be used only to fetch data from the database, and should not be used to modify or delete any data in the database.

    Args:
        query (str): The query to be executed on the database.

    Returns:
        str: The result of the database query, or an error message if the query failed.
    """
    logger.info(f"Executing database query: '{query}'")
    try:
        db_service = DatabaseService()
        result = db_service.execute_query(query)
        logger.info(f"Database query executed successfully.")
        return result
    except Exception as err:
        logger.warning(f"Database tool failed: {err}")
        return f"Database query failed: {err}, please try again with a valid query."
