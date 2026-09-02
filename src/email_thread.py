"""
Email thread memory.

Provides access to all incoming emails and outgoing replies
belonging to the same conversation thread.
"""

from typing import Any, Dict, List

from src.email_database import get_connection


def get_thread(thread_id: str) -> List[Dict[str, Any]]:
    """
    Return all messages belonging to a thread, oldest first.

    Incoming emails and outgoing support replies are stored
    in the same emails table and are distinguished by
    message_type.
    """
    if not thread_id or not thread_id.strip():
        return []

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                message_id,
                thread_id,
                sender,
                recipient,
                subject,
                body,
                timestamp,
                attachments,
                status,
                created_at,
                message_type
            FROM emails
            WHERE thread_id = ?
            ORDER BY
                CASE
                    WHEN timestamp IS NULL OR timestamp = ''
                        THEN created_at
                    ELSE timestamp
                END ASC,
                created_at ASC,
                rowid ASC
            """,
            (thread_id,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def get_thread_context(thread_id: str) -> str:
    """
    Build readable context from the complete email thread.

    Returns an empty string when the thread does not exist.
    """
    messages = get_thread(thread_id)

    if not messages:
        return ""

    context_parts: List[str] = []

    for message in messages:
        sender = message.get("sender") or ""
        subject = message.get("subject") or ""
        body = message.get("body") or ""

        message_type = message.get("message_type")

        if message_type == "reply":
            sender_label = "support"
        else:
            sender_label = sender

        context_parts.append(
            f"From: {sender_label}\n"
            f"Subject: {subject}\n"
            f"Message: {body}"
        )

    return "\n\n".join(context_parts)