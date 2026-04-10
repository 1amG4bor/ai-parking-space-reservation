"""The following script is used to populate the SQL database with initial data for testing and development purposes."""

from dotenv import load_dotenv
from sqlalchemy import insert
from sqlalchemy.orm import Session

from chat_engine.core.utils.db_tool import DatabaseService
from chat_engine.models.database import UserEntity, LocationEntity, VehicleEntity
from evaluation.data.users_data import test_users

load_dotenv()

def run(users: list[dict], clean_up: bool = False):
    """Run the script to populate the SQL database with initial data."""

    db_service = DatabaseService()
    session = Session(db_service._engine)

    # Clear existing data (optional, be cautious with this in production)
    if clean_up:
        VehicleEntity.metadata.drop_all(db_service._engine)
        LocationEntity.metadata.drop_all(db_service._engine)
        UserEntity.metadata.drop_all(db_service._engine)
        print("🧹 Cleaned up existing data from the database.")
    
    # Create tables if they don't exist
    print("📦 Initializing database and creating tables if they don't exist...")
    UserEntity.metadata.create_all(db_service._engine)
    LocationEntity.metadata.create_all(db_service._engine)
    VehicleEntity.metadata.create_all(db_service._engine)


    print(f"🚀 Populating the database with {len(users)} users...")
    for user in users:
        user_entity = UserEntity.from_dict(user)
        session.add(user_entity)
    else:
        session.commit()
        print(f"✅ Successfully populated the database with {len(users)} users.")

                       

if __name__ == "__main__":
    # users = []
    users = test_users
    run(users=users, clean_up=True)
