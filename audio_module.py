import numpy as np
import sounddevice as sd
import joblib
import time
import threading
import librosa
import speech_recognition as sr

# ==============================
# LOAD SCREAM MODEL
# ==============================
model = joblib.load("models/audio_classifier.pkl")

SAMPLE_RATE = 16000
DURATION    = 0.5

# ==============================
# GLOBAL FLAGS
# ==============================
scream_flag  = False
keyword_flag = False
last_detection_time = 0
DETECTION_COUNT = 0

# KEYWORDS that trigger threat
THREAT_KEYWORDS = ["help", "stop", "no", "leave me", "save me", "let go"]

# ==============================
# AUTO-DETECT MIC
# ==============================
def get_input_device():
    try:
        device = sd.default.device[0]
        if device is None or device < 0:
            for i, d in enumerate(sd.query_devices()):
                if d['max_input_channels'] > 0:
                    print(f" Using mic device {i}: {d['name']}")
                    return i
        return device
    except Exception as e:
        print(f" Could not detect mic: {e}")
        return None

MIC_DEVICE = get_input_device()

# ==============================
# FEATURE EXTRACTION
# ==============================
def extract_features(audio):
    audio = audio.flatten()
    mfcc  = librosa.feature.mfcc(y=audio, sr=SAMPLE_RATE, n_mfcc=40)
    return np.mean(mfcc.T, axis=0)

# ==============================
# SCREAM DETECTION THREAD
# ==============================
def detect_scream():
    global scream_flag, last_detection_time, DETECTION_COUNT

    print(f" Scream detection thread running (device: {MIC_DEVICE})")

    while True:
        try:
            audio = sd.rec(
                int(SAMPLE_RATE * DURATION),
                samplerate=SAMPLE_RATE,
                channels=1,
                device=MIC_DEVICE,
                blocking=True,
                dtype='float32'
            )

            volume      = np.linalg.norm(audio)
            current_time = time.time()

            # Reset flag after cooldown
            if scream_flag and (current_time - last_detection_time > 3):
                scream_flag = False
                print(" Scream flag reset")

            if volume < 0.15:
                DETECTION_COUNT = 0
                continue

            features   = extract_features(audio)
            prediction = model.predict([features])[0]
            print(f" Scream prediction: {prediction} | Volume: {round(volume, 3)}")

            if prediction == 1:
                DETECTION_COUNT += 1
            else:
                DETECTION_COUNT = 0
                scream_flag = False

            if DETECTION_COUNT >= 3 and (current_time - last_detection_time > 3):
                scream_flag         = True
                last_detection_time = current_time
                DETECTION_COUNT     = 0
                print(" SCREAM CONFIRMED")

        except Exception as e:
            print(" SCREAM THREAD ERROR:", e)
            time.sleep(1)


# ==============================
# KEYWORD DETECTION THREAD
# ==============================
def detect_keyword():
    global keyword_flag

    print(" Keyword detection thread running...")

    # Keep retrying if PyAudio not ready
    recognizer = None
    while recognizer is None:
        try:
            recognizer = sr.Recognizer()
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True
            # Test mic is accessible
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print(" Keyword mic ready")
        except Exception as e:
            print(f" Keyword mic not ready, retrying in 2s: {e}")
            recognizer = None
            time.sleep(2)

    while True:
        try:
            with sr.Microphone() as source:
                audio = recognizer.listen(source, timeout=4, phrase_time_limit=4)

            text = recognizer.recognize_google(audio).lower()
            print(f" Heard: '{text}'")

            if any(kw in text for kw in THREAT_KEYWORDS):
                keyword_flag = True
                print(f" THREAT KEYWORD DETECTED: '{text}'")
            else:
                keyword_flag = False

        except sr.WaitTimeoutError:
            pass  # silence — keep listening, don't reset flag instantly
        except sr.UnknownValueError:
            pass
        except Exception as e:
            print(" KEYWORD ERROR:", e)
            time.sleep(2)


# ==============================
# START BOTH THREADS
# ==============================
def start_audio_thread():
    print(" Starting audio threads...")

    t1 = threading.Thread(target=detect_scream)
    t1.daemon = True
    t1.start()

    t2 = threading.Thread(target=detect_keyword)
    t2.daemon = True
    t2.start()


# ==============================
# STATUS FUNCTION
# ==============================
def get_scream_status():
    #  returns True if EITHER scream OR keyword detected
    return scream_flag or keyword_flag