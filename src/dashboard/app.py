import os
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template
from flask_cors import CORS

from src.email_database import get_connection

BASE_DIR = Path(__file__).resolve().parents[2]
APP_ROOT = Path(__file__).resolve().parent

app = Flask(__name__)
app.template_folder = str(APP_ROOT / "templates")
app.static_folder = str(BASE_DIR / "src" / "static")
app.static_url_path = "/static"
CORS(app)

GMAIL_CREDENTIALS_PATH = BASE_DIR / "gmail_oauth_credentials.json"
SMART_AGENT_PATH = BASE_DIR / "src" / "smart_email_agent.py"
REPLY_SENDER_PATH = BASE_DIR / "src" / "gmail_reply_sender.py"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/dashboard")
def index():
    return render_template("index.html")


@app.route("/intro")
def intro():
    return render_template("intro.html")


@app.route("/review")
def review_dashboard():
    return render_template("review.html")


@app.route("/api/stats", methods=["GET"])
def get_stats():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM emails WHERE decision_action = 'auto_reply'")
        auto = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM emails WHERE decision_action IN ('human_review', 'escalate')")
        pending = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM emails")
        total = cursor.fetchone()[0]
        conn.close()
        return jsonify({"auto_replied": auto, "pending": pending, "total": total})
    except Exception as exc:
        app.logger.exception("DB stats failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/pending-emails", methods=["GET"])
def get_pending():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, subject, sender, body FROM emails WHERE decision_action IN ('human_review', 'escalate') LIMIT 50"
        )
        emails = cursor.fetchall()
        conn.close()
        return jsonify(
            [{"id": e[0], "subject": e[1], "sender": e[2], "body": e[3]} for e in emails]
        )
    except Exception:
        return jsonify([]), 500


@app.route("/api/email/<email_id>", methods=["GET"])
def get_email(email_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, subject, sender, body, created_at FROM emails WHERE id = ?",
            (email_id,),
        )
        e = cursor.fetchone()
        conn.close()
        if not e:
            return jsonify({}), 404
        return jsonify(
            {"id": e[0], "subject": e[1], "sender": e[2], "body": e[3], "created_at": e[4]}
        )
    except Exception:
        return jsonify({}), 500


@app.route("/api/email/<email_id>/approve", methods=["POST"])
def approve(email_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE emails SET decision_action = 'approved' WHERE id = ?", (email_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"ok": False}), 500


@app.route("/api/email/<email_id>/reject", methods=["POST"])
def reject(email_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE emails SET decision_action = 'escalate' WHERE id = ?", (email_id,))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"ok": False}), 500


@app.route("/api/process-emails", methods=["POST"])
def process_emails():
    """Run Gmail processing only when credentials are configured."""
    if not GMAIL_CREDENTIALS_PATH.exists():
        return jsonify(
            {
                "ok": False,
                "skipped": True,
                "message": (
                    "Gmail OAuth credentials are not configured yet. "
                    "Add gmail_oauth_credentials.json or set the required env vars "
                    "before enabling email automation."
                ),
            }
        ), 200

    try:
        commands = [
            [sys.executable, str(SMART_AGENT_PATH)],
            [sys.executable, str(REPLY_SENDER_PATH)],
        ]

        for command in commands:
            subprocess.run(
                command,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        return jsonify({"ok": True, "message": "Email processing started"})
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Processing timed out after 30 seconds."}), 504
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/human-review-queue")
def human_review_queue():
    """Get emails waiting for human review."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT message_id, sender, subject, body
            FROM emails
            WHERE decision_action = 'human_review'
            AND decision_urgency = 'high'
            AND status = 'processed'
            ORDER BY created_at DESC
            LIMIT 10
            """
        )
        emails = cursor.fetchall()
        conn.close()

        return jsonify(
            {
                "emails": [
                    {
                        "message_id": e[0],
                        "sender": e[1],
                        "subject": e[2],
                        "body": e[3],
                    }
                    for e in emails
                ]
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/email/<msg_id>/resolve", methods=["POST"])
def resolve_email(msg_id):
    """Mark email as resolved by human."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE emails
            SET status = 'human_resolved', human_review_status = 'resolved'
            WHERE message_id = ?
            """,
            (msg_id,),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    print("✅ Dashboard running on http://0.0.0.0:5000")
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
