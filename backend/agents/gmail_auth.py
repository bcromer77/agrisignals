from __future__ import print_function
import os.path
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying scopes, delete the token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    creds = None
    token_path = os.path.join("backend", "credentials", "token.json")
    secret_path = os.path.join("backend", "credentials", "gmail_client_secret.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    print("✅ Gmail authentication complete, token saved to", token_path)

if __name__ == "__main__":
    main()

