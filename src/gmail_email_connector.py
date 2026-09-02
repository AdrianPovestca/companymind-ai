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
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            logger.info("Loaded existing Gmail token")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logger.info("Refreshed Gmail token")
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Gmail OAuth2 authorized")
            
            with open(self.token_path, "w") as token_file:
                token_file.write(creds.to_json())
        
        self.service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail service ready")

    def fetch_unread_emails(self) -> List[Email]:
        try:
            results = self.service.users().messages().list(
                userId=self.user_id,
                q="is:unread",
                maxResults=10
            ).execute()
            messages = results.get("messages", [])
            logger.info(f"Found {len(messages)} unread emails")
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
            from_email = next((h["value"] for h in headers if h["name"] == "From"), "")
            to_email = next((h["value"] for h in headers if h["name"] == "To"), "")
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
                from_address=from_email,
                to_address=to_email,
                body=body,
                received_at=date_str,
                raw_email=json.dumps(message)
            )
            logger.info(f"Parsed Gmail message {message_id}")
            return email
        except Exception as e:
            logger.error(f"Error parsing Gmail message: {e}")
            return None

    def mark_as_read(self, message_id: str) -> None:
        try:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            logger.info(f"Marked message {message_id} as read")
        except HttpError as error:
            logger.error(f"Error marking message as read: {error}")

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
            message["In-Reply-To"] = message_id
            message["References"] = message_id
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            sent_message = self.service.users().messages().send(
                userId=self.user_id,
                body={"raw": raw_message, "threadId": thread_id}
            ).execute()
            logger.info(f"Sent reply: {sent_message['id']}")
            return sent_message["id"]
        except HttpError as error:
            logger.error(f"Error sending reply: {error}")
            return None
