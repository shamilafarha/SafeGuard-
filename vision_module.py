import cv2
import mediapipe as mp
from ultralytics import YOLO
import threading
import time
import numpy as np
import sounddevice as sd
import librosa
import joblib
from db_module import log_threat

# =====================================================
# GLOBAL STATES (Shared Across Threads)
# =====================================================
weapon_detected = False
gesture_detected = False
scream_detected = False
weapon_label = None
weapon_conf = 0

# =====================================================
# LOAD AUDIO CLASSIFIER
# =====================================================
audio_model = joblib.load("audio_classifier.pkl")
SAMPLE_RATE = 16000
DURATION = 1

def extract_features(audio_data):
    mfccs = librosa.feature.mfcc(y=audio_data.flatten(),
                                 sr=SAMPLE_RATE,
                                 n_mfcc=13)
    return np.mean(mfccs.T, axis=0).reshape(1, -1)

def audio_monitor():
    global scream_detected
    while True:
        audio = sd.rec(int(SAMPLE_RATE * DURATION),
                       samplerate=SAMPLE_RATE,
                       channels=1,
                       blocking=True)

        features = extract_features(audio)
        prediction = audio_model.predict(features)[0]

        scream_detected = True if prediction == 1 else False

# Start audio thread
threading.Thread(target=audio_monitor, daemon=True).start()

# =====================================================
# LOAD YOLO MODEL
# =====================================================
model = YOLO("runs/detect/train/weights/best.pt")
TARGET_CLASSES = ["gun", "knife"]

# =====================================================
# MEDIAPIPE HANDS
# =====================================================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)
mp_draw = mp.solutions.drawing_utils

def detect_signal_for_help(hand_landmarks):
    lm = hand_landmarks.landmark
    thumb_folded = lm[4].y > lm[3].y
    index_folded = lm[8].y > lm[6].y
    middle_folded = lm[12].y > lm[10].y
    ring_folded = lm[16].y > lm[14].y
    pinky_folded = lm[20].y > lm[18].y
    return thumb_folded and index_folded and middle_folded and ring_folded and pinky_folded

# =====================================================
# CAMERA INITIALIZATION
# =====================================================
cap = cv2.VideoCapture(0)
last_log_time = 0
LOG_COOLDOWN = 5

print("System Running... Press Q to exit")

# =====================================================
# MAIN LOOP
# =====================================================
while True:
    success, frame = cap.read()
    if not success:
        break

    weapon_detected = False
    gesture_detected = False

    # ------------------ WEAPON DETECTION ------------------
    results = model.predict(frame, conf=0.6, verbose=False)

    for r in results:
        if r.boxes is None:
            continue

        for box in r.boxes:
            cls_id = int(box.cls[0])
            confidence = float(box.conf[0])
            label = model.names[cls_id]

            if label not in TARGET_CLASSES:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            cv2.rectangle(frame, (x1, y1), (x2, y2),
                          (0, 0, 255), 3)

            cv2.putText(frame,
                        f"{label.upper()} {confidence:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 0, 255), 2)

            weapon_detected = True
            weapon_label = label
            weapon_conf = confidence

    # ------------------ GESTURE DETECTION ------------------
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hand_results = hands.process(rgb)

    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame,
                                   hand_landmarks,
                                   mp_hands.HAND_CONNECTIONS)

            if detect_signal_for_help(hand_landmarks):
                gesture_detected = True
                cv2.putText(frame,
                            "SIGNAL FOR HELP",
                            (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 0, 255), 3)

    # ------------------ RISK ENGINE ------------------
    risk_score = 0

    if weapon_detected:
        risk_score += 60
    if gesture_detected:
        risk_score += 20
    if scream_detected:
        risk_score += 30

    color = (0, 0, 255) if risk_score >= 80 else (0, 255, 0)

    cv2.putText(frame,
                f"Risk Level: {risk_score}%",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, color, 3)

    if scream_detected:
        cv2.putText(frame,
                    "SCREAM DETECTED",
                    (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 3)

    # ------------------ LOGGING ------------------
    current_time = time.time()

    if risk_score >= 80 and current_time - last_log_time > LOG_COOLDOWN:
        log_threat(weapon_label,
                   weapon_conf,
                   gesture_detected,
                   risk_score)
        print("High Alert Logged")
        last_log_time = current_time

    cv2.imshow("AI Safety System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()