from enum import Enum

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


class ReservationStatus(Enum):
    PENDING = "Pending"
    BOOKED = "Booked"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"

class PreferenceType(Enum):
    # By accessibility
    ACCESS_24_7 = ("Accessibility", "24/7 access", "Parking lot is accessible from 00:00 to 23:59 every day.")
    CLOSEST_TO_DESTINATION = ("Accessibility", "Closest to destination", "Parking lot is closest to the destination.")
    HANDICAP_ACCESSIBLE = ("Accessibility", "Handicap accessible", "Parking lot is accessible for handicapped individuals.")

    # By security
    CCTV_SURVEILLANCE = ("Security", "CCTV surveillance", "Parking lot is monitored by CCTV cameras.")
    GATED_ACCESS = ("Security", "Gated access", "Parking lot has gated access for security.")
    SECURITY_FEATURES = ("Security", "Security features", "Parking lot has various security features.")

    # By cost
    AUTOMATED_SYSTEM = ("Cost", "Automated system", "Parking lot has an automated system for payment and entry.")
    BUDGET_FRIENDLY = ("Cost", "Budget-friendly", "Parking lot is budget-friendly.")
    
    # By features
    COVERED_PARKING = ("Features", "Covered parking", "Parking lot has covered parking spaces to protect vehicles from weather conditions.")
    EV_CHARGING_STATION = ("Features", "EV charging station", "Parking lot has EV charging stations.")
    LARGE_VEHICLE_SPACES = ("Features", "Large vehicle spaces", "Parking lot has spaces for large vehicles.")
    LONG_TERM_PARKING = ("Features", "Long-term parking", "Parking lot is ideal for long-term stays. It is located farther from the destination but cost-effective, convenient and they are often with secure/surveillance features.")
    SHORT_TERM_PARKING = ("Features", "Short-term parking", "Parking lot ideal for quick trips, pickups. It is located near terminals. Cheap for short stays but expensive for long stays.")
    VALET_SERVICE = ("Features", "Valet service", "A convenient amenity where an attendant parks and retrieves the guest's vehicle.")

    def __new__(cls, category: str, value: str, description: str = ""):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._category = category
        obj._description = description
        return obj
    
    @property
    def category(self):
        return self._category
    
    @property
    def value(self):
        return self._value_
    
    @property
    def description(self):
        return self._description
    
    def to_dict(self):
        """Convert the PreferenceType enum member to a dictionary."""
        return {
            "category": self.category,
            "type": self.value,
            "description": self.description
        }

    def __repr__(self):
        return f"User preference, {self.category} | {self.value} - {self.description}"
