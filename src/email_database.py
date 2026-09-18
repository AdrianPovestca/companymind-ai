import os
import sqlite3
from pathlib import Path
from typing import Optional

from src.email_models import Email

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("DB_PATH", str(BASE_DIR / "emails.db"))).expanduser()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn: sqlite3.Connection, column_name: str, column_definition: str) -> None:
    columns = conn.execute("PRAGMA table_info(emails)").fetchall()
    existing_columns = {column[1] for column in columns}
    if column_name not in existing_columns:
        conn.execute(f"ALTER TABLE emails ADD COLUMN {column_name} {column_definition}")


def init_email_db() -> None:
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
            message_type TEXT DEFAULT 'email',
            urgent_notified_at TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_email_thread_id ON emails(thread_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_email_status ON emails(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_email_message_type ON emails(message_type)")

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
        "urgent_notified_at": "TEXT",
    }
    for column_name, column_definition in required_columns.items():
        _ensure_column(conn, column_name, column_definition)

    conn.commit()
    conn.close()


def save_email(email: Email, status: str = "new") -> None:
    init_email_db()
    conn = get_connection()
    timestamp = email.timestamp.isoformat() if hasattr(email.timestamp, "isoformat") else str(email.timestamp or "")
    attachments = ",".join(str(item) for item in email.attachments)
    conn.execute(
        """
        INSERT OR IGNORE INTO emails (
            message_id, thread_id, sender, recipient, subject, body,
            timestamp, attachments, status, message_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email.message_id,
            email.thread_id,
            email.sender,
            email.recipient,
            email.subject,
            email.body,
            timestamp,
            attachments,
            status,
            "email",
        ),
    )
    conn.commit()
    conn.close()


def get_email(message_id: str) -> Optional[dict]:
    init_email_db()
    conn = get_connection()
    row = conn.execute("SELECT * FROM emails WHERE message_id = ?", (message_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
