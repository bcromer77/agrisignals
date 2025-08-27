import os
from twilio.rest import Client

# Load credentials from environment variables
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
WHATSAPP_FROM = os.getenv("WHATSAPP_FROM", "whatsapp:+14155238886")

client = Client(TWILIO_SID, TWILIO_AUTH)

def send_whatsapp_alert(to_number: str, message_body: str) -> str:
    """
    Send a WhatsApp message to a subscriber.

    Args:
        to_number: Recipient's WhatsApp number (must start with whatsapp:+)
        message_body: The text body of the alert

    Returns:
        Message SID (Twilio identifier)
    """
    message = client.messages.create(
        body=message_body,
        from_=WHATSAPP_FROM,
        to=to_number,
    )
    return message.sid

