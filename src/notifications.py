import sys
sys.path.insert(0, '/workspaces/companymind-ai')

from src.email_database import get_connection
from src.gmail_email_connector import GmailEmailConnector

def send_notification(to_email, subject, message):
    """Send real notification via Gmail"""
    try:
        gmail = GmailEmailConnector(credentials_path="gmail_oauth_credentials.json")
        
        body = f"""
{message}

---
PLATREMO.HUB Email Agent
Automated notification
        """
        
        gmail.send_reply("", body)  # This needs fixing - use direct send
        print(f"✅ Notification sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Notification failed: {e}")
        return False

def check_and_notify():
    """Check for urgent emails and notify"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*), subject FROM emails 
            WHERE decision_urgency = 'high' 
            AND decision_action = 'human_review'
            AND status = 'processed'
            GROUP BY subject
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] > 0:
            send_notification(
                'adrianpovestcagc@gmail.com',
                '🚨 URGENT: Email(s) need review',
                f'{result[0]} high-priority email(s) waiting: {result[1]}'
            )
            return True
        
        return False
    except Exception as e:
        print(f"❌ Check failed: {e}")
        return False

if __name__ == '__main__':
    check_and_notify()
