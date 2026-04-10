import weaviate
import json


with weaviate.connect_to_local() as client:
    parking_lot_info = client.collections.use("ParkingLotInfo")

    print("Querying the vector database...")
    response = parking_lot_info.query.near_text(
        query="Budapest airport.",
        limit=5
    )
    print(f"Retrieved objects: {len(response.objects)}")  # Debugging statement
    for obj in response.objects:
        print(json.dumps(obj.properties, indent=2))  # Inspect the results