"""This script is for testing the semantic search functionality of the vector database.
It connects to a local Weaviate instance, queries the "ParkingLotInfo" collection for objects similar to the 'query',
and prints the retrieved objects' properties in a readable format."""

import json
import sys
import time
import weaviate


def semantic_search(query: str, top_k: int = 5):
    """Performs a semantic search on the Weaviate vector database for parking lot information."""
    print(f"🔍 Performing semantic search for query: '{query}' with top_k={top_k}...")
    time.sleep(2)
    with weaviate.connect_to_local() as client:
        parking_lot_info = client.collections.use("ParkingLotInfo")
        print("Querying the vector database...")
        response = parking_lot_info.query.near_text(query=query, limit=top_k)
        print(f"Retrieved objects: {len(response.objects)}")  # Debugging statement
        for obj in response.objects:
            print(json.dumps(obj.properties, indent=2))  # Inspect the results


if __name__ == "__main__":
    args = sys.argv[1:] or []

    query = args[0] if len(args) > 0 else "Budapest airport."
    top_k = int(args[1]) if len(args) > 1 else 5

    semantic_search(query, top_k)
