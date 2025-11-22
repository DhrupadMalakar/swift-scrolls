# emailer.py
# Sends the Swift Scroll email using Gmail SMTP.

import os
import ssl
import smtplib
from email.message import EmailMessage
from typing import Tuple

from dotenv import load_dotenv
from collector_reddit import load_config  # reuse same config loader


def get_smtp_settings() -> Tuple[str, int, str, str]:
    """
    Load SMTP settings from .env.
    """
    load_dotenv()
    server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")

    if not username or not password:
        raise ValueError("SMTP_USERNAME or SMTP_PASSWORD missing in .env")

    return server, port, username, password


def send_swift_scroll_email(subject: str, body: str) -> None:
    """
    Send a Swift Scroll email using config.json for sender/recipient and SMTP settings from .env.
    """
    config = load_config()
    recipient = config.get("recipient_email")
    sender_email = config.get("sender_email")
    sender_name = config.get("sender_display_name", "Swift Scrolls")

    if not recipient or not sender_email:
        raise ValueError("recipient_email or sender_email missing in config.json")

    server, port, username, password = get_smtp_settings()

    msg = EmailMessage()
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP(server, port) as smtp:
        smtp.starttls(context=context)
        smtp.login(username, password)
        smtp.send_message(msg)
