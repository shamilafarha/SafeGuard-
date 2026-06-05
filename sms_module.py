import requests
import os

# ==============================
# TELEGRAM BOT CONFIGURATION
# ==============================
#
# SETUP STEPS:
# 1. Open Telegram → search @BotFather → send /newbot
# 2. Name it "SafeGuard AI" → copy the TOKEN given
# 3. Open your bot → send any message (e.g. "hello")
# 4. Open: https://api.telegram.org/botYOUR_TOKEN/getUpdates
# 5. Find "id" inside "chat" → that is your CHAT_ID
# 6. Paste both below
#BOT_TOKEN = "yyyyy"
#CHAT_ID   = "xxxxx"
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
# Additional chat IDs to notify (family/friends)
# They must first send a message to your bot to get their chat ID
EXTRA_CHAT_IDS = [
    "1276024693",
    "1452406313",
]
#  POLICE / EMERGENCY (SIMULATED)
POLICE_CONTACTS = [
   #"7899340002"   # Currently your ID for demo purposes
]
# ==============================
# SEND TELEGRAM MESSAGE
# ==============================
def send_telegram_message(text):
    if BOT_TOKEN == "your_bot_token_here":
        print("📱 [DEMO MODE] Telegram not configured — message:")
        print("─" * 50)
        print(text)
        print("─" * 50)
        return False

    all_chats = [CHAT_ID] + EXTRA_CHAT_IDS

    success = False
    for chat_id in all_chats:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            response = requests.post(url, data={
                "chat_id":    chat_id,
                "text":       text,
                "parse_mode": "HTML"
            }, timeout=10)

            result = response.json()
            if result.get("ok"):
                print(f" Telegram message sent to chat {chat_id}")
                success = True
            else:
                print(f" Telegram error: {result.get('description','Unknown')}")

        except Exception as e:
            print(f" Telegram failed: {e}")

    return success

# ==============================
# SEND TELEGRAM PHOTO (evidence)
# ==============================
def send_telegram_photo(photo_path, caption=""):
    if BOT_TOKEN == "your_bot_token_here":
        return

    if not os.path.exists(photo_path):
        return

    all_chats = [CHAT_ID] + EXTRA_CHAT_IDS

    for chat_id in all_chats:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(photo_path, "rb") as photo:
                response = requests.post(url, data={
                    "chat_id": chat_id,
                    "caption": caption[:1024]
                }, files={"photo": photo}, timeout=15)

            if response.json().get("ok"):
                print(f" Evidence photo sent to Telegram chat {chat_id}")
            else:
                print(f" Photo send failed: {response.json()}")

        except Exception as e:
            print(f" Photo send error: {e}")

# ==============================
# MAIN SEND FUNCTION
# (called by main.py as send_sms)
# ==============================
def send_sms(message, extra_contacts=None):
    """
    This function replaces Twilio SMS with Telegram.
    extra_contacts is ignored (Telegram uses chat IDs not phone numbers).
    """
    # Format message nicely for Telegram
    telegram_msg = (
        f" <b>SAFEGUARD AI ALERT</b>\n\n"
        f"{message}\n\n"
        f"<i>Sent by IoT Safety System</i>"
    )
    send_telegram_message(telegram_msg)
