import os
from twilio.rest import Client

sid = os.environ["TWILIO_SID"]
auth = os.environ["TWILIO_AUTH"]
from_number = os.environ["WHATSAPP_FROM"]

# 👇 replace with your verified WhatsApp number in the sandbox
to_number = "whatsapp:+353868203061"  

client = Client(sid, auth)

message = client.messages.create(
    body="🚜 AgriSignals test WhatsApp alert: market moving soon!",
    from_=from_number,
    to=to_number,
)

print("Message SID:", message.sid)

