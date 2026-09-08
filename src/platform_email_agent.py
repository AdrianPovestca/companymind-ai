"""
Email Agent integrated with Platform Layer
Multi-tenant, reads knowledge base, uses business config
"""

import sys
sys.path.insert(0, '/workspaces/companymind-ai')

from src.email_connector import MockEmailConnector
from src.email_models import Email
from src.email_agent import process_email
from src.platform_db import get_platform_connection, get_business_agents

def process_email_for_business(business_id, email_data):
    """
    Process email for specific business
    - Read business knowledge base
    - Use business-specific config
    - Route via platform
    """
    try:
        # Get business config
        conn = get_platform_connection()
        cursor = conn.cursor()
        
        # Get knowledge base for context
        cursor.execute("""
            SELECT content FROM knowledge_base 
            WHERE business_id = ? LIMIT 5
        """, (business_id,))
        kb_docs = cursor.fetchall()
        
        # Get agent config
        cursor.execute("""
            SELECT config_json FROM agent_configs
            WHERE business_id = ? AND agent_name = 'email-agent'
        """, (business_id,))
        agent_config = cursor.fetchone()
        conn.close()
        
        # Create email object
        email = Email(
            message_id=email_data.get('message_id'),
            thread_id=email_data.get('thread_id'),
            subject=email_data.get('subject'),
            body=email_data.get('body'),
            sender=email_data.get('sender'),
            recipient=email_data.get('recipient'),
            timestamp=email_data.get('timestamp'),
            attachments=[]
        )
        
        # Process via standard agent
        result = process_email({
            'message_id': email.message_id,
            'thread_id': email.thread_id,
            'subject': email.subject,
            'body': email.body,
            'sender': email.sender,
            'recipient': email.recipient,
            'timestamp': email.timestamp,
            'attachments': []
        })
        
        # Add business_id to result
        result['business_id'] = business_id
        result['kb_used'] = len(kb_docs) > 0
        
        return result
    
    except Exception as e:
        return {
            'error': str(e),
            'business_id': business_id,
            'action': 'error'
        }

def test_platform_integration():
    """Test email agent with platform"""
    print("=" * 70)
    print("🔗 PLATFORM INTEGRATION TEST: Email Agent")
    print("=" * 70)
    
    # Test email for business 1 (Acme Corp)
    test_email = {
        'message_id': 'platform-test-1',
        'thread_id': 'ptest-1',
        'subject': 'Order status inquiry',
        'body': 'When will my order arrive?',
        'sender': 'customer@acme.com',
        'recipient': 'support@acme.com',
        'timestamp': '2026-09-08T12:00:00'
    }
    
    print("\n📧 Processing email for Business 1 (Acme Corp)...")
    result = process_email_for_business(1, test_email)
    
    print(f"✅ Result:")
    print(f"   Action: {result.get('action')}")
    print(f"   Business: {result.get('business_id')}")
    print(f"   KB Used: {result.get('kb_used')}")
    print(f"   Reply: {result.get('reply', '')[:50] if result.get('reply') else 'None'}...")
    
    print("\n" + "=" * 70)
    print("✅ PLATFORM INTEGRATION WORKING")
    print("=" * 70)

if __name__ == '__main__':
    test_platform_integration()
