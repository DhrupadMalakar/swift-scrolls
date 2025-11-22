from __future__ import print_function
import os
import json
from email.message import EmailMessage
from base64 import urlsafe_b64encode

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Gmail API scope: allow sending email
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def build_html_email(body: str) -> str:
    """
    Wrap the plain-text Swift Scroll in a styled HTML layout
    with a bright, Gen-Z but professional look.
    Works well on desktop + mobile + Gmail dark mode.
    """
    import html

    # Escape any accidental HTML and convert line breaks to <br>
    safe = html.escape(body).replace("\n", "<br>\n")

    return f"""\
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Swift Scrolls · 13th Disciple</title>
    <link href="https://fonts.googleapis.com/css2?family=Mulish:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
      body {{
        margin: 0;
        padding: 0;
        background: #f5f3ff;
        font-family: 'Mulish', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #111827;
      }}
      .wrapper {{
        max-width: 720px;
        margin: 0 auto;
        padding: 24px 16px 40px;
      }}
      .headline {{
        font-size: 12px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: #6b21a8;
        margin-bottom: 8px;
      }}
      .card {{
        background: #ffffff;
        border-radius: 20px;
        padding: 24px 22px 28px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 18px 40px rgba(15,23,42,0.08);
      }}
      .title-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
      }}
      .title-row h1 {{
        font-size: 20px;
        margin: 0;
        font-weight: 700;
        color: #111827;
      }}
      .pill {{
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 999px;
        background: #f5f3ff;
        border: 1px solid #e9d5ff;
        color: #6d28d9;
        font-weight: 600;
        white-space: nowrap;
      }}
      .body-text {{
        margin-top: 12px;
        font-size: 14px;
        line-height: 1.7;
        color: #111827;
      }}
      .body-text b {{
        font-weight: 700;
      }}
      .divider {{
        margin: 18px 0;
        height: 1px;
        background: linear-gradient(90deg, #e9d5ff, #fecaca);
        border-radius: 999px;
      }}
      .footer {{
        margin-top: 18px;
        font-size: 11px;
        color: #6b7280;
        text-align: center;
      }}
      .footer strong {{
        color: #4b5563;
      }}
      @media (max-width: 480px) {{
        .card {{
          padding: 20px 16px 24px;
          border-radius: 18px;
        }}
        .title-row h1 {{
          font-size: 18px;
        }}
        .body-text {{
          font-size: 13px;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="wrapper">
      <div class="headline">THE 13TH DISCIPLE · SWIFT SCROLLS</div>
      <div class="card">
        <div class="title-row">
          <h1>Weekly Swift Scroll</h1>
          <div class="pill">Sunday · 13:13</div>
        </div>
        <div class="divider"></div>
        <div class="body-text">
          {safe}
        </div>
      </div>
      <div class="footer">
        Sent automatically by <strong>The 13th Disciple – Swift Scrolls</strong> · coded with love 🕯💜
      </div>
    </div>
  </body>
</html>"""


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_gmail_service():
    """
    Build a Gmail API service.

    Two modes:
    1) LOCAL MODE (your Mac):
       - Uses credentials.json + token.json via InstalledAppFlow
    2) CI / GITHUB ACTIONS MODE:
       - Uses environment variables:
         GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
    """
    # CI / GitHub Actions mode: use explicit env variables
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

    if client_id and client_secret and refresh_token:
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
        service = build("gmail", "v1", credentials=creds)
        return service

    # Local dev mode: use credentials.json + OAuth browser flow
    creds = None
    token_path = "token.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def send_swift_scroll_via_gmail(subject: str, body: str) -> None:
    """
    Send the Swift Scroll email using the Gmail API.

    - Uses recipient_email and sender_display_name from config.json.
    - Sender account is the Google account authorised via OAuth.
    - Sends both:
      - Plain text (fallback)
      - HTML (styled) version.
    """
    config = load_config()
    recipient = config.get("recipient_email")
    sender_name = config.get("sender_display_name", "Swift Scrolls")

    if not recipient:
        raise ValueError("recipient_email missing in config.json")

    msg = EmailMessage()
    msg["To"] = recipient
    msg["From"] = sender_name  # Gmail shows: "Name <your_gmail>"
    msg["Subject"] = subject

    # Plain text fallback (very simple)
    msg.set_content(body)

    # HTML version – professional, readable on all clients
    html_body = build_html_email(body)
    msg.add_alternative(html_body, subtype="html")

    encoded_message = urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    service = get_gmail_service()
    send_result = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": encoded_message})
        .execute()
    )
    print(f"Gmail API: message sent, ID: {send_result.get('id')}")
