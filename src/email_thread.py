"""
Email thread memory.

Provides access to all emails belonging to the same conversation thread.
"""

from typing import List, Dict

from src.email_database import get_connection


def get_thread(thread_id: str) -> List[Dict]:
    """Return all emails in a thread, oldest first."""
    conn = get_connection()

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
            created_at
        FROM emails
        WHERE thread_id = ?
        ORDER BY timestamp ASC, created_at ASC
        """,
        (thread_id,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]