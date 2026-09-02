"""
Email database layer.

Stores incoming emails, outgoing replies, decision metadata,
and human review information in SQLite.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from src.email_models import Email


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "emails.db"


def get_connection() -> sqlite3.Connection:
    """Create a SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_email_db() -> None:
    """Create the email database schema if it does not exist."""
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

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_email_message_type
        ON emails(message_type)
        """
    )

    conn.commit()
    conn.close()

    _ensure_schema()


def _ensure_column(
    conn: sqlite3.Connection,
    column_name: str,
    column_definition: str,
) -> None:
    """Add a database column if it does not already exist."""
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
    Upgrade an existing emails.db database with any columns
    required by the current email agent.
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

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_email_message_type
        ON emails(message_type)
        """
    )

    conn.commit()
    conn.close()


def save_email(
    email: Email,
    status: str = "new",
) -> None:
    """
    Save an incoming email.

    Existing message IDs are ignored so the same email
    cannot accidentally be inserted twice.
    """
    init_email_db()

    conn = get_connection()

    timestamp = email.timestamp

    if timestamp is None:
        timestamp_value = ""
    elif hasattr(timestamp, "isoformat"):
        timestamp_value = timestamp.isoformat()
    else:
        timestamp_value = str(timestamp)

    attachments = ",".join(
        str(item)
        for item in email.attachments
    )

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
            timestamp_value,
            attachments,
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
    """Update the processing status of an email."""
    init_email_db()

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
    Save the agent decision and analysis metadata.

    Emails requiring human intervention automatically receive
    a pending human review status.
    """
    init_email_db()

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
    Update the human review state for an email.

    Supported review statuses:
    - pending
    - approved
    - rejected
    - resolved
    """
    allowed_statuses = {
        "pending",
        "approved",
        "rejected",
        "resolved",
    }

    if review_status not in allowed_statuses:
        raise ValueError(
            f"Invalid review status: {review_status}. "
            f"Expected one of: "
            f"{', '.join(sorted(allowed_statuses))}"
        )

    if not message_id.strip():
        raise ValueError("message_id cannot be empty.")

    if note is None:
        note = ""

    init_email_db()

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT message_id
        FROM emails
        WHERE message_id = ?
        """,
        (message_id,),
    ).fetchone()

    if existing is None:
        conn.close()
        raise ValueError(
            f"Email not found: {message_id}"
        )

    if review_status == "pending":
        conn.execute(
            """
            UPDATE emails
            SET
                human_review_status = ?,
                human_review_note = ?,
                reviewed_at = NULL
            WHERE message_id = ?
            """,
            (
                review_status,
                note,
                message_id,
            ),
        )
    else:
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
) -> str:
    """
    Save an outgoing support reply as a separate message.

    The reply receives its own unique message ID so it never
    conflicts with the incoming email's primary key.

    Returns:
        The generated reply message ID.
    """
    if not message_id.strip():
        raise ValueError("message_id cannot be empty.")

    if not thread_id.strip():
        raise ValueError("thread_id cannot be empty.")

    if not recipient.strip():
        raise ValueError("recipient cannot be empty.")

    if not subject.strip():
        raise ValueError("subject cannot be empty.")

    if not body.strip():
        raise ValueError("body cannot be empty.")

    init_email_db()

    conn = get_connection()

    base_reply_id = f"reply-{message_id}"
    reply_message_id = base_reply_id
    counter = 1

    while conn.execute(
        """
        SELECT 1
        FROM emails
        WHERE message_id = ?
        """,
        (reply_message_id,),
    ).fetchone() is not None:
        reply_message_id = (
            f"{base_reply_id}-{counter}"
        )
        counter += 1

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
            ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?
        )
        """,
        (
            reply_message_id,
            thread_id,
            "support",
            recipient,
            subject,
            body,
            "",
            "sent",
            "reply",
        ),
    )

    conn.commit()
    conn.close()

    return reply_message_id


def get_replies_for_thread(
    thread_id: str,
) -> list[dict]:
    """Return all support replies belonging to a thread."""
    init_email_db()

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
            timestamp,
            created_at
        FROM emails
        WHERE thread_id = ?
          AND message_type = 'reply'
        ORDER BY
            COALESCE(timestamp, created_at) ASC,
            rowid ASC
        """,
        (thread_id,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]