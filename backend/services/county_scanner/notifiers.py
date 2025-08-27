# backend/services/county_scanner/notifiers.py
import os
import requests
from twilio.rest import Client

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
WHATSAPP_FROM = os.getenv("WHATSAPP_FROM")
WHATSAPP_TO = os.getenv("WHATSAPP_TO")  # your sandbox-joined number

def notify_slack(message: str):
    if not SLACK_WEBHOOK_URL:
        return
    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=5)
        print(f"🔔 Sent to Slack: {message}")
    except Exception as e:
        print("Slack error:", e)

def notify_whatsapp(message: str):
    if not (TWILIO_SID and TWILIO_AUTH and WHATSAPP_FROM and WHATSAPP_TO):
        return
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        msg = client.messages.create(
            body=message,
            from_=WHATSAPP_FROM,
            to=WHATSAPP_TO,
        )
        print(f"📲 WhatsApp SID {msg.sid}")
    except Exception as e:
        print("WhatsApp error:", e)

def alert_all(message: str):
    notify_slack(message)
    notify_whatsapp(message)

