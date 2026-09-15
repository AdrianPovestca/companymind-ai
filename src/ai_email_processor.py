"""
AI Email Processor - Mock version for demo (swap real API when ready)
"""
import sys
sys.path.insert(0, '/workspaces/companymind-ai')

import os
from dotenv import load_dotenv
load_dotenv()

from src.email_database import get_connection
import json

def get_pending_emails():
    """Get emails from DB that need processing"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, subject, sender, body FROM emails 
            WHERE status NOT IN ('processed', 'sent') AND message_type = 'email' 
            LIMIT 5
        """)
        emails = cursor.fetchall()
        conn.close()
        return [{'message_id': e[0], 'subject': e[1], 'sender': e[2], 'body': e[3]} for e in emails]
    except Exception as e:
        print(f"❌ DB error: {e}")
        return []

def process_email_mock(email):
    """Mock AI decision (simulates Claude/Groq response)"""
    # Simple heuristics for demo
    subject_lower = email['subject'].lower()
    body_lower = email['body'].lower()
    
    # Check urgency keywords
    urgent_words = ['urgent', 'asap', 'immediately', 'refund', 'broken', 'complaint']
    is_urgent = any(word in subject_lower or word in body_lower for word in urgent_words)
    
    # Check if it's a question (needs human review)
    question_words = ['where', 'when', 'why', 'how', 'what', '?']
    is_question = any(word in body_lower for word in question_words)
    
    # Simple rules
    should_reply = not is_question and not is_urgent
    
    return {
        'should_auto_reply': should_reply,
        'urgency': 'high' if is_urgent else ('medium' if is_question else 'low'),
        'reason': 'Urgent/needs investigation' if is_urgent else ('Has questions' if is_question else 'Standard response'),
        'reply_text': 'Thank you for your inquiry. We will look into this and get back to you shortly.' if should_reply else ''
    }

def update_email_status(message_id, action, decision_data):
    """Update email status in database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE emails 
            SET status = ?, decision_action = ?, decision_reason = ?, decision_urgency = ?
            WHERE message_id = ?
        """, (
            'processed',
            action,
            decision_data.get('reason', ''),
            decision_data.get('urgency', 'medium'),
            message_id
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ DB update error: {e}")
        return False

def process_all_emails():
    """Main processor"""
    print("\n" + "="*70)
    print("AI EMAIL PROCESSOR (DEMO MODE) RUNNING")
    print("="*70 + "\n")
    
    emails = get_pending_emails()
    print(f"Found {len(emails)} emails to process\n")
    
    auto_reply_count = 0
    human_review_count = 0
    
    for email in emails:
        print(f"📧 {email['subject'][:50]}")
        
        decision = process_email_mock(email)
        
        if decision.get('should_auto_reply'):
            print(f"   ✅ AUTO-REPLY (urgency: {decision['urgency']})")
            update_email_status(email['message_id'], 'auto_reply', decision)
            auto_reply_count += 1
            if decision['reply_text']:
                print(f"   💬 \"{decision['reply_text'][:60]}...\"")
        else:
            print(f"   👤 HUMAN REVIEW (urgency: {decision['urgency']})")
            update_email_status(email['message_id'], 'human_review', decision)
            human_review_count += 1
        
        print(f"   Reason: {decision['reason']}\n")
    
    print("="*70)
    print(f"✅ Processing complete!")
    print(f"   Auto-replied: {auto_reply_count}")
    print(f"   Human review: {human_review_count}")
    print("="*70)

if __name__ == '__main__':
    process_all_emails()
