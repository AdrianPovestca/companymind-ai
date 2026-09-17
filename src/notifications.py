import sys
sys.path.insert(0, '/workspaces/companymind-ai')

from src.gmail_email_connector import GmailEmailConnector

def send_notification(to_email, subject, message):
    """Send real notification via Gmail"""
    try:
        gmail = GmailEmailConnector(credentials_path="gmail_oauth_credentials.json")
        
        body = f"""{message}

---
PLATREMO.HUB Email Agent
Automated Alert
        """
        
        # Use Gmail API to send email
        service = gmail.service
        
        from email.mime.text import MIMEText
        import base64
        
        msg = MIMEText(body)
        msg['to'] = to_email
        msg['from'] = 'adrianpovestcagc@gmail.com'
        msg['subject'] = subject
        
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        send_message = {'raw': raw}
        
        service.users().messages().send(userId='me', body=send_message).execute()
        print(f"📬 Notification sent to {to_email}: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ Notification failed: {e}")
        return False

def check_and_notify():
    """Check for urgent emails and notify"""
    try:
        from src.email_database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM emails 
            WHERE decision_urgency = 'high' 
            AND decision_action = 'human_review'
            AND status = 'processed'
        """)
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            send_notification(
                'adrianpovestcagc@gmail.com',
                f'🚨 {count} Urgent Email(s) Waiting',
                f'{count} high-priority email(s) need human review in the queue.'
            )
            return count
        
        return 0
    except Exception as e:
        print(f"❌ Check failed: {e}")
        return 0

if __name__ == '__main__':
    check_and_notify()
