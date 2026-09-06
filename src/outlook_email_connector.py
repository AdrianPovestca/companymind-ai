import logging
import requests
from typing import List, Optional
from email.mime.text import MIMEText
import base64

from src.email_connector import EmailConnector
from src.email_models import Email

logger = logging.getLogger(__name__)

class OutlookEmailConnector(EmailConnector):
    """Microsoft Outlook via Graph API"""
    
    def __init__(self, access_token: str, **kwargs):
        """
        Args:
            access_token: Microsoft Graph API access token
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://graph.microsoft.com/v1.0/me"
        logger.info("✅ Outlook connector initialized")
    
    def fetch_unread_emails(self) -> List[Email]:
        """Fetch unread emails from Outlook"""
        try:
            url = f"{self.base_url}/mailFolders/inbox/messages?$filter=isRead eq false&$top=10"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"❌ Graph API error: {response.status_code}")
                return []
            
            messages = response.json().get("value", [])
            emails = []
            
            for msg in messages:
                email_obj = self._parse_email(msg)
                if email_obj:
                    emails.append(email_obj)
            
            logger.info(f"📧 Found {len(emails)} unread Outlook emails")
            return emails
        except Exception as e:
            logger.error(f"❌ Error fetching emails: {e}")
            return []
    
    def _parse_email(self, msg: dict) -> Optional[Email]:
        """Parse Graph API
cat >> src/email_provider_registry.py << 'EOF'

from src.outlook_email_connector import OutlookEmailConnector
