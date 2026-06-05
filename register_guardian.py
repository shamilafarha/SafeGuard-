from pymongo import MongoClient
import math

# ==============================
# CONNECT TO MONGODB
# ==============================
client = MongoClient("mongodb://localhost:27017/")
db = client["ai_safety_system"]

# ==============================
# YOUR CURRENT LOCATION
# ==============================
#  Replace these with your actual coordinates
# To find your coordinates: https://maps.google.com → right click → "What's here?"
USER_LAT = 12.9249  # example: Chennai area
USER_LON = 80.1000  # example: Chennai area

# ==============================
# REGISTER A TEST GUARDIAN
# ==============================
# Place guardian at SAME coordinates as user → guaranteed within 500m
guardian = {
    "guardian_id": "G_TEST_001",
    "name": "Test Guardian",
    "phone": "+918075122506",
    "lat": USER_LAT,            # same location as user = 0m distance
    "lon": USER_LON,
    "status": "ACTIVE",
    "is_verified": True,        #  pre-verified for testing
    "govt_id_path": "test",
    "face_encoding": []
}

# Check if already exists
existing = db.guardians.find_one({"guardian_id": "G_TEST_001"})
if existing:
    db.guardians.delete_one({"guardian_id": "G_TEST_001"})
    print(" Removed old test guardian")

db.guardians.insert_one(guardian)
print(f" Test guardian registered!")
print(f"   Name    : {guardian['name']}")
print(f"   Phone   : {guardian['phone']}")
print(f"   Location: {guardian['lat']}, {guardian['lon']}")
print(f"   Verified: {guardian['is_verified']}")
print(f"   Status  : {guardian['status']}")
print()
print(" Now run main.py — guardian will be found within 500m!")

# Verify it's in DB
count = db.guardians.count_documents({"is_verified": True, "status": "ACTIVE"})
print(f" Total verified active guardians in DB: {count}")