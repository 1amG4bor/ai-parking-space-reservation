"""This script is for testing the semantic search functionality of the vector database.
It connects to a local Weaviate instance, queries the "ParkingLotInfo" collection for objects similar to the 'query',
and prints the retrieved objects' properties in a readable format."""

import weaviate
import json


def semantic_search(query: str, top_k: int = 5):
    """Performs a semantic search on the Weaviate vector database for parking lot information."""
    with weaviate.connect_to_local() as client:
        parking_lot_info = client.collections.use("ParkingLotInfo")

        print("Querying the vector database...")
        response = parking_lot_info.query.near_text(
            query=query,
            limit=top_k
        )
        print(f"Retrieved objects: {len(response.objects)}")  # Debugging statement
        for obj in response.objects:
            print(json.dumps(obj.properties, indent=2))  # Inspect the results

if __name__ == "__main__":
    query = "Budapest airport."
    num_of_results = 5
    semantic_search(query, num_of_results)
