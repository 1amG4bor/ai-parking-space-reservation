"""Module for representing USER related database entities and models."""

from datetime import datetime
from sqlalchemy import Enum, ForeignKey, Table, Column
from sqlalchemy.orm import relationship, Mapped, mapped_column

from chat_engine.models.base import Base
from chat_engine.models.enums import FuelType, PreferenceType, VehicleType, ReservationStatus


user_preference_association = Table(
    "user_preferences",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("preference_id", ForeignKey("preferences.id"), primary_key=True),
)


class UserEntity(Base):
    """A class representing a user entity in the database."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    locations: Mapped[list["LocationEntity"]] = relationship(
        "LocationEntity", back_populates="user", cascade="all, delete-orphan"
    )
    vehicles: Mapped[list["VehicleEntity"]] = relationship(
        "VehicleEntity", back_populates="user", cascade="all, delete-orphan"
    )
    preferences: Mapped[list["PreferenceEntity"]] = relationship(
        "PreferenceEntity",
        secondary=user_preference_association,
        back_populates="users",
    )
    reservations: Mapped[list["ReservationEntity"]] = relationship(
        "ReservationEntity", back_populates="user", cascade="all, delete-orphan"
    )


class LocationEntity(Base):
    """A class representing a location entity in the database.
    It has a many-to-one relationship with UserEntity, as a user can have multiple locations but each location belongs to only one user.
    """

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
    """A class representing a vehicle entity in the database.
    It has a many-to-one relationship with UserEntity, as a user can have multiple vehicles but each vehicle belongs to only one user.
    """

    __tablename__ = "vehicles"

    type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False)
    model: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    license_plate: Mapped[str] = mapped_column(unique=True, nullable=False)
    fuel_type: Mapped[FuelType] = mapped_column(Enum(FuelType), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserEntity"] = relationship("UserEntity", back_populates="vehicles")

    def __repr__(self):
        return f"{self.model} - {self.license_plate} | {self.type.value} ({self.fuel_type.value})"


PREFERENCE_TYPE_ENUM = Enum(
    PreferenceType,
    name="preferencetype",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
    validate_strings=True,
)


class PreferenceEntity(Base):
    """A class representing a user preference entity in the database.
    It has a many-to-many relationship with UserEntity, as a user can have multiple preferences and multiple users can have the same preference.
    """

    __tablename__ = "preferences"

    category: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[PreferenceType] = mapped_column(PREFERENCE_TYPE_ENUM, nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)

    users: Mapped[list["UserEntity"]] = relationship(
        "UserEntity",
        secondary=user_preference_association,
        back_populates="preferences",
    )

    def __repr__(self):
        return f"User preference of {self.category} | {self.type.value} - {self.description}"


class ReservationEntity(Base):
    """A class representing a reservation entity in the database.
    It has a many-to-one relationship with UserEntity, as a user can have multiple reservations but each reservation belongs to only one user.
    """

    __tablename__ = "reservations"

    reservation_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    reservation_time: Mapped[datetime] = mapped_column(nullable=True)
    parking_lot_id: Mapped[str] = mapped_column(nullable=False)
    parking_space_category: Mapped[str] = mapped_column(nullable=False)
    start_time: Mapped[datetime] = mapped_column(nullable=False)
    end_time: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(Enum(ReservationStatus), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserEntity"] = relationship("UserEntity", back_populates="reservations")

    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    vehicle: Mapped["VehicleEntity"] = relationship("VehicleEntity")

    def __repr__(self):
        return f"Reservation {self.reservation_id} for parking lot {self.parking_lot_id} from {self.start_time} to {self.end_time} with status {self.status.value}"
