"""
Email database layer.

Stores parsed emails, replies, decision metadata,
and human review information in SQLite.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from src.email_models import Email


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "emails.db"


def get_connection() -> sqlite3.Connection:
    """Create a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_email_db() -> None:
    """Create all required email tables and columns."""
    conn = get_connection()

    conn.execute(
        """
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            decision_action TEXT,
            decision_reason TEXT,
            decision_intent TEXT,
            decision_urgency TEXT,
            requires_human INTEGER DEFAULT 0,
            human_review_status TEXT,
            human_review_note TEXT,
            reviewed_at TEXT,
            message_type TEXT DEFAULT 'email'
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_email_thread_id
        ON emails(thread_id)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_email_status
        ON emails(status)
        """
    )

    conn.commit()
    conn.close()


def _ensure_column(
    conn: sqlite3.Connection,
    column_name: str,
    column_definition: str,
) -> None:
    """Add a column if it does not already exist."""
    columns = conn.execute(
        "PRAGMA table_info(emails)"
    ).fetchall()

    existing_columns = {
        column["name"]
        for column in columns
    }

    if column_name not in existing_columns:
        conn.execute(
            f"ALTER TABLE emails ADD COLUMN "
            f"{column_name} {column_definition}"
        )


def _ensure_schema() -> None:
    """
    Make sure older emails.db files receive
    all new columns introduced by the agent.
    """
    conn = get_connection()

    required_columns = {
        "decision_action": "TEXT",
        "decision_reason": "TEXT",
        "decision_intent": "TEXT",
        "decision_urgency": "TEXT",
        "requires_human": "INTEGER DEFAULT 0",
        "human_review_status": "TEXT",
        "human_review_note": "TEXT",
        "reviewed_at": "TEXT",
        "message_type": "TEXT DEFAULT 'email'",
    }

    for column_name, column_definition in required_columns.items():
        _ensure_column(
            conn,
            column_name,
            column_definition,
        )

    conn.commit()
    conn.close()


def save_email(
    email: Email,
    status: str = "new",
) -> None:
    """Save an email. Existing message IDs are ignored."""
    init_email_db()
    _ensure_schema()

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
            status,
            message_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            "email",
        ),
    )

    conn.commit()
    conn.close()


def get_email(
    message_id: str,
) -> Optional[dict]:
    """Return an email by message ID."""
    init_email_db()
    _ensure_schema()

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM emails
        WHERE message_id = ?
        """,
        (message_id,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


def update_email_status(
    message_id: str,
    status: str,
) -> None:
    """Update processing status for an email."""
    conn = get_connection()

    conn.execute(
        """
        UPDATE emails
        SET status = ?
        WHERE message_id = ?
        """,
        (
            status,
            message_id,
        ),
    )

    conn.commit()
    conn.close()


def save_decision_metadata(
    message_id: str,
    action: str,
    reason: str,
    intent: str,
    urgency: str,
    requires_human: bool,
) -> None:
    """
    Save the decision made by the agent.

    If human intervention is required,
    create a pending human review automatically.
    """
    init_email_db()
    _ensure_schema()

    conn = get_connection()

    human_review_status = (
        "pending"
        if requires_human
        else None
    )

    conn.execute(
        """
        UPDATE emails
        SET
            decision_action = ?,
            decision_reason = ?,
            decision_intent = ?,
            decision_urgency = ?,
            requires_human = ?,
            human_review_status = ?
        WHERE message_id = ?
        """,
        (
            action,
            reason,
            intent,
            urgency,
            int(requires_human),
            human_review_status,
            message_id,
        ),
    )

    conn.commit()
    conn.close()


def get_decision_metadata(
    message_id: str,
) -> Optional[dict]:
    """Return decision and human review metadata."""
    init_email_db()
    _ensure_schema()

    conn = get_connection()

    row = conn.execute(
        """
        SELECT
            message_id,
            status,
            decision_action,
            decision_reason,
            decision_intent,
            decision_urgency,
            requires_human,
            human_review_status,
            human_review_note,
            reviewed_at
        FROM emails
        WHERE message_id = ?
        """,
        (message_id,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


def review_email(
    message_id: str,
    review_status: str,
    note: str,
) -> None:
    """
    Complete or update a human review.

    Example statuses:
    - approved
    - rejected
    - resolved
    - pending
    """
    init_email_db()
    _ensure_schema()

    conn = get_connection()

    conn.execute(
        """
        UPDATE emails
        SET
            human_review_status = ?,
            human_review_note = ?,
            reviewed_at = CURRENT_TIMESTAMP
        WHERE message_id = ?
        """,
        (
            review_status,
            note,
            message_id,
        ),
    )

    conn.commit()
    conn.close()


def save_reply(
    message_id: str,
    thread_id: str,
    recipient: str,
    subject: str,
    body: str,
) -> None:
    """
    Save an outgoing reply as part of the email thread.
    """
    init_email_db()
    _ensure_schema()

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO emails (
            message_id,
            thread_id,
            sender,
            recipient,
            subject,
            body,
            timestamp,
            attachments,
            status,
            message_type
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            message_id,
            thread_id,
            "support",
            recipient,
            subject,
            body,
            "CURRENT_TIMESTAMP",
            "",
            "sent",
            "reply",
        ),
    )

    conn.commit()
    conn.close()


def get_replies_for_thread(
    thread_id: str,
) -> list[dict]:
    """Return all replies belonging to a thread."""
    init_email_db()
    _ensure_schema()

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            rowid AS reply_id,
            message_id,
            thread_id,
            recipient,
            subject,
            body,
            created_at
        FROM emails
        WHERE thread_id = ?
        AND message_type = 'reply'
        ORDER BY created_at ASC
        """,
        (thread_id,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]