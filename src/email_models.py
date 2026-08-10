"""
Data models for the AI Email Agent.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Email:
    """
    Represents a single email message.
    """

    message_id: str
    thread_id: str
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: Optional[datetime] = None
    attachments: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"Email("
            f"message_id={self.message_id!r}, "
            f"thread_id={self.thread_id!r}, "
            f"sender={self.sender!r}, "
            f"subject={self.subject!r}"
            f")"
        )