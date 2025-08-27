import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Keys you want to confirm
keys_to_check = [
    "OPENAI_API_KEY",
    "FIRECRAWL_API_KEY",
    "MONGODB_URI",
    "MONGODB_DB",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_WHATSAPP_NUMBER"
]

print("\n🔍 Environment Variable Check:\n")
for key in keys_to_check:
    value = os.getenv(key)
    if value:
        # Show first 6 chars only to confirm it's loaded (hide sensitive parts)
        print(f"{key}: ✅ Loaded ({value[:6]}...{value[-4:]})")
    else:
        print(f"{key}: ❌ MISSING")

print("\n✅ Done. If any are ❌, double-check your .env file.\n")

