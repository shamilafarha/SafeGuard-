import math
from db_module import save_guardian, log_guardian_action_db, get_all_guardians

# ==============================
# LOAD GUARDIANS FROM DB ON STARTUP
# ==============================
try:
    guardians = get_all_guardians()
    print(f" Loaded {len(guardians)} guardians from DB")
except Exception as e:
    print(f" Could not load guardians from DB: {e}")
    guardians = []


# -----------------------------
# REGISTER GUARDIAN
# -----------------------------
def register_guardian(name, phone, lat, lon, govt_id_path, face_encoding):
    guardian = {
        "guardian_id": f"G{len(guardians)+1}",
        "name": name,
        "phone": phone,
        "lat": lat,
        "lon": lon,
        "status": "ACTIVE",
        "is_verified": False,
        "govt_id_path": govt_id_path,
        "face_encoding": face_encoding
    }

    guardians.append(guardian)
    save_guardian(guardian)
    print(f" Guardian Registered: {name}")


# -----------------------------
# VERIFY GUARDIAN
# -----------------------------
def verify_guardian(guardian_id):
    for g in guardians:
        if g["guardian_id"] == guardian_id:
            g["is_verified"] = True
            print(f"✔ Guardian Verified: {g['name']}")


# -----------------------------
# HAVERSINE DISTANCE (metres)
# -----------------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    """
     FIX: Use Haversine formula to get actual distance in metres.
    Old Euclidean formula gave wrong results for geo-coordinates.
    """
    R = 6371000  # Earth radius in metres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # returns distance in metres


# -----------------------------
# FIND VERIFIED NEARBY GUARDIANS
# -----------------------------
def find_nearby_guardians(user_lat, user_lon, radius_metres=500):
    """
    ✅ FIX: Now filters by actual 500-metre radius using Haversine.
    Also returns phone numbers list for SMS dispatch.
    """
    nearby = []

    for g in guardians:
        if not g.get("is_verified") or g.get("status") != "ACTIVE":
            continue

        dist = calculate_distance(user_lat, user_lon, g["lat"], g["lon"])
        print(f" Guardian {g['name']} distance: {dist:.1f}m")

        if dist <= radius_metres:
            nearby.append(g["phone"])  # return phone numbers for SMS
            print(f"✅ Nearby guardian found: {g['name']} ({dist:.1f}m)")

    if not nearby:
        print(" No verified guardians found within 500m")

    return nearby


# -----------------------------
# LOG GUARDIAN ACTION
# -----------------------------
def log_guardian_action(guardian_id, event_id, action_type):
    action = {
        "guardian_id": guardian_id,
        "event_id": event_id,
        "action_type": action_type
    }
    log_guardian_action_db(action)
    print(f" Action logged: {guardian_id} → {action_type}")