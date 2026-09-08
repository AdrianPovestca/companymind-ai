"""
Real Yahoo email test
Tests connector with actual Yahoo email
"""

from src.yahoo_email_connector import YahooEmailConnector
from src.email_agent import process_unread_emails

# You'll need:
# YAHOO_EMAIL = your.email@yahoo.com
# YAHOO_APP_PASSWORD = generated in Yahoo account settings

YAHOO_EMAIL = input("Yahoo email: ")
YAHOO_APP_PASSWORD = input("Yahoo app password: ")

try:
    # Connect to real Yahoo
    connector = YahooEmailConnector(
        email=YAHOO_EMAIL,
        app_password=YAHOO_APP_PASSWORD
    )
    
    # Fetch real unread emails
    emails = connector.fetch_unread_emails()
    
    print(f"\n✅ Connected! Found {len(emails)} unread emails")
    
    for email in emails:
        print(f"\n📧 {email.subject}")
        print(f"From: {email.sender}")
        print(f"Body: {email.body[:100]}...")
    
    # Process with agent
    results = process_unread_emails(connector)
    
    print(f"\n✅ Processed {len(results)} emails")
    for r in results:
        print(f"  - {r['email'].subject}: {r['action']}")
        if r.get('reply'):
            print(f"    Reply: {r['reply'][:50]}...")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
