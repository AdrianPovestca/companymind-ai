"""
Continuous scheduler - runs email pipeline every 5 minutes
"""
import sys
sys.path.insert(0, '/workspaces/companymind-ai')

import schedule
import time
import subprocess
from datetime import datetime
from src.notifications import check_and_notify
from src.urgent_handler import handle_urgent_emails

def run_full_pipeline():
    """Run complete email processing pipeline"""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*70}")
    print(f"[{now}] RUNNING EMAIL PIPELINE")
    print(f"{'='*70}\n")
    
    # 1. Fetch emails from Gmail
    print("Step 1: Fetching emails from Gmail...")
    subprocess.run(['python', '-m', 'src.gmail_email_connector'], 
                   capture_output=True)
    
    # 2. Analyze and decide
    print("Step 2: Analyzing emails...")
    subprocess.run(['python', 'src/smart_email_agent.py'], 
                   capture_output=True)
    
    # 3. Handle urgent emails (send preliminary reply)
    print("Step 3: Handling urgent emails...")
    handle_urgent_emails()
    
    # 4. Send standard auto-replies
    print("Step 4: Sending auto-replies...")
    subprocess.run(['python', 'src/gmail_reply_sender.py'], 
                   capture_output=True)
    
    # 5. Check and notify
    print("Step 5: Checking for notifications...")
    urgent_count = check_and_notify()
    
    print(f"\n[{now}] Pipeline complete! {urgent_count} urgent(s)")
    print(f"{'='*70}\n")

# Run every 5 minutes
schedule.every(5).minutes.do(run_full_pipeline)

# Also run once on startup
run_full_pipeline()

print("✅ Email Agent Scheduler Started!")
print("📧 Running every 5 minutes...")
print("Press Ctrl+C to stop\n")

while True:
    schedule.run_pending()
    time.sleep(60)
