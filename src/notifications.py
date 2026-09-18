"""Send urgent email notifications via Telegram."""
import os
import requests
from src.email_database import get_connection


def send_telegram_notification(title, message):
    """Send notification via Telegram Bot."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Telegram credentials not set")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = f"<b>{title}</b>\n\n{message}"
        
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        })
        
        return response.status_code == 200
    except Exception as exc:
        print(f"❌ Telegram notification failed: {exc}")
        return False


def check_and_notify():
    """Check for urgent emails and send Telegram notifications."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT message_id, sender, subject FROM emails
        WHERE decision_urgency = 'high' AND decision_action = 'human_review'
          AND status = 'processed' AND urgent_notified_at IS NULL
        ORDER BY created_at DESC LIMIT 20
    """).fetchall()
    conn.close()
    
    sent = 0
    for message_id, sender, subject in rows:
        title = f"🚨 URGENT EMAIL"
        message = f"<b>From:</b> {sender}\n<b>Subject:</b> {subject}\n\n<i>Needs immediate attention</i>"
        
        if send_telegram_notification(title, message):
            conn = get_connection()
            conn.execute(
                "UPDATE emails SET urgent_notified_at = CURRENT_TIMESTAMP WHERE message_id = ?", 
                (message_id,)
            )
            conn.commit()
            conn.close()
            sent += 1
    
    return sent


if __name__ == "__main__":
    print(f"Urgent notifications sent: {check_and_notify()}")
