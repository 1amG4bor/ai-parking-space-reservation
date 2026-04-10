"""Module for representing database entities and models."""

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column, RelationshipProperty
from datetime import datetime, timezone

from chat_engine.models.vehicle import FuelType, VehicleType


class Base(DeclarativeBase):
    """Base class for all database models."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )

    @classmethod
    def from_dict(cls, data: dict):
        """Create an instance of the model from a dictionary."""
        # Separate relationship data from plain column data
        relationship_data = {}
        column_data = {}
        
        # Get all defined relationships for this class
        mapper = cls.__mapper__
        
        for key, value in data.items():
            if key in mapper.relationships:
                rel_property: RelationshipProperty = mapper.relationships[key]
                target_class = rel_property.mapper.class_
                
                # Convert dict(s) to entity object(s)
                if isinstance(value, list):
                    relationship_data[key] = [target_class.from_dict(i) for i in value]
                elif isinstance(value, dict):
                    relationship_data[key] = target_class.from_dict(value)
            else:
                column_data[key] = value

        return cls(**column_data, **relationship_data)


class UserEntity(Base):
    """A class representing a user entity in the database."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    locations: Mapped[list["LocationEntity"]] = relationship("LocationEntity", back_populates="user", cascade="all, delete-orphan")
    vehicles: Mapped[list["VehicleEntity"]] = relationship("VehicleEntity", back_populates="user", cascade="all, delete-orphan")

class LocationEntity(Base):
    """A class representing a location entity in the database."""

    __tablename__ = "locations"

    country: Mapped[str] = mapped_column(nullable=False)
    county: Mapped[str] = mapped_column(nullable=False)
    city: Mapped[str] = mapped_column(nullable=False)
    zip_code: Mapped[str] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserEntity"] = relationship("UserEntity", back_populates="locations")

    def __repr__(self):
        return f"{self.address}, {self.city} {self.zip_code}, {self.county}, {self.country}"
        

class VehicleEntity(Base):
    """A class representing a vehicle entity in the database."""

    __tablename__ = "vehicles"

    type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False)
    model: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    license_plate: Mapped[str] = mapped_column(unique=True, nullable=False)
    fuel_type: Mapped[FuelType] = mapped_column(Enum(FuelType), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserEntity"] = relationship("UserEntity", back_populates="vehicles")
