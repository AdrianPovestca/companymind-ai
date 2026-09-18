"""Send one notification for each new urgent email awaiting review."""
import os
from email.mime.text import MIMEText
import base64

from src.email_database import get_connection
from src.gmail_email_connector import GmailEmailConnector


def send_notification(to_email, subject, message):
    try:
        gmail = GmailEmailConnector(credentials_path="gmail_oauth_credentials.json")
        msg = MIMEText(f"{message}\n\n---\nPLATREMO.HUB Email Agent")
        msg["to"] = to_email
        msg["from"] = os.environ.get("ALERT_EMAIL", "adrianpovestcagc@gmail.com")
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        gmail.service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception as exc:
        print(f"❌ Notification failed: {exc}")
        return False


def check_and_notify():
    conn = get_connection()
    rows = conn.execute("""
        SELECT message_id, sender, subject FROM emails
        WHERE decision_urgency = 'high' AND decision_action = 'human_review'
          AND status = 'processed' AND urgent_notified_at IS NULL
        ORDER BY created_at DESC LIMIT 20
    """).fetchall()
    conn.close()
    sent = 0
    destination = os.environ.get("ALERT_EMAIL", "adrianpovestcagc@gmail.com")
    for message_id, sender, subject in rows:
        if send_notification(destination, f"🚨 URGENT: {subject}", f"From: {sender}\nHigh-priority email needs immediate attention."):
            conn = get_connection()
            conn.execute("UPDATE emails SET urgent_notified_at = CURRENT_TIMESTAMP WHERE message_id = ?", (message_id,))
            conn.commit(); conn.close()
            sent += 1
    return sent


if __name__ == "__main__":
    print(f"Urgent notifications sent: {check_and_notify()}")
