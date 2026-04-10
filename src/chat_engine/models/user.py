from dataclasses import dataclass

from chat_engine.models.vehicle import VehicleInfo

@dataclass
class LocationData:
    country: str
    county: str
    city: str
    zip_code: str
    address: str


@dataclass
class UserData:
    username: str
    email: str
    password: str
    locations: list[LocationData]
    vehicles: list[VehicleInfo]