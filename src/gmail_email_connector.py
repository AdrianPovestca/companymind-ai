import base64
import logging
import os
import json
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText

from src.email_connector import EmailConnector
from src.email_models import Email

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

class GmailEmailConnector(EmailConnector):
    def __init__(self, credentials_path: str, **kwargs):
        self.credentials_path = credentials_path
        self.service = None
        self.user_id = "me"
        self.token_path = "gmail_token.json"
        logger.info(f"Gmail connector initialized")
        self._authenticate()

    def _authenticate(self) -> None:
        creds = None
        
        # Try to load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            logger.info("✅ Loaded existing Gmail token")
        
        # If no valid token, get new one
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logger.info("🔄 Refreshed Gmail token")
            else:
                # First time auth - manual flow
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                
                # Get auth URL
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                print("\n" + "="*70)
                print("🔗 GMAIL AUTHORIZATION REQUIRED")
                print("="*70)
                print(f"Copy & paste this link in your browser:\n")
                print(f"{auth_url}\n")
                print("After authorizing:")
                print("1. You'll be redirected to localhost (may show error - OK!)")
                print("2. Copy the CODE from the URL (after code=)")
                print("3. Paste it below\n")
                print("="*70)
                
                code = input("📋 Paste authorization code here: ").strip()
                
                try:
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    logger.info("✅ Gmail authorization successful")
                except Exception as e:
                    logger.error(f"Authorization failed: {e}")
                    raise
            
            # Save token for reuse
            with open(self.token_path, "w") as token_file:
                token_file.write(creds.to_json())
                logger.info(f"💾 Token saved to {self.token_path}")
        
        self.service = build("gmail", "v1", credentials=creds)
        logger.info("✅ Gmail service ready!")

    def fetch_unread_emails(self) -> List[Email]:
        try:
            results = self.service.users().messages().list(
                userId=self.user_id,
                q="is:unread",
                maxResults=10
            ).execute()
            messages = results.get("messages", [])
            logger.info(f"📧 Found {len(messages)} unread emails")
            
            emails = []
            for message in messages:
                email_obj = self._parse_gmail_message(message["id"])
                if email_obj:
                    emails.append(email_obj)
            return emails
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []

    def _parse_gmail_message(self, message_id: str) -> Optional[Email]:
        try:
            message = self.service.users().messages().get(
                userId=self.user_id,
                id=message_id,
                format="full"
            ).execute()
            
            headers = message["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "")
            recipient = next((h["value"] for h in headers if h["name"] == "To"), "")
            date_str = next((h["value"] for h in headers if h["name"] == "Date"), "")
            
            body = ""
            if "parts" in message["payload"]:
                for part in message["payload"]["parts"]:
                    if part["mimeType"] == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            body = base64.urlsafe_b64decode(data).decode("utf-8")
                            break
            else:
                data = message["payload"].get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
            
            email = Email(
                message_id=message_id,
                subject=subject,
                sender=sender,
                recipient=recipient,
                body=body,
                timestamp=date_str,
                thread_id=message.get("threadId", ""),
                attachments=[]
            )
            logger.info(f"✅ Parsed: {subject[:30]}")
            return email
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None

    def mark_as_read(self, message_id: str) -> None:
        try:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            logger.info(f"✅ Marked as read: {message_id[:20]}")
        except HttpError as error:
            logger.error(f"Error marking as read: {error}")

    def send_reply(self, message_id: str, reply_text: str) -> Optional[str]:
        try:
            original = self.service.users().messages().get(
                userId=self.user_id,
                id=message_id,
                format="full"
            ).execute()
            
            thread_id = original["threadId"]
            headers = original["payload"]["headers"]
            from_header = next((h["value"] for h in headers if h["name"] == "From"), "")
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
            
            if "<" in from_header:
                reply_to = from_header.split("<")[1].split(">")[0]
            else:
                reply_to = from_header
            
            message = MIMEText(reply_text)
            message["to"] = reply_to
            message["subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            sent = self.service.users().messages().send(
                userId=self.user_id,
                body={"raw": raw_message, "threadId": thread_id}
            ).execute()
            
            logger.info(f"✅ Sent reply: {sent['id'][:20]}")
            return sent["id"]
        except HttpError as error:
            logger.error(f"Error sending reply: {error}")
            return None
