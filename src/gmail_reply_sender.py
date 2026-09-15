"""
Send Gmail replies for auto-approved emails
"""
import sys
sys.path.insert(0, '/workspaces/companymind-ai')

from src.email_database import get_connection
from src.gmail_email_connector import GmailEmailConnector

def get_emails_to_reply():
    """Get emails marked for auto_reply but not yet sent"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, thread_id, subject, sender, body FROM emails 
            WHERE decision_action = 'auto_reply' AND status = 'processed'
            LIMIT 5
        """)
        emails = cursor.fetchall()
        conn.close()
        return [{'message_id': e[0], 'thread_id': e[1], 'subject': e[2], 'sender': e[3], 'body': e[4]} for e in emails]
    except Exception as e:
        print(f"❌ DB error: {e}")
        return []

def get_reply_text(message_id):
    """Get the generated reply text from DB"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT decision_reason FROM emails WHERE message_id = ?
        """, (message_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None
    except Exception as e:
        print(f"❌ DB error: {e}")
        return None

def mark_as_sent(message_id):
    """Mark email as sent in database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE emails 
            SET status = 'sent', decision_action = 'auto_reply_sent'
            WHERE message_id = ?
        """, (message_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ DB update error: {e}")
        return False

def send_replies():
    """Main function - send pending replies"""
    print("\n" + "="*70)
    print("GMAIL REPLY SENDER")
    print("="*70 + "\n")
    
    try:
        gmail = GmailEmailConnector(credentials_path="gmail_oauth_credentials.json")
    except Exception as e:
        print(f"❌ Gmail connection error: {e}")
        return
    
    emails_to_reply = get_emails_to_reply()
    print(f"Found {len(emails_to_reply)} emails to reply to\n")
    
    sent_count = 0
    error_count = 0
    
    for email in emails_to_reply:
        print(f"📧 Replying to: {email['sender']}")
        print(f"   Subject: {email['subject'][:50]}")
        
        # In real implementation, get reply text from smart_email_agent
        # For now, use a generic reply
        reply_text = "Thank you for your inquiry. We will get back to you shortly."
        
        try:
            # Send reply via Gmail API
            sent_id = gmail.send_reply(email['message_id'], reply_text)
            
            if sent_id:
                print(f"   ✅ Sent (ID: {sent_id})")
                mark_as_sent(email['message_id'])
                sent_count += 1
            else:
                print(f"   ❌ Failed to send")
                error_count += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:60]}")
            error_count += 1
        
        print()
    
    print("="*70)
    print(f"✅ Processing complete!")
    print(f"   Sent: {sent_count}")
    print(f"   Errors: {error_count}")
    print("="*70)

if __name__ == '__main__':
    send_replies()
