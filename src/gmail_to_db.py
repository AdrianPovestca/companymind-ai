"""
Save Gmail emails to emails.db
"""
import sys
sys.path.insert(0, '/workspaces/companymind-ai')

from src.email_database import get_connection
from datetime import datetime
import uuid

def save_email_to_db(email_data):
    """Save Gmail email to database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        message_id = email_data.get('message_id', str(uuid.uuid4()))
        thread_id = email_data.get('thread_id', message_id)
        timestamp = email_data.get('timestamp', datetime.now().isoformat())
        
        cursor.execute("""
            INSERT OR IGNORE INTO emails (
                message_id, thread_id, sender, recipient, subject, body,
                timestamp, attachments, status, created_at, message_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            thread_id,
            email_data.get('sender', 'Unknown'),
            email_data.get('recipient', 'Unknown'),
            email_data.get('subject', 'No subject'),
            email_data.get('body', ''),
            timestamp,
            '[]',
            'new',
            datetime.now().isoformat(),
            'email'
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Saved to DB: {email_data.get('subject', 'No subject')}")
        return True
        
    except Exception as e:
        print(f"❌ DB error: {str(e)}")
        return False
