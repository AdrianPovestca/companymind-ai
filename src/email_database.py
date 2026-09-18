"""Email database layer."""
import sqlite3
from pathlib import Path
from typing import Optional
from src.email_models import Email

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "emails.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema():
    conn = get_connection()
    columns = {row[1] for row in conn.execute("PRAGMA table_info(emails)")}
    for name, definition in {
        "urgent_notified_at": "TEXT",
        "decision_action": "TEXT",
        "decision_reason": "TEXT",
        "decision_intent": "TEXT",
        "decision_urgency": "TEXT",
        "requires_human": "INTEGER DEFAULT 0",
        "human_review_status": "TEXT",
        "human_review_note": "TEXT",
        "reviewed_at": "TEXT",
        "message_type": "TEXT DEFAULT 'email'",
    }.items():
        if name not in columns:
            conn.execute(f"ALTER TABLE emails ADD COLUMN {name} {definition}")
    conn.commit(); conn.close()


def init_email_db():
    conn = get_connection()
    conn.execute("""CREATE TABLE IF NOT EXISTS emails (
        message_id TEXT PRIMARY KEY, thread_id TEXT NOT NULL, sender TEXT NOT NULL,
        recipient TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL,
        timestamp TEXT NOT NULL, attachments TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP, decision_action TEXT, decision_reason TEXT,
        decision_intent TEXT, decision_urgency TEXT, requires_human INTEGER DEFAULT 0,
        human_review_status TEXT, human_review_note TEXT, reviewed_at TEXT,
        message_type TEXT DEFAULT 'email', urgent_notified_at TEXT)""")
    conn.commit(); conn.close(); _ensure_schema()


# Keep the public helpers used by the rest of the application.
def save_email(email: Email, status: str = "new"):
    init_email_db()
    conn = get_connection()
    timestamp = email.timestamp.isoformat() if hasattr(email.timestamp, "isoformat") else str(email.timestamp or "")
    conn.execute("""INSERT OR IGNORE INTO emails(message_id,thread_id,sender,recipient,subject,body,timestamp,attachments,status,message_type) VALUES(?,?,?,?,?,?,?,?,?,?)""", (email.message_id, email.thread_id, email.sender, email.recipient, email.subject, email.body, timestamp, ",".join(map(str, email.attachments)), status, "email"))
    conn.commit(); conn.close()


def get_email(message_id: str) -> Optional[dict]:
    init_email_db(); conn = get_connection(); row = conn.execute("SELECT * FROM emails WHERE message_id=?", (message_id,)).fetchone(); conn.close()
    return dict(row) if row else None
