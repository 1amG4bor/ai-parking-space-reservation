"""Service for database operations, including initialization and connection management."""

from datetime import datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload

from chat_engine.core.config.config import ConfigManager
from chat_engine.core.config.logging import logger
from chat_engine.core.utils.patterns import Singleton
from chat_engine.models.db_entities import (
    LocationEntity,
    PreferenceEntity,
    ReservationEntity,
    UserEntity,
    VehicleEntity,
)
from chat_engine.models.enums import ReservationStatus


class DatabaseService(metaclass=Singleton):
    """
    A service class responsible for managing database connections and operations.
    """

    def __init__(self):
        cfg_manager = ConfigManager()
        try:
            db_url_template = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
            self._db_url = db_url_template.format(
                user=cfg_manager.get_config("DATABASE_USER"),
                password=cfg_manager.get_config("DATABASE_PASSWORD"),
                host=cfg_manager.get_config("DATABASE_HOST"),
                port=cfg_manager.get_config("DATABASE_PORT"),
                db=cfg_manager.get_config("DATABASE_NAME"),
            )
            # Initialize database connection here (e.g., using SQLAlchemy)
            self._engine = create_engine(self._db_url)
            self._initialize_database()
        except Exception as err:
            logger.error(f"❌ Failed to initialize connection to the database: {err}")
            raise ConnectionError(f"Failed to connect to the database: {err}") from err

    def _initialize_database(self):
        """Initialize the database schema and tables if they don't exist."""
        # Initialize connection and create tables if necessary
        try:
            with self._engine.connect():
                logger.info("✅ Successfully connected to the database.")
                # Create tables if they don't exist
                UserEntity.metadata.create_all(self._engine)
                LocationEntity.metadata.create_all(self._engine)
                VehicleEntity.metadata.create_all(self._engine)
                ReservationEntity.metadata.create_all(self._engine)
                PreferenceEntity.metadata.create_all(self._engine)
                logger.info("✅ Database tables are initialized and ready.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize the database: {e}")
            raise ConnectionError(f"Failed to initialize the database: {e}") from e

    def get_user_by_email(self, email: str):
        """Fetch a user from the database by their email, including locations and vehicles."""
        with Session(self._engine) as session:
            stmt = (
                select(UserEntity)
                .options(
                    selectinload(UserEntity.locations),
                    selectinload(UserEntity.vehicles),
                    selectinload(UserEntity.preferences),
                    selectinload(UserEntity.reservations),
                )
                .where(UserEntity.email == email)
            )
            return session.execute(stmt).scalars().first()

    def get_user_by_username(self, username: str):
        """Fetch a user from the database by their username, including locations and vehicles."""
        with Session(self._engine) as session:
            stmt = (
                select(UserEntity)
                .options(
                    selectinload(UserEntity.locations),
                    selectinload(UserEntity.vehicles),
                    selectinload(UserEntity.preferences),
                )
                .where(UserEntity.username == username)
            )
            return session.execute(stmt).scalars().first()

    def add_user(self, user_data: dict):
        """Add a new user to the database."""
        try:
            with self._engine.connect() as connection:
                connection.execute(UserEntity.__table__.insert(), [user_data])
                logger.info(f"✅ Added new user: {user_data['username']} to the database.")
        except Exception as e:
            logger.error(f"❌ Failed to add user {user_data['username']} to the database: {e}")
            raise  # Re-raise the same exception

    def add_location(self, user_name: str, location_data: dict):
        """Add a new location to the database."""
        try:
            user = self.get_user_by_username(user_name)
            with Session(self._engine) as session:
                if user is None:
                    raise ValueError(f"User '{user_name}' not found.")

                user.locations.append(LocationEntity(**location_data))
                session.commit()
                logger.info(f"✅ Added new location to the user {user_name}.")
        except Exception as e:
            logger.error(f"❌ Failed to add location to the user {user_name}: {e}")
            raise  # Re-raise the same exception

    def add_vehicle(self, user_name: str, vehicle_data: dict):
        """Add a new vehicle to the database."""
        try:
            user = self.get_user_by_username(user_name)
            with Session(self._engine) as session:
                if user is None:
                    raise ValueError(f"User '{user_name}' not found.")

                user.vehicles.append(VehicleEntity(**vehicle_data))
                session.commit()
                logger.info(f"✅ Added new vehicle to the user {user_name}.")
        except Exception as e:
            logger.error(f"❌ Failed to add vehicle to the user {user_name}: {e}")
            raise  # Re-raise the same exception

    def get_all_reservations(self):
        """Fetch all reservations from the database."""
        with Session(self._engine) as session:
            stmt = select(ReservationEntity).options(
                selectinload(ReservationEntity.user), selectinload(ReservationEntity.vehicle)
            )
            return session.execute(stmt).scalars().all()

    def get_all_reservations_by_username(self, username: str):
        """Fetch all reservations for a specific user from the database."""
        with Session(self._engine) as session:
            stmt = (
                select(ReservationEntity)
                .join(UserEntity)
                .options(
                    selectinload(ReservationEntity.user),
                    selectinload(ReservationEntity.vehicle),
                )
                .where(UserEntity.username == username)
            )
            return session.execute(stmt).scalars().all()

    def create_reservation(self, username: str, reservation: ReservationEntity) -> dict:
        """Create a reservation and return persistence details."""
        try:
            user = self.get_user_by_username(username)
            with Session(self._engine) as session:
                if user is None:
                    raise ValueError(f"User with username:'{username}' not found.")

                user_in_session = session.get(UserEntity, user.id)
                if user_in_session is None:
                    raise ValueError(f"User with username:'{username}' not found.")

                user_in_session.reservations.append(reservation)
                session.commit()
                session.refresh(reservation)
                logger.info(f"✅ Reservation created successfully for the user: {username}.")
                return {
                    "created": True,
                    "status": reservation.status.value,
                    "reservation_id": reservation.reservation_id,
                    "username": username,
                }
        except Exception as e:
            logger.error(f"❌ Failed to create reservation for the user: {username}: {e}")
            raise  # Re-raise the same exception

    def update_reservation_status(self, reservation_id: str, new_status: ReservationStatus):
        """Update the status of an existing reservation in the database."""
        try:
            with Session(self._engine) as session:
                stmt = select(ReservationEntity).where(ReservationEntity.reservation_id == reservation_id)
                reservation = session.execute(stmt).scalars().first()
                if reservation is None:
                    raise ValueError(f"Reservation with ID '{reservation_id}' not found.")

                reservation.status = new_status
                reservation.reservation_time = (
                    datetime.now()
                )  # Update reservation time to current time when status changes
                session.commit()
                logger.info(f"✅ Updated reservation {reservation_id} status to {new_status}.")
        except Exception as e:
            logger.error(f"❌ Failed to update reservation {reservation_id} status: {e}")
            raise  # Re-raise the same exception

    def execute_query(self, query: str):
        """Execute a raw SQL query against the database."""
        if any(keyword in str(query).lower() for keyword in ["delete", "update", "insert"]):
            logger.warning(f"⚠️ Attempt to execute a potentially harmful query: {query}")
            raise ValueError("Only SELECT queries are allowed.")
        try:
            with self._engine.connect() as connection:
                result = connection.execute(query)
                logger.info(f"✅ Successfully executed query: {query}")
                return result.fetchall()
        except Exception as e:
            logger.error(f"❌ Failed to execute query '{query}': {e}")
            raise  # Re-raise the same exception
