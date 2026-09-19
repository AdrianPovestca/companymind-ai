"""Campaign management database module."""
import sqlite3
from pathlib import Path
import os
from datetime import datetime
from typing import Optional, List

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("DB_PATH", str(BASE_DIR / "emails.db"))).expanduser()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_campaign_db() -> None:
    """Initialize campaign tables."""
    conn = get_connection()
    
    # Campaigns table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            sender_email TEXT NOT NULL,
            recipient_count INTEGER DEFAULT 0,
            speed_setting TEXT DEFAULT 'normal',
            scheduled_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            status TEXT DEFAULT 'draft',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Campaign recipients table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaign_recipients (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            email TEXT NOT NULL,
            name TEXT,
            personalization_data TEXT,
            status TEXT DEFAULT 'pending',
            sent_at TEXT,
            error_message TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    """)
    
    # Campaign logs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaign_logs (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            event_type TEXT,
            message TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_campaign_status ON campaigns(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_campaign_recipients_campaign ON campaign_recipients(campaign_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_campaign_recipients_status ON campaign_recipients(status)")
    
    conn.commit()
    conn.close()


def create_campaign(campaign_id: str, name: str, subject: str, body: str, 
                   sender_email: str, recipient_count: int, speed_setting: str = 'normal',
                   scheduled_at: Optional[str] = None) -> bool:
    """Create new campaign."""
    init_campaign_db()
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO campaigns 
            (id, name, subject, body, sender_email, recipient_count, speed_setting, scheduled_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft')
        """, (campaign_id, name, subject, body, sender_email, recipient_count, speed_setting, scheduled_at))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating campaign: {e}")
        return False
    finally:
        conn.close()


def add_campaign_recipient(recipient_id: str, campaign_id: str, email: str, 
                          name: Optional[str] = None, personalization_data: Optional[str] = None) -> bool:
    """Add recipient to campaign."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO campaign_recipients 
            (id, campaign_id, email, name, personalization_data, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (recipient_id, campaign_id, email, name, personalization_data))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding recipient: {e}")
        return False
    finally:
        conn.close()


def get_campaign(campaign_id: str) -> Optional[dict]:
    """Get campaign by ID."""
    init_campaign_db()
    conn = get_connection()
    row = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_campaigns(status: Optional[str] = None, limit: int = 50) -> List[dict]:
    """Get campaigns with optional filter."""
    init_campaign_db()
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM campaigns WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM campaigns ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_campaign_status(campaign_id: str, status: str) -> bool:
    """Update campaign status."""
    conn = get_connection()
    try:
        if status == 'started':
            conn.execute(
                "UPDATE campaigns SET status = ?, started_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, campaign_id)
            )
        elif status == 'completed':
            conn.execute(
                "UPDATE campaigns SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, campaign_id)
            )
        else:
            conn.execute("UPDATE campaigns SET status = ? WHERE id = ?", (status, campaign_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating campaign: {e}")
        return False
    finally:
        conn.close()


def get_campaign_recipients(campaign_id: str, status: Optional[str] = None) -> List[dict]:
    """Get recipients for campaign."""
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT * FROM campaign_recipients WHERE campaign_id = ? AND status = ?",
            (campaign_id, status)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM campaign_recipients WHERE campaign_id = ?",
            (campaign_id,)
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_recipient_status(recipient_id: str, status: str, error_message: Optional[str] = None) -> bool:
    """Update recipient status after sending."""
    conn = get_connection()
    try:
        if status == 'sent':
            conn.execute(
                "UPDATE campaign_recipients SET status = ?, sent_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, recipient_id)
            )
        elif status == 'failed':
            conn.execute(
                "UPDATE campaign_recipients SET status = ?, error_message = ? WHERE id = ?",
                (status, error_message, recipient_id)
            )
        else:
            conn.execute("UPDATE campaign_recipients SET status = ? WHERE id = ?", (status, recipient_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating recipient: {e}")
        return False
    finally:
        conn.close()


def get_campaign_stats(campaign_id: str) -> dict:
    """Get campaign statistics."""
    conn = get_connection()
    
    total = conn.execute(
        "SELECT COUNT(*) as cnt FROM campaign_recipients WHERE campaign_id = ?",
        (campaign_id,)
    ).fetchone()['cnt']
    
    sent = conn.execute(
        "SELECT COUNT(*) as cnt FROM campaign_recipients WHERE campaign_id = ? AND status = 'sent'",
        (campaign_id,)
    ).fetchone()['cnt']
    
    failed = conn.execute(
        "SELECT COUNT(*) as cnt FROM campaign_recipients WHERE campaign_id = ? AND status = 'failed'",
        (campaign_id,)
    ).fetchone()['cnt']
    
    pending = conn.execute(
        "SELECT COUNT(*) as cnt FROM campaign_recipients WHERE campaign_id = ? AND status = 'pending'",
        (campaign_id,)
    ).fetchone()['cnt']
    
    conn.close()
    return {
        'total': total,
        'sent': sent,
        'failed': failed,
        'pending': pending
    }


def add_campaign_log(log_id: str, campaign_id: str, event_type: str, message: str) -> bool:
    """Add log entry for campaign."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO campaign_logs (id, campaign_id, event_type, message) VALUES (?, ?, ?, ?)",
            (log_id, campaign_id, event_type, message)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding log: {e}")
        return False
    finally:
        conn.close()
