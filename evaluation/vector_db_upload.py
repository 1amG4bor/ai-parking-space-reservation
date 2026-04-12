"""This script is responsible for uploading data to the vector database."""
import os
import json
import weaviate
from weaviate.classes.config import Configure, Property, DataType

ROOT_FOLDER = os.getcwd()

def upload_data_to_vector_db(file_path: str):
    source_data = _load_data_from_source(file_path)
    collection_name = "ParkingLotInfo"

    
    # Connect to vector database
    with weaviate.connect_to_local() as client:
        # Delete the collection if already exists
        print(f"Checking if collection '{collection_name}' exists...")
        if client.collections.exists(collection_name):
            print(f"The '{collection_name}' collection exists, deleting it...")
            client.collections.delete(collection_name)

        # Recreate the collection with the defined schema and vectorization configuration
        capacity_related_properties = [
            Property(name="general", data_type=DataType.INT),
            Property(name="underground", data_type=DataType.INT),
            Property(name="ground", data_type=DataType.INT),
            Property(name="multi_storey", data_type=DataType.INT),
        ]


        print(f"Creating the collection: '{collection_name}'...")
        parking_lot_info = client.collections.create(
            name="ParkingLotInfo",
            properties=[
                Property(name="parking_lot_id", data_type=DataType.TEXT),
                Property(name="name", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
                Property(name="type", data_type=DataType.TEXT),
                Property(name="features", data_type=DataType.TEXT_ARRAY),
                Property(name="restrictions", data_type=DataType.TEXT_ARRAY),
                Property(name="amenities", data_type=DataType.TEXT_ARRAY),
                Property(name="capacity", data_type=DataType.OBJECT, nested_properties=capacity_related_properties),
                Property(name="price", data_type=DataType.OBJECT, nested_properties=capacity_related_properties),
                Property(name="address", data_type=DataType.TEXT),
                Property(name="coordinate", data_type=DataType.NUMBER_ARRAY),
                Property(name="operating_hours", data_type=DataType.OBJECT,
                    nested_properties=[
                        Property(name="open", data_type=DataType.TEXT),
                        Property(name="close", data_type=DataType.TEXT),
                    ]),
            ],
            vector_config=Configure.Vectors.text2vec_ollama(
                api_endpoint="http://ollama:11434",
                model="nomic-embed-text",
            )
        )

        parking_lot_info = client.collections.use("ParkingLotInfo")

        print(f"Importing data into the collection...")
        with parking_lot_info.batch.fixed_size(batch_size=10) as batch:
            for record in source_data:
                batch.add_object(properties=record)
    
    print(f"Imported & vectorized {len(source_data)} records into 'ParkingLotInfo' collection of vector database.")


def _load_data_from_source(file_path: str):
    with open(file_path, "r", encoding="utf-8") as file:
        source_data = json.load(file)
    return source_data


if __name__ == "__main__":
    source_file_name = "parking_lot_data.json"
    data_source_file = os.path.join(ROOT_FOLDER, "data", source_file_name)
    upload_data_to_vector_db(data_source_file)

