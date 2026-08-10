"""
Email database layer.

Stores parsed emails and their processing status in SQLite.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from src.email_models import Email

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "emails.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_email_db() -> None:
    """Create the email table if it does not exist."""
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            message_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            attachments TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_email_thread_id
        ON emails(thread_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_email_status
        ON emails(status)
    """)

    conn.commit()
    conn.close()


def save_email(email: Email, status: str = "new") -> None:
    """Save an email. Existing message IDs are ignored."""
    conn = get_connection()

    conn.execute(
        """
        INSERT OR IGNORE INTO emails (
            message_id,
            thread_id,
            sender,
            recipient,
            subject,
            body,
            timestamp,
            attachments,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email.message_id,
            email.thread_id,
            email.sender,
            email.recipient,
            email.subject,
            email.body,
            email.timestamp,
            ",".join(email.attachments),
            status,
        ),
    )

    conn.commit()
    conn.close()


def get_email(message_id: str) -> Optional[dict]:
    """Return an email by message ID."""
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM emails WHERE message_id = ?",
        (message_id,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


def update_email_status(message_id: str, status: str) -> None:
    """Update processing status for an email."""
    conn = get_connection()

    conn.execute(
        """
        UPDATE emails
        SET status = ?
        WHERE message_id = ?
        """,
        (status, message_id),
    )

    conn.commit()
    conn.close()