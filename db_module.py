from pymongo import MongoClient
from datetime import datetime
import time 
# ==============================
# CONNECT TO MONGODB
# ==============================
client = MongoClient("mongodb://localhost:27017/")
db = client["ai_safety_system"]
collection = db["threat_logs"]

# ==============================
# LOG THREAT
# ==============================
def log_threat(weapon, confidence, gesture, scream, risk):
    data = {
        "weapon": weapon,
        "confidence": confidence,
        "gesture_detected": gesture,
        "scream_detected": scream,
        "risk_score": risk,
        "timestamp": datetime.now()
    }
    collection.insert_one(data)
    print(" Threat Logged in MongoDB")

# ==============================
# STORE EVIDENCE
# ==============================
def log_evidence(file_path, risk_score):
    data = {
        "file_path": file_path,
        "risk_score": risk_score,
        "timestamp": time.time()  
    }
    db.evidence.insert_one(data)
    print(" Evidence stored in DB")

# ==============================
# STORE GUARDIAN
# ==============================
def save_guardian(guardian):
    db.guardians.insert_one(guardian)
    print(" Guardian saved to DB")

# ==============================
# NEW: LOAD ALL GUARDIANS FROM DB
# ==============================
def get_all_guardians():
    guardians = list(db.guardians.find({}, {"_id": 0}))
    print(f" Fetched {len(guardians)} guardians from DB")
    return guardians

# ==============================
# STORE GUARDIAN ACTION
# ==============================
def log_guardian_action_db(action):
    db.guardian_actions.insert_one(action)
    print(" Guardian action stored in DB")