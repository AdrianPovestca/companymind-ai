import sys
sys.path.insert(0, '/workspaces/companymind-ai')

from src.email_database import get_connection
from src.gmail_email_connector import GmailEmailConnector

def handle_urgent_emails():
    """Send preliminary reply to urgent emails before human review"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, subject, sender FROM emails 
            WHERE decision_urgency = 'high' AND decision_action = 'human_review'
            AND status = 'processed'
            LIMIT 5
        """)
        emails = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"❌ DB error: {e}")
        return 0
    
    if not emails:
        return 0
    
    print(f"\n📌 Handling {len(emails)} urgent emails...\n")
    
    gmail = GmailEmailConnector(credentials_path="gmail_oauth_credentials.json")
    sent_count = 0
    
    # SEND NOTIFICATION FOR EACH URGENT EMAIL
    from src.notifications import send_notification
    
    for msg_id, subject, sender in emails:
        # Send notification FIRST
        send_notification(
            'adrianpovestcagc@gmail.com',
            f'🚨 URGENT: {subject}',
            f'From: {sender}\n\nHigh-priority email needs immediate attention!'
        )
        
        urgent_reply = """Thank you for contacting us about this urgent matter.

We understand this requires immediate attention and have escalated your case to our team. 
Someone will respond within 1 hour with a full solution.

Best regards,
Email Agent
"""
        
        print(f"📧 Urgent reply to: {sender}")
        print(f"   Subject: {subject[:50]}")
        
        try:
            sent_id = gmail.send_reply(msg_id, urgent_reply)
            if sent_id:
                print(f"   ✅ Preliminary reply sent (ID: {sent_id})")
                
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE emails 
                    SET decision_action = 'urgent_preliminary_reply'
                    WHERE message_id = ?
                """, (msg_id,))
                conn.commit()
                conn.close()
                sent_count += 1
            else:
                print(f"   ❌ Failed to send")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:60]}")
        
        print()
    
    return sent_count

if __name__ == '__main__':
    handle_urgent_emails()
