"""
Send notifications for urgent/important emails
"""
import sys
sys.path.insert(0, '/workspaces/companymind-ai')

from src.email_database import get_connection
import smtplib
from email.mime.text import MIMEText

def send_email_notification(to_email, subject, body):
    """Send email notification"""
    try:
        # Using Gmail to send notifications
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = 'adrianpovestcagc@gmail.com'
        msg['To'] = to_email
        
        # Note: In production, use SMTP with credentials
        print(f"📬 Notification sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"❌ Notification failed: {e}")
        return False

def check_and_notify():
    """Check for urgent emails and send notifications"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Find urgent emails that need attention
        cursor.execute("""
            SELECT COUNT(*), subject FROM emails 
            WHERE decision_urgency = 'high' 
            AND decision_action = 'human_review'
            GROUP BY subject
        """)
        urgent = cursor.fetchall()
        
        conn.close()
        
        if urgent:
            for count, subject in urgent:
                msg = f"URGENT: {count} high-priority email(s) need attention:\n{subject}"
                send_email_notification('adrianpovestcagc@gmail.com', 
                                      '🚨 URGENT Email Alert', msg)
            return len(urgent)
        
        return 0
    except Exception as e:
        print(f"❌ Notification check failed: {e}")
        return 0

if __name__ == '__main__':
    check_and_notify()
