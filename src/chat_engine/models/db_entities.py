"""Module for representing USER related database entities and models."""

from datetime import datetime

from sqlalchemy import Column, Enum, ForeignKey, Table
from sqlalchemy.orm import Mapped, attributes, mapped_column, relationship

from chat_engine.models.base import Base
from chat_engine.models.enums import FuelType, PreferenceType, ReservationStatus, VehicleType

user_preference_association = Table(
    "user_preferences",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("preference_id", ForeignKey("preferences.id"), primary_key=True),
)


class UserEntity(Base):
    """Entity that represents a user in the database."""

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

    def to_dict(self):

        result = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
        }
        state = attributes.instance_state(self)
        if state.attrs.locations.loaded_value is not attributes.NO_VALUE:
            result["locations"] = [loc.to_dict() for loc in self.locations]
        if state.attrs.vehicles.loaded_value is not attributes.NO_VALUE:
            result["vehicles"] = [v.to_dict() for v in self.vehicles]
        if state.attrs.preferences.loaded_value is not attributes.NO_VALUE:
            result["preferences"] = [p.to_dict() for p in self.preferences]
        if state.attrs.reservations.loaded_value is not attributes.NO_VALUE:
            result["reservations"] = [r.to_dict() for r in self.reservations]
        return result


class LocationEntity(Base):
    """Entity that represents a location in the database. It has a many-to-one relationship with UserEntity,
    as a user can have multiple locations but each location belongs to only one user.
    """

    __tablename__ = "locations"

    country: Mapped[str] = mapped_column(nullable=False)
    county: Mapped[str] = mapped_column(nullable=False)
    city: Mapped[str] = mapped_column(nullable=False)
    zip_code: Mapped[str] = mapped_column(nullable=False)
    address: Mapped[str] = mapped_column(nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserEntity"] = relationship("UserEntity", back_populates="locations")

    def to_dict(self):

        result = {
            "id": self.id,
            "country": self.country,
            "county": self.county,
            "city": self.city,
            "zip_code": self.zip_code,
            "address": self.address,
            "user_id": self.user_id,
        }
        if attributes.instance_state(self).attrs.user.loaded_value is not attributes.NO_VALUE:
            result["user"] = {"id": self.user.id, "username": self.user.username}
        return result

    def __str__(self):
        return f"{self.address}, {self.city} {self.zip_code}, {self.county}, {self.country}"


class VehicleEntity(Base):
    """Entity that represents a vehicle in the database. It has a many-to-one relationship with UserEntity,
    as a user can have multiple vehicles but each vehicle belongs to only one user.
    """

    __tablename__ = "vehicles"

    type: Mapped[VehicleType] = mapped_column(Enum(VehicleType), nullable=False)
    model: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    license_plate: Mapped[str] = mapped_column(unique=True, nullable=False)
    fuel_type: Mapped[FuelType] = mapped_column(Enum(FuelType), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserEntity"] = relationship("UserEntity", back_populates="vehicles")

    def to_dict(self):

        result = {
            "id": self.id,
            "type": self.type.value,
            "model": self.model,
            "year": self.year,
            "license_plate": self.license_plate,
            "fuel_type": self.fuel_type.value,
            "user_id": self.user_id,
        }
        if attributes.instance_state(self).attrs.user.loaded_value is not attributes.NO_VALUE:
            result["user"] = {"id": self.user.id, "username": self.user.username}
        return result

    def __str__(self):
        return f"{self.model} - {self.license_plate} | {self.type.value} ({self.fuel_type.value})"


PREFERENCE_TYPE_ENUM = Enum(
    PreferenceType,
    name="preferencetype",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
    validate_strings=True,
)


class PreferenceEntity(Base):
    """Entity that represents a user preference in the database. It has a many-to-many relationship with UserEntity,
    as a user can have multiple preferences and multiple users can have the same preference.
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

    def to_dict(self):

        result = {
            "id": self.id,
            "category": self.category,
            "type": self.type.value,
            "description": self.description,
        }
        if attributes.instance_state(self).attrs.users.loaded_value is not attributes.NO_VALUE:
            result["users"] = [{"id": u.id, "username": u.username} for u in self.users]
        return result

    def __str__(self):
        return f"User preference of {self.category} | {self.type.value} - {self.description}"


class ReservationEntity(Base):
    """Entity that represents a reservation in the database. It has a many-to-one relationship with UserEntity,
    as a user can have multiple reservations but each reservation belongs to only one user.
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

    def __str__(self):
        template = "Reservation {} for parking lot {} from {} to {} with status {}"
        return template.format(
            self.reservation_id, self.parking_lot_id, self.start_time, self.end_time, self.status.value
        )

    def to_dict(self):
        result = {
            "reservation_id": self.reservation_id,
            "reservation_time": self.reservation_time.isoformat() if self.reservation_time else None,
            "parking_lot_id": self.parking_lot_id,
            "parking_space_category": self.parking_space_category,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status.value,
            "user_id": self.user_id,
            "vehicle_id": self.vehicle_id,
        }
        # Include relationship data only when already loaded (avoids DetachedInstanceError)

        if attributes.instance_state(self).attrs.user.loaded_value is not attributes.NO_VALUE:
            result["user"] = {
                "id": self.user.id,
                "username": self.user.username,
                "email": self.user.email,
            }
        if attributes.instance_state(self).attrs.vehicle.loaded_value is not attributes.NO_VALUE:
            result["vehicle"] = {
                "type": self.vehicle.type.value,
                "model": self.vehicle.model,
                "year": self.vehicle.year,
                "license_plate": self.vehicle.license_plate,
                "fuel_type": self.vehicle.fuel_type.value,
            }
        return result
