from chat_engine.models.vehicle import VehicleType, FuelType

test_users = [
    {
        "username": "user1",
        "email": "user1@mymail.com",
        "password": "user-pw",
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
                "type": VehicleType.SUV.value.upper(),
                "model": "Kia Sportage",
                "year": 2016,
                "license_plate": "ABCD-123",
                "fuel_type": FuelType.DIESEL.value.upper(),
            },
        ],
    },
    {
        "username": "user2",
        "email": "user2@mymail.com",
        "password": "user-pw",
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
                "type": VehicleType.SEDAN.value.upper(),
                "model": "Toyota Corolla",
                "year": 2018,
                "license_plate": "EFGH-456",
                "fuel_type": FuelType.PETROL.value.upper(),
            },
        ],
    },
    {
        "username": "user3",
        "email": "user3@mymail.com",
        "password": "user-pw",
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
                "type": VehicleType.COUPE.value.upper(),
                "model": "Audi TT Coupe",
                "year": 2020,
                "license_plate": "IJKL-789",
                "fuel_type": FuelType.ELECTRIC.value.upper(),
            },
        ],
    },
    {
        "username": "user4",
        "email": "user4@mymail.com",
        "password": "user-pw",
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
                "type": VehicleType.VAN.value.upper(),
                "model": "Ford Transit",
                "year": 2015,
                "license_plate": "MNOP-321",
                "fuel_type": FuelType.DIESEL.value.upper(),
            },
        ],
    },
    {
        "username": "user5",
        "email": "user5@mymail.com",
        "password": "user-pw",
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
                "type": VehicleType.TRUCK.value.upper(),
                "model": "Mercedes-Benz Actros",
                "year": 2019,
                "license_plate": "QRST-654",
                "fuel_type": FuelType.DIESEL.value.upper(),
            },
        ],
    },
]
