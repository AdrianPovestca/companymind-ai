"""Send Gmail replies for emails approved for automatic reply."""
import os
import sys

from src.email_database import get_connection, init_email_db
from src.gmail_email_connector import GmailEmailConnector


def get_emails_to_reply():
    init_email_db()
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT message_id, thread_id, subject, sender, body
        FROM emails
        WHERE decision_action = 'auto_reply' AND status = 'processed'
          AND message_type = 'email'
        LIMIT 5
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_as_sent(message_id):
    conn = get_connection()
    conn.execute(
        """
        UPDATE emails
        SET status = 'sent', decision_action = 'auto_reply_sent'
        WHERE message_id = ?
        """,
        (message_id,),
    )
    conn.commit()
    conn.close()


def send_replies():
    """Send replies without making a failed Gmail connection crash the pipeline."""
    init_email_db()
    emails_to_reply = get_emails_to_reply()
    if not emails_to_reply:
        print("No automatic replies pending.")
        return 0

    # ✅ FIX: Pe Render, secret files sunt în /etc/secrets/
    credentials_path = "/etc/secrets/gmail_oauth_credentials.json"
    
    # Check dacă fișierul există
    if not os.path.exists(credentials_path):
        print(f"ERROR: Credentials file not found at {credentials_path}", file=sys.stderr)
        return 1
    
    try:
        gmail = GmailEmailConnector(credentials_path=credentials_path)
    except Exception as exc:
        print(f"Gmail reply sender skipped: {exc}", file=sys.stderr)
        return 1

    sent_count = 0
    for email in emails_to_reply:
        reply_text = "Thank you for your inquiry. We will get back to you shortly."
        try:
            sent_id = gmail.send_reply(email["message_id"], reply_text)
            if sent_id:
                mark_as_sent(email["message_id"])
                sent_count += 1
                print(f"Reply sent to {email['sender']}: {sent_id}")
            else:
                print(f"Reply was not sent for {email['message_id']}", file=sys.stderr)
        except Exception as exc:
            print(f"Reply error for {email['message_id']}: {exc}", file=sys.stderr)

    print(f"Automatic replies sent: {sent_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(send_replies())
