import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import os
import json
import time

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="SafeGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# CUSTOM CSS
# ==============================
st.markdown("""
<style>
/* Dark theme */
[data-testid="stAppViewContainer"] {
    background: #04080f;
    color: #e8f0fe;
}
[data-testid="stSidebar"] {
    background: #080f1a;
    border-right: 1px solid #112240;
}
[data-testid="stSidebar"] * { color: #e8f0fe !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background: #0c1525;
    border: 1px solid #112240;
    border-radius: 10px;
    padding: 16px;
}
[data-testid="stMetricValue"] { color: #e63950 !important; font-size: 2rem !important; }

/* Headings */
h1, h2, h3 { color: #e8f0fe !important; }

/* Dataframe */
[data-testid="stDataFrame"] { background: #0c1525; }

/* Alert box */
.sos-box {
    background: rgba(230,57,80,0.15);
    border: 2px solid #e63950;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    animation: pulse 1s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }

/* Signal cards */
.signal-card {
    background: #0c1525;
    border: 1px solid #112240;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.signal-card.active { border-color: #e63950; background: rgba(230,57,80,0.08); }
.signal-active { color: #e63950; font-weight: bold; }
.signal-clear  { color: #00d68f; }

/* Progress bar color */
.stProgress > div > div { background: #e63950 !important; }
</style>
""", unsafe_allow_html=True)

# ==============================
# MONGODB CONNECTION
# ==============================
@st.cache_resource
def get_db():
    client = MongoClient("mongodb://localhost:27017/")
    return client["ai_safety_system"]

db = get_db()

# ==============================
# READ LIVE STATUS FROM main.py
# ==============================
def read_status():
    try:
        if os.path.exists("system_status.json"):
            with open("system_status.json") as f:
                return json.load(f)
    except:
        pass
    return {"risk": 0, "weapon": 0, "weapon_label": "none",
            "audio": 0, "gesture": 0}

# ==============================
# HELPER FUNCTIONS
# ==============================
def fmt_time(ts):
    if not ts: return "—"
    try: return datetime.fromtimestamp(float(ts)).strftime("%d %b %Y %H:%M:%S")
    except: return "—"

# ==============================
# SIDEBAR NAVIGATION
# ==============================
st.sidebar.markdown("## 🛡️ SafeGuard AI")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", [
    "🏠 Home",
    "📹 Live Monitor",
    "👥 Guardians",
    "🖼️ Evidence Vault",
    "📊 Threat History"
])
st.sidebar.markdown("---")
st.sidebar.markdown("**System Info**")
st.sidebar.markdown("This app reads live data from MongoDB")

# ══════════════════════════════
# PAGE 1 — HOME
# ══════════════════════════════
if page == "🏠 Home":
    st.markdown("# 🛡️ SafeGuard AI")
    st.markdown("### IoT-Integrated Multi-Signal Safety & Threat Detection System")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    threats  = list(db.evidence.find())
    guardians = list(db.guardians.find())
    verified = [g for g in guardians if g.get("is_verified")]
    peak     = max((e.get("risk_score", 0) or 0 for e in threats), default=0)

    col1.metric("🚨 Total Threats",   len(threats))
    col2.metric("👥 Guardians",        len(verified), "verified")
    col3.metric("📸 Evidence Files",   len(threats))
    col4.metric("⚠️ Peak Risk Score",  f"{peak}%")

    st.markdown("---")
    st.markdown("### How It Works")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 🔫 Weapon Detection")
        st.markdown("YOLOv8 dual-model system detects guns and knives in real-time camera feed with confidence scoring.")
    with c2:
        st.markdown("#### 🤚 Gesture Recognition")
        st.markdown("MediaPipe tracks 21 hand landmarks to detect the international Signal for Help gesture.")
    with c3:
        st.markdown("#### 🔊 Audio Detection")
        st.markdown("MFCC scream classifier + keyword detection for 'help', 'stop', 'no' in real time.")

    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown("#### 📍 Guardian Dispatch")
        st.markdown("Notifies verified guardians within 500m using Haversine distance formula automatically.")
    with c5:
        st.markdown("#### 🧮 Risk Scoring")
        st.markdown("Weighted formula: Risk = (0.5×W) + (0.3×S) + (0.2×G). SOS triggers at ≥ 80%.")
    with c6:
        st.markdown("#### 🔒 Privacy Module")
        st.markdown("Gaussian blur protects bystander faces. Evidence only stored on confirmed threat.")

# ══════════════════════════════
# PAGE 2 — LIVE MONITOR
# ══════════════════════════════
elif page == "📹 Live Monitor":
    st.markdown("# 📹 Live Monitor")
    st.markdown("Real-time threat detection status — auto-refreshes every 2 seconds")
    st.markdown("---")

    # Auto refresh
    placeholder = st.empty()

    with placeholder.container():
        status = read_status()
        risk   = status.get("risk", 0)

        # SOS ALERT
        if risk >= 80:
            st.markdown(f"""
            <div class="sos-box">
                <h2 style="color:#e63950;margin:0">🚨 SOS TRIGGERED</h2>
                <p style="color:#e8f0fe;margin-top:8px">Emergency alerts have been dispatched!</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")

        # Risk Score
        col1, col2 = st.columns([1, 2])
        with col1:
            color = "#e63950" if risk >= 80 else "#ffb020" if risk >= 40 else "#00d68f"
            st.markdown(f"""
            <div style="background:#0c1525;border:1px solid #112240;border-radius:12px;
              padding:28px;text-align:center;">
              <div style="font-size:64px;font-weight:800;color:{color};line-height:1;">{risk}%</div>
              <div style="color:#4a6080;font-size:13px;margin-top:8px;letter-spacing:2px;">RISK SCORE</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("#### Signal Status")

            # Weapon
            w = status.get("weapon", 0)
            wl = status.get("weapon_label", "none")
            st.markdown(f"""
            <div class="signal-card {'active' if w else ''}">
              <span>🔫 Weapon Detection</span>
              <span class="{'signal-active' if w else 'signal-clear'}">
                {'🔴 ' + wl.upper() + ' DETECTED' if w else '🟢 CLEAR'}
              </span>
            </div>""", unsafe_allow_html=True)

            # Audio
            a = status.get("audio", 0)
            st.markdown(f"""
            <div class="signal-card {'active' if a else ''}">
              <span>🔊 Audio Threat</span>
              <span class="{'signal-active' if a else 'signal-clear'}">
                {'🔴 SCREAM / HELP DETECTED' if a else '🟢 CLEAR'}
              </span>
            </div>""", unsafe_allow_html=True)

            # Gesture
            g = status.get("gesture", 0)
            st.markdown(f"""
            <div class="signal-card {'active' if g else ''}">
              <span>🤚 Help Gesture</span>
              <span class="{'signal-active' if g else 'signal-clear'}">
                {'🔴 SIGNAL FOR HELP' if g else '🟢 CLEAR'}
              </span>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Risk Level")
        st.progress(min(risk, 100) / 100)
        st.caption(f"Current risk: {risk}% — SOS triggers at 80%")

        # Recent evidence
        st.markdown("#### Recent Threat Events")
        recent = list(db.evidence.find({}, {"_id": 0}).sort("timestamp", -1).limit(5))
        if recent:
            for e in recent:
                r = e.get("risk_score", 0) or 0
                t = fmt_time(e.get("timestamp"))
                icon = "🔴" if r >= 80 else "🟡"
                st.markdown(f"{icon} `{t}` — Risk: **{r}%**")
        else:
            st.info("No threat events yet — run main.py and trigger SOS")

    # Auto refresh every 2 seconds
    time.sleep(2)
    st.rerun()

# ══════════════════════════════
# PAGE 3 — GUARDIANS
# ══════════════════════════════
elif page == "👥 Guardians":
    st.markdown("# 👥 Guardian Network")
    st.markdown("Register and manage verified guardians who respond during emergencies")
    st.markdown("---")

    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.markdown("### Register New Guardian")
        with st.form("guardian_form"):
            name   = st.text_input("Full Name", placeholder="Guardian's full name")
            phone  = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
            lat    = st.text_input("Latitude",  placeholder="e.g. 12.9789")
            lon    = st.text_input("Longitude", placeholder="e.g. 79.9593")
            gov_id = st.text_input("Government ID (optional)", placeholder="ID reference")
            submit = st.form_submit_button("✅ Register Guardian", use_container_width=True)

            if submit:
                if not all([name, phone, lat, lon]):
                    st.error("Name, phone, latitude and longitude are required.")
                else:
                    try:
                        db.guardians.insert_one({
                            "guardian_id": f"G{db.guardians.count_documents({})+1}",
                            "name": name, "phone": phone,
                            "lat": float(lat), "lon": float(lon),
                            "govt_id_path": gov_id,
                            "status": "ACTIVE",
                            "is_verified": True,
                            "face_encoding": [],
                            "registered_at": datetime.now()
                        })
                        st.success(f"✅ Guardian '{name}' registered successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.info("💡 To find your coordinates: Open Google Maps → Right click your location → Copy the numbers shown")

    with col2:
        st.markdown("### Registered Guardians")
        guardians = list(db.guardians.find({}, {"_id": 0, "face_encoding": 0}))

        if guardians:
            st.markdown(f"**{len(guardians)} total** | **{sum(1 for g in guardians if g.get('is_verified'))} verified**")
            for g in guardians:
                verified = g.get("is_verified", False)
                status   = g.get("status", "—")
                with st.container():
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.markdown(f"**{g.get('name','—')}**")
                    c2.markdown(f"`{g.get('phone','—')}`")
                    c3.markdown("✅ Verified" if verified else "⚠️ Pending")
                    st.caption(f"📍 {g.get('lat',0):.4f}, {g.get('lon',0):.4f} | Status: {status}")
                    st.markdown("---")
        else:
            st.info("No guardians registered yet")

# ══════════════════════════════
# PAGE 4 — EVIDENCE VAULT
# ══════════════════════════════
elif page == "🖼️ Evidence Vault":
    st.markdown("# 🖼️ Evidence Vault")
    st.markdown("All captured threat evidence stored with privacy protection")
    st.markdown("---")

    evidence_list = list(db.evidence.find({}, {"_id": 0}).sort("timestamp", -1))

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Files", len(evidence_list))
    col2.metric("High Risk (≥80%)", sum(1 for e in evidence_list if (e.get("risk_score",0) or 0) >= 80))
    col3.metric("Peak Risk", f"{max((e.get('risk_score',0) or 0 for e in evidence_list), default=0)}%")

    st.markdown("---")

    if not evidence_list:
        st.info("No evidence captured yet — trigger SOS in main.py to generate evidence files")
    else:
        # Show in grid of 3 columns
        cols = st.columns(3)
        for i, e in enumerate(evidence_list):
            with cols[i % 3]:
                risk = e.get("risk_score", 0) or 0
                fp   = e.get("file_path", "") or ""
                ts   = fmt_time(e.get("timestamp"))

                # Show image if file exists
                if fp and os.path.exists(fp):
                    st.image(fp, use_column_width=True)
                else:
                    st.markdown(f"""
                    <div style="background:#0c1525;border:1px solid #112240;border-radius:8px;
                      aspect-ratio:4/3;display:flex;align-items:center;justify-content:center;
                      font-size:40px;">⚠️</div>
                    """, unsafe_allow_html=True)

                color = "🔴" if risk >= 80 else "🟡"
                st.markdown(f"{color} **{risk}% Risk**")
                st.caption(ts)
                st.caption(fp.split("/")[-1].split("\\")[-1] if fp else "—")
                st.markdown("---")

# ══════════════════════════════
# PAGE 5 — THREAT HISTORY
# ══════════════════════════════
elif page == "📊 Threat History":
    st.markdown("# 📊 Threat History")
    st.markdown("Complete audit log of all detected threat events")
    st.markdown("---")

    threats = list(db.evidence.find({}, {"_id": 0}).sort("timestamp", -1))

    col1, col2, col3, col4 = st.columns(4)
    total = len(threats)
    high  = sum(1 for e in threats if (e.get("risk_score",0) or 0) >= 80)
    peak  = max((e.get("risk_score",0) or 0 for e in threats), default=0)

    col1.metric("Total Events",     total)
    col2.metric("SOS Triggered",    high)
    col3.metric("Below Threshold",  total - high)
    col4.metric("Peak Risk",        f"{peak}%")

    st.markdown("---")

    if not threats:
        st.info("No threat history yet — run main.py and trigger SOS to generate logs")
    else:
        # Chart
        import pandas as pd
        df_chart = pd.DataFrame([{
            "Time":  fmt_time(e.get("timestamp")),
            "Risk%": e.get("risk_score", 0) or 0
        } for e in reversed(threats)])

        st.markdown("#### Risk Score Over Time")
        st.line_chart(df_chart.set_index("Time")["Risk%"])

        st.markdown("---")
        st.markdown("#### All Events")

        # Table
        df = pd.DataFrame([{
            "Timestamp":   fmt_time(e.get("timestamp")),
            "Risk Score":  f"{e.get('risk_score',0) or 0}%",
            "Evidence File": (e.get("file_path","") or "").split("/")[-1].split("\\")[-1] or "—"
        } for e in threats])

        st.dataframe(df, use_container_width=True, hide_index=True)