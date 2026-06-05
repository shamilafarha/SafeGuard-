from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["ai_safety_system"]

# Show all current guardians first
print(" Current guardians in DB:")
for g in db.guardians.find({}, {"_id": 0}):
    print(f"  → {g.get('name')} | lat: {g.get('lat')} | lon: {g.get('lon')} | verified: {g.get('is_verified')}")

print()

# Delete ALL guardians
deleted = db.guardians.delete_many({})
print(f" Deleted {deleted.deleted_count} guardian(s)")

# Insert ONE correct guardian
guardian = {
    "guardian_id": "G001",
    "name": "Test Guardian",
    "phone": "+91XXXXXXXXXX",
    "lat": 12.978988870583095,
    "lon": 79.95933015744542,
    "status": "ACTIVE",
    "is_verified": True,
    "govt_id_path": "test",
    "face_encoding": []
}
db.guardians.insert_one(guardian)
print(" New guardian inserted!")

# Verify
print()
print(" Updated guardians in DB:")
for g in db.guardians.find({}, {"_id": 0}):
    print(f"  → {g.get('name')} | lat: {g.get('lat')} | lon: {g.get('lon')} | verified: {g.get('is_verified')}")

print()
print(" Done! Now run main.py and trigger SOS — distance will be 0.0m!")
