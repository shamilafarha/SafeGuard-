import os
import numpy as np
import librosa
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

DATASET_PATH = "audio_dataset"

def extract_features(file_path):
    try:
        y, sr = librosa.load(file_path, sr=16000)

        # Normalize audio
        y = y / np.max(np.abs(y))

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        return np.mean(mfcc.T, axis=0)

    except:
        return None

features = []
labels = []

for label, folder in enumerate(["normal", "scream"]):
    path = os.path.join(DATASET_PATH, folder)

    for file in os.listdir(path):
        file_path = os.path.join(path, file)

        feat = extract_features(file_path)

        if feat is not None:
            features.append(feat)
            labels.append(label)

print("Dataset loaded:", len(features))

X = np.array(features)
y = np.array(labels)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier(n_estimators=200)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print("Accuracy:", accuracy)

joblib.dump(model, "audio_classifier.pkl")
print("Model saved!")