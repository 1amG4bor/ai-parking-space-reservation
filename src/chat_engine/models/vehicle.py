from enum import Enum
from dataclasses import dataclass

class VehicleType(Enum):
    MICRO = "Micro"
    SEDAN = "Sedan"
    COUPE = "Coupe"
    STATION_WAGON = "Station Wagon"
    SUV = "SUV"
    PICKUP = "Pickup"
    VAN = "Van"
    CAMPERVAN = "Campervan"
    LORRY = "Lorry"
    TRUCK = "Truck"
    BUS = "Bus"
    
    
class FuelType(Enum):
    PETROL = "Petrol"
    DIESEL = "Diesel"
    CNG = "CNG"
    LPG = "LPG"
    HYBRID = "Hybrid"
    ELECTRIC = "Electric"


@dataclass
class VehicleInfo:
    type: VehicleType
    model: str
    year: int
    license_plate: str
    fuel_type: FuelType