from chat_engine.models.enums import VehicleType, FuelType, PreferenceType

test_users = [
    {
        "username": "john.doe",
        "email": "jdoe@mymail.com",
        "password": "user-pw",
        "preferences": [PreferenceType.COVERED_PARKING.to_dict(), PreferenceType.ACCESS_24_7.to_dict()],
        "locations": [
            {
                "country": "Hungary",
                "county": "Csongrád",
                "city": "Szeged",
                "zip_code": "6700",
                "address": "Széchenyi tér 1",
            },
        ],
        "vehicles": [
            {
                "type": VehicleType.SUV.name,
                "model": "Kia Sportage",
                "year": 2016,
                "license_plate": "ABCD-123",
                "fuel_type": FuelType.DIESEL.name,
            },
        ],
    },
    {
        "username": "user2",
        "email": "user2@mymail.com",
        "password": "user-pw",
        "preferences": [],
        "locations": [
            {
                "country": "Hungary",
                "county": "Pest",
                "city": "Budapest",
                "zip_code": "1051",
                "address": "Kossuth Lajos sgt. 5",
            },
        ],
        "vehicles": [
            {
                "type": VehicleType.SEDAN.name,
                "model": "Toyota Corolla",
                "year": 2018,
                "license_plate": "EFGH-456",
                "fuel_type": FuelType.PETROL.name,
            },
        ],
    },
    {
        "username": "user3",
        "email": "user3@mymail.com",
        "password": "user-pw",
        "preferences": [PreferenceType.EV_CHARGING_STATION.to_dict()],
        "locations": [
            {
                "country": "Hungary",
                "county": "Győr-Moson-Sopron",
                "city": "Győr",
                "zip_code": "9021",
                "address": "Rákóczi Ferenc utca 10",
            },
        ],
        "vehicles": [
            {
                "type": VehicleType.COUPE.name,
                "model": "Audi TT Coupe",
                "year": 2020,
                "license_plate": "IJKL-789",
                "fuel_type": FuelType.ELECTRIC.name,
            },
        ],
    },
    {
        "username": "user4",
        "email": "user4@mymail.com",
        "password": "user-pw",
        "preferences": [PreferenceType.LARGE_VEHICLE_SPACES.to_dict()],
        "locations": [
            {
                "country": "Hungary",
                "county": "Borsod-Abaúj-Zemplén",
                "city": "Miskolc",
                "zip_code": "3525",
                "address": "Szent István tér 2",
            },
        ],
        "vehicles": [
            {
                "type": VehicleType.VAN.name,
                "model": "Ford Transit",
                "year": 2015,
                "license_plate": "MNOP-321",
                "fuel_type": FuelType.DIESEL.name,
            },
        ],
    },
    {
        "username": "user5",
        "email": "user5@mymail.com",
        "password": "user-pw",
        "preferences": [PreferenceType.LARGE_VEHICLE_SPACES.to_dict()],
        "locations": [
            {
                "country": "Hungary",
                "county": "Baranya",
                "city": "Pécs",
                "zip_code": "7621",
                "address": "Király utca 15",
            },
        ],
        "vehicles": [
            {
                "type": VehicleType.TRUCK.name,
                "model": "Mercedes-Benz Actros",
                "year": 2019,
                "license_plate": "QRST-654",
                "fuel_type": FuelType.DIESEL.name,
            },
        ],
    },
]
