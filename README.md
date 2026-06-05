# SafeGuard: Edge AI-Based IoT Multi-Modal Safety and Threat Detection System

SafeGuard is an autonomous, intervention-free Edge AI framework designed to solve the fatal flaw of traditional panic buttons—the reliance on manual activation during high-stress situations. By leveraging localized edge processing, the system runs parallel visual and acoustic pipelines to detect ongoing threats in real time, calculate dynamic risk metrics, preserve bystander privacy, and automate immediate emergency notifications.

---

##  Core Features

- **Intervention-Free Monitoring:** Continuously monitors environmental data without requiring physical interactions from a victim.
- **Multi-Modal Real-Time Tracking:** Processes synchronized data streams for visual anomalies (weapons/gestures) and audible emergencies (distress phrases).
- **Privacy-Preserving Edge Processing (`utils_privacy.py`):** Ensures public compliance by real-time face tracking and applying a dynamic blurring filter, lifting obfuscation strictly upon high-risk validation to capture forensic logs.
- **Automated Emergency Alerts:** Packages localized GPS location tags, live timestamps, and snapshot evidence data to dispatch over background network workers directly to a unified Telegram guardian group.

---

##  Core Architecture & Multimodal Late Fusion

SafeGuard employs a **Multimodal Late Fusion** scheme to handle streaming variables. Instead of early feature binding, separate visual and acoustic nodes continuously stream isolated confidence probabilities to a centralized risk engine.

```text
[Webcam Stream] ──> OpenCV Frame Parser ──> Visual Threat Weight (V) ┐
                                                                      ├──> Late Fusion Engine ──> Unified Risk Score
[Microphone]   ──> Sounddevice Pipeline ──> TF Lite / Audio Phrase (A)┘
