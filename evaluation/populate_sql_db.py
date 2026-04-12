"""The following script is used to populate the SQL database with initial data for testing and development purposes."""

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from chat_engine.core.utils.db_tool import DatabaseService
from chat_engine.models.db_entities import UserEntity, VehicleEntity, LocationEntity, ReservationEntity
from evaluation.data.users_data import test_users
from evaluation.data.reservation_data import test_reservations


load_dotenv()

def run(users: list[dict], reservations: list[dict], clean_up: bool = False):
    """Run the script to populate the SQL database with initial data."""

    db_service = DatabaseService()
    session = Session(db_service._engine)

    # Clear existing data (optional, be cautious with this in production)
    if clean_up:
        ReservationEntity.metadata.drop_all(db_service._engine)
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

    print(f"🚀 Populating the database with {len(reservations)} reservations...")
    for reservation in reservations:
        reservation_entity = ReservationEntity.from_dict(reservation)
        session.add(reservation_entity)
    else:
        session.commit()
        print(f"✅ Successfully populated the database with {len(reservations)} reservations.")

if __name__ == "__main__":
    run(users=test_users, reservations=test_reservations, clean_up=True)
