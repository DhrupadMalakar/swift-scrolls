# gmail_sender.py
# Send email using Gmail API (OAuth) instead of SMTP.

import os.path
from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from collector_reddit import load_config

# Gmail API scope: send emails only
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def get_gmail_service():
    """
    Create or load OAuth token and return an authenticated Gmail API service.
    """
    creds = None
    token_path = "token.json"

    # Load existing token if present
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid creds, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # credentials.json must be in the project root (same folder as token.json)
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for next time
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def send_swift_scroll_via_gmail(subject: str, body: str) -> None:
    """
    Send the Swift Scroll email using the Gmail API.
    Uses recipient_email and sender_display_name from config.json.
    The sender account is the Google account you used during OAuth.
    """
    config = load_config()
    recipient = config.get("recipient_email")
    sender_name = config.get("sender_display_name", "Swift Scrolls")

    if not recipient:
        raise ValueError("recipient_email missing in config.json")

    # The actual "from" Gmail address is determined by the authenticated account.
    # We'll just use the display name here.
    msg = EmailMessage()
    msg["To"] = recipient
    msg["From"] = sender_name  # Gmail will show it as: "Name <your_gmail_here>"
    msg["Subject"] = subject
    msg.set_content(body)

    raw_message = msg.as_bytes().decode("utf-8")
    # Gmail API expects base64url-encoded message, but the client lib handles it
    from base64 import urlsafe_b64encode

    encoded_message = urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    service = get_gmail_service()
    send_result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body={"raw": encoded_message},
        )
        .execute()
    )

    print(f"Gmail API: message sent, ID: {send_result.get('id')}")
