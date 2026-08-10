"""
Email connector for the AI Email Agent.

Defines the interface used by the email agent to receive emails.
The connector is intentionally separated from the agent logic so that
different email providers can be supported later.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

from src.email_models import Email


logger = logging.getLogger(__name__)


class EmailConnector(ABC):
    """
    Base interface for email providers.
    """

    @abstractmethod
    def fetch_unread_emails(self) -> List[Email]:
        """
        Return unread emails available for processing.
        """
        raise NotImplementedError

    @abstractmethod
    def mark_as_read(self, message_id: str) -> None:
        """
        Mark an email as read.
        """
        raise NotImplementedError


class MockEmailConnector(EmailConnector):
    """
    Temporary connector used for local development and testing.

    This allows us to build and test the email agent before connecting
    a real Gmail account.
    """

    def __init__(self, emails: List[Email] | None = None):
        self._emails = emails or []
        self._read_message_ids: set[str] = set()

    def fetch_unread_emails(self) -> List[Email]:
        """
        Return emails that have not been marked as read.
        """
        unread_emails = [
            email
            for email in self._emails
            if email.message_id not in self._read_message_ids
        ]

        logger.info(
            "Fetched %d unread email(s)",
            len(unread_emails),
        )

        return unread_emails

    def mark_as_read(self, message_id: str) -> None:
        """
        Mark a specific email as read.
        """
        self._read_message_ids.add(message_id)

        logger.info(
            "Marked email %s as read",
            message_id,
        )