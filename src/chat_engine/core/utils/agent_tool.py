import os

from langchain.tools import tool, ToolRuntime
from tavily import TavilyClient

from chat_engine.core.rag.retriever import ParkingInfoRetriever
from chat_engine.core.config.logging import logger
from fastapi import HTTPException

from chat_engine.core.utils.db_tool import DatabaseService


@tool
def guardrail_tool(query: str) -> dict:
    """
    A tool for checking the intent of the user's query before going further and taking any action.
    Use this tool to check any query and prevent exposure of sensitive data and/or avoid any inappropriate or malicious act.

    Args:
        query (str): The query to be checked.

    Returns:
        dict: A dictionary containing the result of the guardrail check.
        - blocked (bool): True if the query is blocked by the guardrail, False otherwise.
        - reason (str): The reason why the query is blocked, if applicable.
        - suggestions (list): A list of suggestions for modifying the query to make it acceptable, if applicable.
    """
    logger.info(f"Guardrail check for the user's query: {query}")
    
    

@tool
def user_info_tool(runtime: ToolRuntime) -> dict:
    """
    A tool for getting information about the users, like their vehicles, locations, and their preferences.
    These fetched information can be used to assist in finding parking lots that match the user's criteria, habits, and needs.
    
    Examples:
    - If a user has a preference for underground parking, the agent can prioritize suggesting underground parking lots when providing recommendations.
    - If a user has multiple vehicles, the agent can consider the suggest other vehicle that can fit into the parking lot requirement when searching for parking spaces.
    - If a user has multiple locations, the agent can consider the location of the user when searching for parking spaces, and prioritize parking lots that are closer to the user's location.

    Args:
        runtime (ToolRuntime): The runtime context provided by the agent when invoking the tool, which can be used to access relevant information about the user and the conversation.
    """
    logger.info(f"Getting user preferences.")
    username = runtime.state.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="User is not authenticated.")

    # Fetch user preferences from the database.
    db_service = DatabaseService()
    user_data = db_service.get_user_by_username(username)
    if not user_data:
        return {}
    
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

    Args:
        query (str): The user's query for which relevant parking information needs to be retrieved.
        top_k (int): The number of relevant parking lot information to retrieve from the vector database.
    """
    logger.info(f"Retrieving parking information for query: {query} with top_k: {top_k}")
    retriever = ParkingInfoRetriever(top_k=top_k)
    parking_info = retriever.retrieve(query)
    logger.info(f"Retrieved {len(parking_info)} parking information.")
    return parking_info


@tool
def websearch_tool(search_query: str) -> str:
    """
    A tool for performing a websearch operation based on the user's query.

    Args:
        search_query (str): The query for a websearch so that the agent can gather additional information from the web to assist the user with providing information or their parking space reservation.
    
    Returns:
        dict: The result of the websearch operation.
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
    logger.info(f"Performing websearch with the query: {search_query}")
    tavily_api_key = os.getenv("TAVILY_API_KEY").replace("'", "").replace('"', '')
    tavily_client = TavilyClient(api_key=tavily_api_key)
    result = tavily_client.search(search_query)
    logger.info(f"Websearch result is {len(result)} character long.")
    return result


@tool
def reservation_tool(parking_lot_id: str, category: str, user_id: str, reservation_time: dict) -> bool:
    """
    A tool for making a reservation for a parking space.

    Args:
        parking_lot_id (str): The ID of the parking lot where the reservation is to be made.
        category (str): The category of the parking lot like "general", "underground", "ground", or "multi_storey".
        user_id (str): The ID of the user making the reservation.
        reservation_time (dict): A dictionary containing the "start" and "end" time of the reservation.

    Returns:
        bool: True if the reservation was successful, False otherwise.
    """
    # Placeholder for reservation logic
    logger.info(f"Making reservation for user {user_id} at parking lot {parking_lot_id} ({category}) from {reservation_time['start']} to {reservation_time['end']}")
    # TODO: Implement actual reservation logic here.
    return True