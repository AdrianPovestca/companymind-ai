import imaplib
import smtplib
import logging
from typing import List, Optional
from email.mime.text import MIMEText
from email.parser import Parser

from src.email_connector import EmailConnector
from src.email_models import Email

logger = logging.getLogger(__name__)

class YahooEmailConnector(EmailConnector):
    """Yahoo Mail via IMAP/SMTP"""
    
    def __init__(self, email: str, app_password: str, **kwargs):
        """
        Args:
            email: Yahoo email address
            app_password: Yahoo app-specific password (not regular password)
        """
        self.email = email
        self.app_password = app_password
        self.imap_conn = None
        self.smtp_conn = None
        self._connect()
        logger.info(f"✅ Yahoo connector initialized for {email}")
    
    def _connect(self):
        """Connect to Yahoo IMAP"""
        try:
            self.imap_conn = imaplib.IMAP4_SSL("imap.mail.yahoo.com", 993)
            self.imap_conn.login(self.email, self.app_password)
            self.imap_conn.select("INBOX")
            logger.info("✅ Connected to Yahoo IMAP")
        except Exception as e:
            logger.error(f"❌ Yahoo IMAP connection failed: {e}")
            raise
    
    def fetch_unread_emails(self) -> List[Email]:
        """Fetch unread emails from Yahoo"""
        try:
            _, msg_nums = self.imap_conn.search(None, "UNSEEN")
            emails = []
            
            for msg_num in msg_nums[0].split():
                _, msg_data = self.imap_conn.fetch(msg_num, "(RFC822)")
                email_obj = self._parse_email(msg_data[0][1], msg_num.decode())
                if email_obj:
                    emails.append(email_obj)
            
            logger.info(f"📧 Found {len(emails)} unread Yahoo emails")
            return emails
        except Exception as e:
            logger.error(f"❌ Error fetching emails: {e}")
            return []
    
    def _parse_email(self, raw_email: bytes, msg_id: str) -> Optional[Email]:
        """Parse raw email to Email object"""
        try:
            parser = Parser()
            msg = parser.parsestr(raw_email.decode("utf-8", errors="ignore"))
            
            subject = msg.get("Subject", "")
            sender = msg.get("From", "")
            recipient = msg.get("To", "")
            date = msg.get("Date", "")
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            
            email = Email(
                message_id=msg_id,
                subject=subject,
                sender=sender,
                recipient=recipient,
                body=body,
                timestamp=date,
                thread_id=msg_id,
                attachments=[]
            )
            logger.info(f"✅ Parsed: {subject[:30]}")
            return email
        except Exception as e:
            logger.error(f"❌ Error parsing email: {e}")
            return None
    
    def mark_as_read(self, message_id: str) -> None:
        """Mark email as read"""
        try:
            self.imap_conn.store(message_id, "+FLAGS", "\\Seen")
            logger.info(f"✅ Marked as read: {message_id}")
        except Exception as e:
            logger.error(f"❌ Error marking as read: {e}")
    
    def send_reply(self, message_id: str, reply_text: str) -> Optional[str]:
        """Send reply via SMTP"""
        try:
            smtp = smtplib.SMTP("smtp.mail.yahoo.com", 587)
            smtp.starttls()
            smtp.login(self.email, self.app_password)
            
            msg = MIMEText(reply_text)
            msg["Subject"] = f"Re: Email"
            msg["From"] = self.email
            msg["To"] = self.email
            
            smtp.send_message(msg)
            smtp.quit()
            
            logger.info(f"✅ Sent reply")
            return message_id
        except Exception as e:
            logger.error(f"❌ Error sending reply: {e}")
            return None
