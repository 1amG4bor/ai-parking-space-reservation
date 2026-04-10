"""Service for database operations, including initialization and connection management."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload

from chat_engine.core.config.config import ConfigManager
from chat_engine.core.utils.patterns import Singleton
from chat_engine.models.database import UserEntity, LocationEntity, VehicleEntity
from chat_engine.core.config.logging import logger

class DatabaseService(metaclass=Singleton):
    """
    A service class responsible for managing database connections and operations.
    """

    def __init__(self):
        cfg_manager = ConfigManager()
        self._db_url = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}".format(
            user=cfg_manager.get_config("DATABASE_USER"),
            password=cfg_manager.get_config("DATABASE_PASSWORD"),
            host=cfg_manager.get_config("DATABASE_HOST"),
            port=cfg_manager.get_config("DATABASE_PORT"),
            db=cfg_manager.get_config("DATABASE_NAME"),
        )
        # Initialize database connection here (e.g., using SQLAlchemy)
        self._engine = create_engine(self._db_url)
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the database schema and tables if they don't exist."""
        # Initialize connection and create tables if necessary
        try:
            with self._engine.connect() as connection:
                logger.info("✅ Successfully connected to the database.")
                UserEntity.metadata.create_all(self._engine)
                LocationEntity.metadata.create_all(self._engine)    
                VehicleEntity.metadata.create_all(self._engine)
                logger.info("✅ Database tables are initialized and ready.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize the database: {e}")
            raise ConnectionError(f"Failed to initialize the database: {e}")

    def get_user_by_email(self, email: str):
        """Fetch a user from the database by their email, including locations and vehicles."""
        with Session(self._engine) as session:
            stmt = (
                select(UserEntity)
                .options(
                    selectinload(UserEntity.locations),
                    selectinload(UserEntity.vehicles),
                )
                .where(UserEntity.email == email)
            )
            return session.execute(stmt).scalars().first()
    
    def get_user_by_username(self, username: str):
        """Fetch a user from the database by their username, including locations and vehicles."""
        # UserEntity.__table__.select().where(UserEntity.username == username)
        with Session(self._engine) as session:
            stmt = (
                select(UserEntity)
                .options(
                    selectinload(UserEntity.locations),
                    selectinload(UserEntity.vehicles),
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
            raise Exception(f"Failed to add user {user_data['username']} to the database: {e}")
    
    def add_location(self, user_name: str, location_data: dict):
        """Add a new location to the database."""
        try:
            with Session(self._engine) as session:
                stmt = (
                    select(UserEntity)
                    .options(
                        selectinload(UserEntity.locations),
                        selectinload(UserEntity.vehicles),
                    )
                    .where(UserEntity.username == user_name)
                )
                user = session.execute(stmt).scalars().first()
                if user is None:
                    raise ValueError(f"User '{user_name}' not found.")

                user.locations.append(LocationEntity(**location_data))
                session.commit()
                logger.info(f"✅ Added new location to the user {user_name}.")
        except Exception as e:
            logger.error(f"❌ Failed to add location to the user {user_name}: {e}")
            raise Exception(f"Failed to add location to the user {user_name}: {e}")
