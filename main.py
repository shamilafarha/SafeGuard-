import cv2
import mediapipe as mp
from ultralytics import YOLO
from sms_module import send_sms, send_telegram_photo
from audio_module import start_audio_thread, get_scream_status
from location_module import get_location
from guardian_module import find_nearby_guardians
from db_module import log_evidence
import os
import time
import json

# ==============================
# FACE BLUR PERSISTENCE (STABILIZATION)
# ==============================
last_known_faces = []
face_last_seen = 0
FACE_TIMEOUT = 1.0  # Keep blurred for 1s if detector flickers

# ==============================
# SIGNAL PERSISTENCE (3 SECOND WINDOW)
# ==============================
signal_timeout = 3
weapon_time = 0
gesture_time = 0
scream_time = 0

# ==============================
# SOS COOLDOWN
# ==============================
SOS_COOLDOWN = 30
last_sos_time = 0

# ==============================
# FACE DETECTION
# ==============================
face_cascade = cv2.CascadeClassifier("models/haarcascade_frontalface_default.xml")

# ==============================
# LOAD YOLO MODELS (DUAL)
# ==============================
custom_model = YOLO("runs/detect/train2/weights/best.pt")
coco_model   = YOLO("models/yolov8n.pt")
COCO_WEAPON_CLASSES = {43: "knife", 76: "knife"}
CONF_THRESHOLD      = 0.15
COCO_CONF_THRESHOLD = 0.35

# ==============================
# MEDIAPIPE HANDS
# ==============================
mp_hands = mp.solutions.hands
hands    = mp_hands.Hands(min_detection_confidence=0.6, min_tracking_confidence=0.6)
mp_draw  = mp.solutions.drawing_utils


def detect_signal_for_help(hand_landmarks):
    lm = hand_landmarks.landmark
    index_folded  = lm[8].y  > lm[6].y
    middle_folded = lm[12].y > lm[10].y
    ring_folded   = lm[16].y > lm[14].y
    thumb_tucked  = abs(lm[4].x - lm[5].x) < 0.1
    return index_folded and middle_folded and ring_folded and thumb_tucked


def write_status(risk_percent, weapon, scream, gesture, weapon_label="none"):
    try:
        with open("system_status.json", "w") as f:
            json.dump({
                "risk": risk_percent,
                "weapon": weapon,
                "weapon_label": weapon_label,
                "audio": scream,
                "gesture": gesture
            }, f)
    except:
        pass


# ==============================
# FIX: SMART CAMERA DETECTION
# Tries multiple backends and indexes
# so it works on any Windows laptop
# ==============================
def open_camera():
    """
    Try every combination of index + backend until one opens AND reads a frame.
    Returns the working VideoCapture object, or None if nothing works.
    """
    # Backend priority list for Windows
    backends = [
        ("DSHOW",   cv2.CAP_DSHOW),    # DirectShow  — most reliable on Windows
        ("MSMF",    cv2.CAP_MSMF),     # Media Foundation — Windows built-in
        ("ANY",     cv2.CAP_ANY),       # Let OpenCV choose
    ]

    for idx in range(5):                # Try camera indexes 0 – 4
        for bname, backend in backends:
            try:
                cap = cv2.VideoCapture(idx, backend)
                if cap.isOpened():
                    # Do a real read test — isOpened() alone is NOT reliable
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"✅ Camera opened — index {idx}, backend {bname}")
                        # Set resolution for consistency
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        return cap
                    else:
                        cap.release()
                        print(f"   Index {idx} / {bname}: opened but read failed — skipping")
                else:
                    print(f"   Index {idx} / {bname}: could not open")
            except Exception as e:
                print(f"   Index {idx} / {bname}: exception — {e}")

    return None   # Nothing worked


# ==============================
# INITIALIZE SYSTEM
# ==============================
start_audio_thread()

print("🔍 Searching for camera...")
cap = open_camera()

if cap is None:
    print("\n❌ No working camera found.")
    print("   Possible fixes:")
    print("   1. Allow camera access in Windows Settings → Privacy → Camera")
    print("   2. Close any other app using the camera (Zoom, Teams, etc.)")
    print("   3. Unplug and replug an external webcam")
    print("   4. Try running: pip install opencv-python --upgrade")
    exit()

print("🛡️  System Guarding... Press Q to exit\n")

# ==============================
# MAIN PROCESSING LOOP
# ==============================
while True:
    ret, frame = cap.read()

    # ── FIX: if read fails, try to recover instead of crashing ──
    if not ret or frame is None:
        print("⚠️  Frame read failed — attempting recovery...")
        time.sleep(0.1)
        # Try to re-read up to 5 times before giving up
        recovered = False
        for _ in range(5):
            ret, frame = cap.read()
            if ret and frame is not None:
                recovered = True
                break
            time.sleep(0.1)
        if not recovered:
            print("❌ Camera lost. Exiting.")
            break

    now = time.time()

    # ── Reset detection flags based on persistence window ──
    weapon_detected  = 1 if (now - weapon_time)  < signal_timeout else 0
    gesture_detected = 1 if (now - gesture_time) < signal_timeout else 0
    scream_detected  = 1 if (now - scream_time)  < signal_timeout else 0
    weapon_label     = "none"

    # ── 1. STABILIZED FACE DETECTION ──
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    current_faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(current_faces) > 0:
        last_known_faces = current_faces
        face_last_seen   = now

    # Persistence: keep last known faces for FACE_TIMEOUT seconds
    faces_to_process = last_known_faces if (now - face_last_seen) < FACE_TIMEOUT else []

    # ── 2. DUAL-PATH WEAPON DETECTION ──
    # Custom model (guns / knives)
    for r in custom_model(frame, conf=CONF_THRESHOLD, verbose=False):
        for box in r.boxes:
            label = custom_model.names[int(box.cls[0])]
            if label in ("gun", "knife"):
                weapon_detected = 1
                weapon_time     = now
                weapon_label    = label
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(frame, f"{label} {float(box.conf[0]):.2f}",
                            (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # COCO fallback (knife class 43, scissors class 76)
    for r in coco_model(frame, conf=COCO_CONF_THRESHOLD, verbose=False):
        for box in r.boxes:
            cls = int(box.cls[0])
            if cls in COCO_WEAPON_CLASSES:
                weapon_detected = 1
                weapon_time     = now
                weapon_label    = COCO_WEAPON_CLASSES[cls]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                cv2.putText(frame, f"knife(coco) {float(box.conf[0]):.2f}",
                            (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

    # ── 3. GESTURE DETECTION ──
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)
    if res.multi_hand_landmarks:
        for hl in res.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hl, mp_hands.HAND_CONNECTIONS)
            if detect_signal_for_help(hl):
                gesture_detected = 1
                gesture_time     = now
                cv2.putText(frame, "HELP GESTURE!", (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    # ── 4. AUDIO DETECTION ──
    if get_scream_status():
        scream_detected = 1
        scream_time     = now

    # ── 5. WEIGHTED RISK ENGINE (LATE-FUSION) ──
    risk_score   = (0.5 * weapon_detected) + (0.3 * scream_detected) + (0.2 * gesture_detected)
    risk_percent = int(risk_score * 100)
    write_status(risk_percent, weapon_detected, scream_detected, gesture_detected, weapon_label)

    # ── 6. AUTONOMOUS EMERGENCY RESPONSE ──
    color = (0, 255, 0)   # green = safe
    if risk_score >= 0.8:
        color = (0, 0, 255)   # red = threat
        if now - last_sos_time >= SOS_COOLDOWN:
            last_sos_time = now
            lat, lon      = get_location()

            # Send Telegram text alert
            send_sms(
                f"🚨 ALERT! Risk: {risk_percent}%\n"
                f"📍 Location: https://maps.google.com/?q={lat},{lon}",
                find_nearby_guardians(lat, lon)
            )

            # Save evidence photo
            fname = f"evidence/threat_{int(now)}.jpg"
            os.makedirs("evidence", exist_ok=True)
            cv2.imwrite(fname, frame)
            log_evidence(fname, risk_percent)

            # Send evidence photo to Telegram
            send_telegram_photo(fname, f"🚨 Critical Threat! Risk: {risk_percent}%")
            print(f"🚨 SOS triggered! Risk: {risk_percent}% | Evidence: {fname}")

    # ── 7. ETHICAL PRIVACY MODULE (FACE BLURRING) ──
    for (x, y, w, h) in faces_to_process:
        # Bounds check — prevents crash at frame edges
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(frame.shape[1], x + w)
        y2 = min(frame.shape[0], y + h)
        face_roi = frame[y1:y2, x1:x2]

        if face_roi.size == 0:
            continue   # skip empty ROI

        if risk_score < 0.8:
            # Privacy mode — blur bystander faces
            frame[y1:y2, x1:x2] = cv2.GaussianBlur(face_roi, (99, 99), 30)
        else:
            # Threat confirmed — show face for evidence
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # ── 8. REAL-TIME UI DISPLAY ──
    # Risk score bar
    cv2.putText(frame, f"Risk: {risk_percent}%", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

    # Signal flags
    cv2.putText(frame, f"W:{weapon_detected} S:{scream_detected} G:{gesture_detected}",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # SOS cooldown countdown
    if risk_score >= 0.8:
        remaining = int(SOS_COOLDOWN - (now - last_sos_time))
        if remaining > 0:
            cv2.putText(frame, f"Next SOS in: {remaining}s", (20, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

    cv2.imshow("SafeGuard AI Safety System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ── CLEANUP ──
cap.release()
cv2.destroyAllWindows()
print("✅ SafeGuard shut down cleanly.")