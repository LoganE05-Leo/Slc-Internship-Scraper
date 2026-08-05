"""SMTP email delivery. No-op (returns False) unless all required env vars are set."""
import os
import smtplib
from email.mime.text import MIMEText


def send_email(subject: str, body_markdown: str) -> bool:
    host = os.environ.get("SMTP_HOST")
    if not host:
        return False

    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    to_raw = os.environ.get("EMAIL_TO", "")
    recipients = [addr.strip() for addr in to_raw.split(",") if addr.strip()]

    if not (user and password and recipients):
        return False

    msg = MIMEText(body_markdown, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = ", ".join(recipients)

    with smtplib.SMTP_SSL(host, port) as server:
        server.login(user, password)
        server.sendmail(user, recipients, msg.as_string())
    return True
