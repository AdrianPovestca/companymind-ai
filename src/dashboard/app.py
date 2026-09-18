import os
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template
from flask_cors import CORS

from src.email_database import get_connection, init_email_db


BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(BASE_DIR / "src" / "static"),
    static_url_path="/static",
)
CORS(app)

# Create the SQLite schema when the Render web process starts. The database is
# still ephemeral on Render's free filesystem, so use a managed database for
# production persistence if required.
try:
    init_email_db()
except Exception as exc:
    app.logger.warning("Database initialization failed: %s", exc)


def _close_connection(conn):
    if conn is not None:
        conn.close()


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/dashboard")
def dashboard():
    return render_template("index.html")


@app.get("/intro")
def intro():
    template = TEMPLATES_DIR / "intro.html"
    if template.exists():
        return render_template("intro.html")
    return render_template("index.html")


@app.get("/review")
def review_dashboard():
    template = TEMPLATES_DIR / "review.html"
    if template.exists():
        return render_template("review.html")
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/stats")
def get_stats():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        auto_replied = cursor.execute(
            "SELECT COUNT(*) FROM emails WHERE decision_action = ?",
            ("auto_reply",),
        ).fetchone()[0]
        pending = cursor.execute(
            """SELECT COUNT(*) FROM emails
               WHERE decision_action IN ('human_review', 'escalate')"""
        ).fetchone()[0]
        total = cursor.execute("SELECT COUNT(*) FROM emails").fetchone()[0]
        return jsonify(
            {"auto_replied": auto_replied, "pending": pending, "total": total}
        )
    except Exception as exc:
        app.logger.exception("Could not read dashboard statistics")
        return jsonify({"error": str(exc)}), 500
    finally:
        _close_connection(conn)


@app.get("/api/pending-emails")
def get_pending():
    conn = None
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT message_id, subject, sender, body
               FROM emails
               WHERE decision_action IN ('human_review', 'escalate')
               ORDER BY created_at DESC
               LIMIT 50"""
        ).fetchall()
        return jsonify(
            [
                {
                    "id": row[0],
                    "message_id": row[0],
                    "subject": row[1],
                    "sender": row[2],
                    "body": row[3],
                }
                for row in rows
            ]
        )
    except Exception as exc:
        app.logger.exception("Could not read pending emails")
        return jsonify({"error": str(exc)}), 500
    finally:
        _close_connection(conn)


@app.get("/api/human-review-queue")
def human_review_queue():
    conn = None
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT message_id, sender, subject, body
               FROM emails
               WHERE decision_action = 'human_review'
               AND human_review_status = 'pending'
               ORDER BY created_at DESC
               LIMIT 50"""
        ).fetchall()
        return jsonify(
            {
                "emails": [
                    {
                        "message_id": row[0],
                        "sender": row[1],
                        "subject": row[2],
                        "body": row[3],
                    }
                    for row in rows
                ]
            }
        )
    except Exception as exc:
        app.logger.exception("Could not read human review queue")
        return jsonify({"error": str(exc)}), 500
    finally:
        _close_connection(conn)


@app.post("/api/email/<message_id>/resolve")
def resolve_email(message_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.execute(
            """UPDATE emails
               SET status = 'human_resolved', human_review_status = 'resolved'
               WHERE message_id = ?""",
            (message_id,),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Email not found"}), 404
        return jsonify({"success": True})
    except Exception as exc:
        app.logger.exception("Could not resolve email")
        return jsonify({"error": str(exc)}), 500
    finally:
        _close_connection(conn)


@app.post("/api/process-emails")
def process_emails():
    """Run the existing email processing scripts from the repository root."""
    try:
        commands = [
            [sys.executable, "src/smart_email_agent.py"],
            [sys.executable, "src/gmail_reply_sender.py"],
        ]
        for command in commands:
            result = subprocess.run(
                command,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode != 0:
                app.logger.error("Command failed: %s\n%s", command, result.stderr)
                return jsonify({"ok": False, "error": result.stderr}), 500
        return jsonify({"ok": True, "message": "Email processing complete"})
    except Exception as exc:
        app.logger.exception("Email processing failed")
        return jsonify({"ok": False, "error": str(exc)}), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
