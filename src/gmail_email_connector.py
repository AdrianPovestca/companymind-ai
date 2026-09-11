"""
Gmail Email Connector.

Uses Google OAuth2 Desktop flow with a local callback server.
"""

import base64
import logging
import os
from email.mime.text import MIMEText
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

        logger.info("Gmail connector initialized")
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Gmail using the desktop OAuth flow."""
        creds = None

        # Load existing OAuth token if available.
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(
                    self.token_path,
                    SCOPES,
                )
                logger.info("Loaded existing Gmail token")
            except Exception as error:
                logger.warning(f"Could not load Gmail token: {error}")
                creds = None

        # Refresh or create credentials.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logger.info("Gmail token refreshed")
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    SCOPES,
                )

                logger.info("Starting Gmail OAuth browser flow")

                # Opens the browser automatically and uses an available
                # local port for the OAuth callback.
                creds = flow.run_local_server(port=0)

                logger.info("Gmail authorization successful")

            # Save token locally for future runs.
            with open(self.token_path, "w") as token_file:
                token_file.write(creds.to_json())

            logger.info(f"Gmail token saved to {self.token_path}")

        self.service = build(
            "gmail",
            "v1",
            credentials=creds,
        )

        logger.info("Gmail service ready")

    def fetch_unread_emails(self, limit: int = 10) -> List[Email]:
        """Fetch unread emails from Gmail."""
        try:
            results = (
                self.service.users()
                .messages()
                .list(
                    userId=self.user_id,
                    q="is:unread",
                    maxResults=limit,
                )
                .execute()
            )

            messages = results.get("messages", [])
            logger.info(f"Found {len(messages)} unread emails")

            emails = []

            for message in messages:
                email_obj = self._parse_gmail_message(message["id"])

                if email_obj:
                    emails.append(email_obj)

            return emails

        except HttpError as error:
            logger.error(f"Gmail API error while fetching emails: {error}")
            return []

    def _parse_gmail_message(
        self,
        message_id: str,
    ) -> Optional[Email]:
        """Parse a Gmail API message into the Email model."""
        try:
            message = (
                self.service.users()
                .messages()
                .get(
                    userId=self.user_id,
                    id=message_id,
                    format="full",
                )
                .execute()
            )

            headers = message["payload"].get("headers", [])

            subject = next(
                (
                    header["value"]
                    for header in headers
                    if header["name"].lower() == "subject"
                ),
                "",
            )

            sender = next(
                (
                    header["value"]
                    for header in headers
                    if header["name"].lower() == "from"
                ),
                "",
            )

            recipient = next(
                (
                    header["value"]
                    for header in headers
                    if header["name"].lower() == "to"
                ),
                "",
            )

            date_str = next(
                (
                    header["value"]
                    for header in headers
                    if header["name"].lower() == "date"
                ),
                "",
            )

            body = self._extract_body(message["payload"])

            email_obj = Email(
                message_id=message_id,
                thread_id=message.get("threadId", ""),
                sender=sender,
                recipient=recipient,
                subject=subject,
                body=body,
                timestamp=date_str,
                attachments=[],
            )

            logger.info(f"Parsed email: {subject[:50]}")

            return email_obj

        except HttpError as error:
            logger.error(f"Gmail API error while parsing message: {error}")
            return None

        except Exception as error:
            logger.error(f"Error parsing Gmail message: {error}")
            return None

    def _extract_body(self, payload) -> str:
        """Extract plain-text body from a Gmail message payload."""
        try:
            if "parts" in payload:
                for part in payload["parts"]:
                    mime_type = part.get("mimeType", "")

                    if mime_type == "text/plain":
                        data = part.get("body", {}).get("data", "")

                        if data:
                            return base64.urlsafe_b64decode(data).decode(
                                "utf-8",
                                errors="replace",
                            )

                    # Handle nested multipart messages.
                    if mime_type.startswith("multipart/"):
                        nested_body = self._extract_body(part)

                        if nested_body:
                            return nested_body

            else:
                data = payload.get("body", {}).get("data", "")

                if data:
                    return base64.urlsafe_b64decode(data).decode(
                        "utf-8",
                        errors="replace",
                    )

        except Exception as error:
            logger.warning(f"Could not extract email body: {error}")

        return ""

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a Gmail message as read."""
        try:
            (
                self.service.users()
                .messages()
                .modify(
                    userId=self.user_id,
                    id=message_id,
                    body={"removeLabelIds": ["UNREAD"]},
                )
                .execute()
            )

            logger.info(f"Marked email as read: {message_id[:20]}")

            return True

        except HttpError as error:
            logger.error(f"Error marking email as read: {error}")
            return False

    def send_reply(
        self,
        message_id: str,
        reply_text: str,
    ) -> Optional[str]:
        """Send a reply to the original Gmail thread."""
        try:
            original = (
                self.service.users()
                .messages()
                .get(
                    userId=self.user_id,
                    id=message_id,
                    format="full",
                )
                .execute()
            )

            thread_id = original.get("threadId", "")
            headers = original["payload"].get("headers", [])

            from_header = next(
                (
                    header["value"]
                    for header in headers
                    if header["name"].lower() == "from"
                ),
                "",
            )

            subject = next(
                (
                    header["value"]
                    for header in headers
                    if header["name"].lower() == "subject"
                ),
                "",
            )

            message = MIMEText(reply_text)

            message["to"] = from_header

            if subject.lower().startswith("re:"):
                message["subject"] = subject
            else:
                message["subject"] = f"Re: {subject}"

            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()

            sent = (
                self.service.users()
                .messages()
                .send(
                    userId=self.user_id,
                    body={
                        "raw": raw_message,
                        "threadId": thread_id,
                    },
                )
                .execute()
            )

            sent_id = sent.get("id")

            logger.info(f"Sent Gmail reply: {sent_id}")

            return sent_id

        except HttpError as error:
            logger.error(f"Error sending Gmail reply: {error}")
            return None

        except Exception as error:
            logger.error(f"Unexpected error sending Gmail reply: {error}")
            return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing Gmail connector...\n")

    try:
        connector = GmailEmailConnector(
            credentials_path="gmail_oauth_credentials.json"
        )

        emails = connector.fetch_unread_emails(limit=3)

        print(f"Found {len(emails)} unread emails\n")

        for email_obj in emails:
            print(f"Subject: {email_obj.subject}")
            print(f"From: {email_obj.sender}")
            print(f"To: {email_obj.recipient}")
            print(f"Thread: {email_obj.thread_id}")
            print()

        print("GMAIL CONNECTOR WORKING")

    except Exception as error:
        print(f"Gmail connector error: {error}")