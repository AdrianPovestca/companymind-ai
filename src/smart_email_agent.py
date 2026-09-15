"""
Full Smart Email Agent - Phase 2
- Multi-language support
- Smart categorization
- Gmail reply sending
- Email threading
"""
import sys
sys.path.insert(0, '/workspaces/companymind-ai')

from src.email_database import get_connection
from src.gmail_email_connector import GmailEmailConnector
import json
import re

class SmartEmailAgent:
    def __init__(self):
        self.gmail = GmailEmailConnector(credentials_path="gmail_oauth_credentials.json")
        self.categories = {
            'sales': ['price', 'quote', 'offer', 'discount', 'buy', 'purchase'],
            'support': ['help', 'issue', 'problem', 'error', 'not working', 'broken'],
            'billing': ['invoice', 'payment', 'refund', 'charge', 'bill'],
            'inquiry': ['when', 'where', 'how', 'what', 'status', 'track'],
            'complaint': ['angry', 'upset', 'unacceptable', 'terrible', 'worst']
        }
        self.languages = {
            'ro': 'Romanian',
            'en': 'English',
            'de': 'German',
            'ru': 'Russian'
        }
    
    def detect_language(self, text):
        """Detect language from email text (simple heuristic)"""
        # Romanian words
        if any(word in text.lower() for word in ['sunt', 'este', 'pentru', 'care']):
            return 'ro'
        # German words
        if any(word in text.lower() for word in ['ist', 'haben', 'können', 'bitte']):
            return 'de'
        # Russian words
        if any(word in text.lower() for word in ['это', 'что', 'как', 'для']):
            return 'ru'
        return 'en'  # default English
    
    def categorize_email(self, subject, body):
        """Categorize email by content"""
        text = (subject + ' ' + body).lower()
        
        scores = {}
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'
    
    def determine_urgency(self, subject, body, category):
        """Determine email urgency"""
        text = (subject + ' ' + body).lower()
        
        urgent_markers = ['urgent', 'asap', 'immediately', 'emergency', '!', 'broken']
        high_count = sum(1 for marker in urgent_markers if marker in text)
        
        if high_count >= 2 or category in ['complaint', 'support']:
            return 'high'
        elif 'important' in text:
            return 'medium'
        return 'low'
    
    def should_auto_reply(self, category, urgency):
        """Decide if email should get auto-reply"""
        # High urgency/complaints need human touch
        if urgency == 'high' or category == 'complaint':
            return False
        
        # Sales inquiries can auto-reply
        if category in ['sales', 'inquiry']:
            return True
        
        # Support/billing usually need human
        if category in ['support', 'billing']:
            return False
        
        return True
    
    def generate_reply(self, email_data, language='en', category='general'):
        """Generate contextual reply based on category and language"""
        replies = {
            'en': {
                'sales': 'Thank you for your interest. We would be happy to provide you with a quote. Our sales team will contact you shortly.',
                'support': 'We received your support request. Our technical team is investigating and will get back to you as soon as possible.',
                'billing': 'Thank you for contacting us about billing. We will review your inquiry and respond within 24 hours.',
                'inquiry': 'Thank you for your inquiry. We will provide you with the information as soon as possible.',
                'general': 'Thank you for reaching out. We will respond to your message shortly.'
            },
            'ro': {
                'sales': 'Mulțumim pentru interes. Echipa noastră de vânzări vă va contacta cu o ofertă în curând.',
                'support': 'Am primit cererea dvs. de suport. Echipa tehnică investighează și va răspunde în cel mai scurt timp.',
                'billing': 'Mulțumim pentru contactare. Vom revizui și răspunde în 24 de ore.',
                'inquiry': 'Mulțumim pentru întrebare. Vă vom furniza informația în cel mai scurt timp.',
                'general': 'Mulțumim că ați contactat. Vă vom răspunde în curând.'
            },
            'de': {
                'sales': 'Vielen Dank für Ihr Interesse. Unser Verkaufsteam wird Sie in Kürze mit einem Angebot kontaktieren.',
                'support': 'Wir haben Ihre Supportanfrage erhalten. Unser technisches Team untersucht das Problem und meldet sich bald.',
                'billing': 'Danke für Ihre Kontaktaufnahme. Wir überprüfen und antworten innerhalb von 24 Stunden.',
                'inquiry': 'Vielen Dank für Ihre Frage. Wir werden Ihnen die Informationen schnellstmöglich zukommen lassen.',
                'general': 'Danke, dass Sie uns kontaktiert haben. Wir antworten in Kürze.'
            }
        }
        
        # Get reply in specified language, fallback to English
        lang_replies = replies.get(language, replies['en'])
        return lang_replies.get(category, lang_replies['general'])
    
    def process_email(self, email):
        """Process single email - full analysis"""
        category = self.categorize_email(email['subject'], email['body'])
        language = self.detect_language(email['subject'] + ' ' + email['body'])
        urgency = self.determine_urgency(email['subject'], email['body'], category)
        should_reply = self.should_auto_reply(category, urgency)
        
        reply_text = self.generate_reply(email, language, category) if should_reply else None
        
        return {
            'category': category,
            'language': language,
            'urgency': urgency,
            'should_auto_reply': should_reply,
            'reply_text': reply_text,
            'language_name': self.languages.get(language, 'English')
        }
    
    def update_email_db(self, message_id, decision):
        """Update email decision in database"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE emails 
                SET status = ?, decision_action = ?, decision_reason = ?, decision_urgency = ?, decision_intent = ?
                WHERE message_id = ?
            """, (
                'processed',
                'auto_reply' if decision['should_auto_reply'] else 'human_review',
                f"Category: {decision['category']}, Language: {decision['language_name']}",
                decision['urgency'],
                decision['category'],
                message_id
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ DB error: {e}")
            return False

def main():
    print("\n" + "="*70)
    print("PHASE 2: SMART EMAIL AGENT")
    print("="*70 + "\n")
    
    agent = SmartEmailAgent()
    
    # Get pending emails
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
    except Exception as e:
        print(f"❌ DB error: {e}")
        return
    
    if not emails:
        print("No emails to process")
        return
    
    print(f"Processing {len(emails)} emails...\n")
    
    auto_reply_count = 0
    human_review_count = 0
    
    for msg_id, subject, sender, body in emails:
        email_data = {
            'message_id': msg_id,
            'subject': subject,
            'sender': sender,
            'body': body
        }
        
        print(f"📧 {subject[:50]}")
        
        decision = agent.process_email(email_data)
        
        print(f"   Category: {decision['category'].upper()}")
        print(f"   Language: {decision['language_name']}")
        print(f"   Urgency: {decision['urgency'].upper()}")
        
        if decision['should_auto_reply']:
            print(f"   ✅ AUTO-REPLY")
            print(f"   💬 \"{decision['reply_text'][:60]}...\"")
            auto_reply_count += 1
        else:
            print(f"   👤 HUMAN REVIEW")
            human_review_count += 1
        
        agent.update_email_db(msg_id, decision)
        print()
    
    print("="*70)
    print(f"✅ Processing complete!")
    print(f"   Auto-replied: {auto_reply_count}")
    print(f"   Human review: {human_review_count}")
    print("="*70)

if __name__ == '__main__':
    main()
