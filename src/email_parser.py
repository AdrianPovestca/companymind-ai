"""
Email parser for the AI Email Agent.

Converts raw email data into the standard Email model used
throughout the application.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.email_models import Email


def parse_email(data: Dict[str, Any]) -> Email:
    """
    Convert raw email data into an Email object.

    Expected fields:
        message_id
        thread_id
        sender
        recipient
        subject
        body

    Optional fields:
        timestamp
        attachments
    """

    required_fields = [
        "message_id",
        "thread_id",
        "sender",
        "recipient",
        "subject",
        "body",
    ]

    missing_fields = [
        field for field in required_fields
        if not data.get(field)
    ]

    if missing_fields:
        raise ValueError(
            f"Missing required email fields: {', '.join(missing_fields)}"
        )

    timestamp = data.get("timestamp")

    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise ValueError(
                f"Invalid timestamp format: {timestamp}"
            ) from exc

    if timestamp is not None and not isinstance(timestamp, datetime):
        raise ValueError("timestamp must be a datetime or ISO formatted string")

    attachments: Optional[List[str]] = data.get("attachments")

    if attachments is None:
        attachments = []

    if not isinstance(attachments, list):
        raise ValueError("attachments must be a list")

    return Email(
        message_id=str(data["message_id"]),
        thread_id=str(data["thread_id"]),
        sender=str(data["sender"]),
        recipient=str(data["recipient"]),
        subject=str(data["subject"]),
        body=str(data["body"]),
        timestamp=timestamp,
        attachments=attachments,
    )