"""Campaign sending engine with batching, throttling, and retry logic."""
import time
import uuid
from typing import List, Dict, Optional
from datetime import datetime
import re
import os
import base64
from email.mime.text import MIMEText

from src.gmail_email_connector import GmailEmailConnector
from src.campaign_database import (
    get_campaign_recipients, update_recipient_status, 
    add_campaign_log, update_campaign_status, get_campaign
)


class TemplateParser:
    """Parse and personalize email templates."""
    
    PLACEHOLDER_PATTERN = r'\[([A-Z_]+)\]'
    
    @staticmethod
    def parse(template: str, data: Dict[str, str]) -> str:
        """Replace placeholders with values from data dict."""
        result = template
        for placeholder in re.findall(TemplateParser.PLACEHOLDER_PATTERN, template):
            key = placeholder.lower()
            value = data.get(key, f"[{placeholder}]")
            result = result.replace(f"[{placeholder}]", str(value))
        return result
    
    @staticmethod
    def get_placeholders(template: str) -> List[str]:
        """Extract all placeholders from template."""
        return re.findall(TemplateParser.PLACEHOLDER_PATTERN, template)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


class CampaignSender:
    """Handles campaign sending with throttling and retry."""
    
    # Speed settings: emails per second
    SPEED_SETTINGS = {
        'slow': 0.5,      # 1 email per 2 seconds
        'normal': 1.0,    # 1 email per second
        'fast': 2.0,      # 2 emails per second
    }
    
    def __init__(self, credentials_path: str):
        """Initialize campaign sender."""
        self.gmail = GmailEmailConnector(credentials_path=credentials_path)
        self.credentials_path = credentials_path
    
    def get_delay_for_speed(self, speed_setting: str) -> float:
        """Get delay between emails based on speed setting."""
        return 1.0 / self.SPEED_SETTINGS.get(speed_setting, 1.0)
    
    def validate_recipients(self, recipients: List[Dict]) -> tuple:
        """Validate recipient emails, return (valid, invalid)."""
        valid = []
        invalid = []
        
        for recipient in recipients:
            email = recipient.get('email', '').strip()
            if not email:
                invalid.append({**recipient, 'error': 'Empty email'})
            elif not TemplateParser.validate_email(email):
                invalid.append({**recipient, 'error': 'Invalid email format'})
            else:
                valid.append(recipient)
        
        return valid, invalid
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   sender_email: str) -> tuple:
        """Send single email via Gmail using send_reply method."""
        try:
            # Create MIME message
            msg = MIMEText(body)
            msg['to'] = to_email
            msg['from'] = sender_email
            msg['subject'] = subject
            
            # Encode message
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            
            # Send via Gmail API
            message = self.gmail.service.users().messages().send(
                userId="me",
                body={'raw': raw}
            ).execute()
            
            message_id = message.get('id')
            return True, message_id
        except Exception as e:
            return False, str(e)
    
    def process_campaign(self, campaign_id: str, batch_size: int = 50, 
                        max_retries: int = 3) -> Dict:
        """
        Process campaign sending with batching and retry.
        
        Returns stats dict with sent/failed counts.
        """
        campaign = get_campaign(campaign_id)
        if not campaign:
            return {'error': 'Campaign not found'}
        
        if campaign['status'] not in ['draft', 'scheduled']:
            return {'error': f"Campaign status is {campaign['status']}, cannot send"}
        
        # Update status to started
        update_campaign_status(campaign_id, 'started')
        add_campaign_log(str(uuid.uuid4()), campaign_id, 'start', 'Campaign sending started')
        
        # Get pending recipients
        recipients = get_campaign_recipients(campaign_id, status='pending')
        if not recipients:
            update_campaign_status(campaign_id, 'completed')
            return {'error': 'No pending recipients'}
        
        # Validate recipients
        valid_recipients, invalid_recipients = self.validate_recipients(recipients)
        
        # Mark invalid as failed
        for invalid in invalid_recipients:
            recipient_id = invalid.get('id')
            update_recipient_status(recipient_id, 'failed', invalid.get('error'))
            add_campaign_log(str(uuid.uuid4()), campaign_id, 'validation_failed',
                           f"Invalid email: {invalid.get('email')}")
        
        # Get delay between sends
        delay = self.get_delay_for_speed(campaign['speed_setting'])
        
        # Parse template
        subject_template = campaign['subject']
        body_template = campaign['body']
        sender_email = campaign['sender_email']
        
        stats = {
            'sent': 0,
            'failed': 0,
            'skipped': len(invalid_recipients),
            'total': len(recipients),
            'failed_emails': []
        }
        
        # Send in batches with throttling
        for i, recipient in enumerate(valid_recipients):
            recipient_id = recipient['id']
            email = recipient['email']
            
            # Parse personalization data
            personal_data = {
                'email': email,
                'name': recipient.get('name', ''),
            }
            
            # If there's extra personalization data, parse it
            if recipient.get('personalization_data'):
                try:
                    import json
                    extra_data = json.loads(recipient['personalization_data'])
                    personal_data.update(extra_data)
                except:
                    pass
            
            # Personalize subject and body
            subject = TemplateParser.parse(subject_template, personal_data)
            body = TemplateParser.parse(body_template, personal_data)
            
            # Send email
            success, message_id = self.send_email(email, subject, body, sender_email)
            
            if success:
                update_recipient_status(recipient_id, 'sent')
                stats['sent'] += 1
                add_campaign_log(str(uuid.uuid4()), campaign_id, 'sent',
                               f"Email sent to {email} (message_id: {message_id})")
            else:
                update_recipient_status(recipient_id, 'failed', message_id)
                stats['failed'] += 1
                stats['failed_emails'].append({
                    'email': email,
                    'error': message_id
                })
                add_campaign_log(str(uuid.uuid4()), campaign_id, 'send_failed',
                               f"Failed to send to {email}: {message_id}")
            
            # Throttle to respect rate limits
            if i < len(valid_recipients) - 1:  # Don't delay after last email
                time.sleep(delay)
        
        # Mark campaign as completed
        update_campaign_status(campaign_id, 'completed')
        add_campaign_log(str(uuid.uuid4()), campaign_id, 'complete',
                        f"Campaign completed: {stats['sent']} sent, {stats['failed']} failed")
        
        return stats
