import os
import subprocess
import sys
import threading
import time
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
PYTHON = sys.executable

_agent_lock = threading.Lock()
_agent_stop = threading.Event()
_agent_thread = None
_agent_processes = []
_agent_state = {"running": False, "status": "Oprit", "last_error": None, "last_run": None}


def _pipeline():
    """Run the complete pipeline until Stop is pressed."""
    global _agent_processes
    commands = [
        [PYTHON, "-m", "src.gmail_email_connector"],
        [PYTHON, "src/smart_email_agent.py"],
        [PYTHON, "-m", "src.notifications"],
        [PYTHON, "src/urgent_handler.py"],
        [PYTHON, "src/gmail_reply_sender.py"],
    ]
    while not _agent_stop.is_set():
        try:
            for command in commands:
                if _agent_stop.is_set():
                    break
                with _agent_lock:
                    process = subprocess.Popen(
                        command, cwd=str(BASE_DIR), stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True,
                    )
                    _agent_processes.append(process)
                process.wait()
                with _agent_lock:
                    if process in _agent_processes:
                        _agent_processes.remove(process)
                if process.returncode not in (0, None) and not _agent_stop.is_set():
                    _agent_state["last_error"] = f"Procesul {' '.join(command[1:])} a eșuat ({process.returncode})"
            _agent_state["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
            _agent_state["status"] = "Pornit · verific din nou în 5 minute" if not _agent_stop.is_set() else "Oprit"
            _agent_stop.wait(300)
        except Exception as exc:
            _agent_state["last_error"] = str(exc)
            _agent_state["status"] = "Eroare"
            break
    _agent_state["running"] = False
    if _agent_state["status"] != "Eroare":
        _agent_state["status"] = "Oprit"


def _start_agent():
    global _agent_thread
    with _agent_lock:
        if _agent_thread and _agent_thread.is_alive():
            return False
        _agent_stop.clear()
        _agent_state.update({"running": True, "status": "Pornez agentul…", "last_error": None})
        _agent_thread = threading.Thread(target=_pipeline, daemon=True, name="email-agent")
        _agent_thread.start()
    return True


def _stop_agent():
    _agent_stop.set()
    with _agent_lock:
        processes = list(_agent_processes)
    for process in processes:
        if process.poll() is None:
            process.terminate()
    return True


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


@app.route("/api/agent/status")
def agent_status():
    return jsonify(_agent_state)


@app.route("/api/agent/start", methods=["POST"])
def start_agent():
    if not GMAIL_CREDENTIALS_PATH.exists():
        return jsonify({"ok": False, "error": "Lipsește gmail_oauth_credentials.json."}), 400
    return jsonify({"ok": _start_agent(), **_agent_state})


@app.route("/api/agent/stop", methods=["POST"])
def stop_agent():
    _stop_agent()
    return jsonify({"ok": True, **_agent_state})


@app.route("/api/stats")
def get_stats():
    try:
        conn = get_connection()
        row = conn.execute("""
            SELECT
              COUNT(*) AS total,
              SUM(CASE WHEN decision_action IN ('auto_reply', 'auto_reply_sent') THEN 1 ELSE 0 END) AS auto_replied,
              SUM(CASE WHEN decision_action IN ('human_review', 'escalate', 'urgent_preliminary_reply') THEN 1 ELSE 0 END) AS pending,
              SUM(CASE WHEN decision_urgency = 'high' AND human_review_status = 'pending' THEN 1 ELSE 0 END) AS urgent
            FROM emails WHERE message_type = 'email'
        """).fetchone()
        conn.close()
        return jsonify({"total": row[0] or 0, "auto_replied": row[1] or 0, "pending": row[2] or 0, "urgent": row[3] or 0})
    except Exception as exc:
        app.logger.exception("DB stats failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/pending-emails")
def get_pending():
    try:
        conn = get_connection()
        rows = conn.execute("""
            SELECT message_id, subject, sender, body FROM emails
            WHERE decision_action IN ('human_review', 'escalate', 'urgent_preliminary_reply')
            ORDER BY created_at DESC LIMIT 50
        """).fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])
    except Exception:
        return jsonify([]), 500


@app.route("/api/email/<email_id>")
def get_email(email_id):
    conn = get_connection()
    row = conn.execute("SELECT message_id, subject, sender, body, created_at FROM emails WHERE message_id = ?", (email_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({}), 404
    return jsonify(dict(row))


@app.route("/api/email/<email_id>/approve", methods=["POST"])
def approve(email_id):
    conn = get_connection()
    conn.execute("UPDATE emails SET decision_action = 'approved', human_review_status = 'approved' WHERE message_id = ?", (email_id,))
    conn.commit(); conn.close()
    return jsonify({"ok": True})


@app.route("/api/email/<email_id>/reject", methods=["POST"])
def reject(email_id):
    conn = get_connection()
    conn.execute("UPDATE emails SET decision_action = 'escalate', human_review_status = 'rejected' WHERE message_id = ?", (email_id,))
    conn.commit(); conn.close()
    return jsonify({"ok": True})


@app.route("/api/process-emails", methods=["POST"])
def process_emails():
    """Backward-compatible alias for Start."""
    if not GMAIL_CREDENTIALS_PATH.exists():
        return jsonify({"ok": False, "error": "Lipsește gmail_oauth_credentials.json."}), 400
    _start_agent()
    return jsonify({"ok": True, "message": "Agentul este pornit", **_agent_state})


if __name__ == "__main__":
    print("✅ Dashboard running on http://0.0.0.0:5000")
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
