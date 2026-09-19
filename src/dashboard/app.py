import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, render_template
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

from src.email_database import get_connection, init_email_db
from src.gmail_reply_sender import send_replies
from src.notifications import check_and_notify

BASE_DIR = Path(__file__).resolve().parents[2]
APP_ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
app.template_folder = str(APP_ROOT / "templates")
app.static_folder = str(BASE_DIR / "src" / "static")
app.static_url_path = "/static"
CORS(app)

GMAIL_CREDENTIALS_PATH = Path(os.environ.get("GMAIL_CREDENTIALS_PATH", str(BASE_DIR / "gmail_oauth_credentials.json"))).expanduser()
GMAIL_TOKEN_PATH = Path(os.environ.get("GMAIL_TOKEN_PATH", str(BASE_DIR / "gmail_token.json"))).expanduser()
PYTHON = sys.executable
init_email_db()

_agent_lock = threading.Lock()
_agent_stop = threading.Event()
_agent_thread = None
_agent_processes = []
_agent_state = {"running": False, "status": "Stopped", "last_error": None, "last_run": None}

# APScheduler initialization
scheduler = None

def init_scheduler():
    """Initialize and start APScheduler for background jobs."""
    global scheduler
    if scheduler is not None:
        return
    
    scheduler = BackgroundScheduler()
    
    # Job 1: Send email replies every 2 minutes
    scheduler.add_job(
        func=send_replies,
        trigger="interval",
        minutes=2,
        id="email_reply_job",
        name="Send email replies",
        replace_existing=True,
        max_instances=1
    )
    
    # Job 2: Check and send Telegram notifications every 2 minutes
    scheduler.add_job(
        func=check_and_notify,
        trigger="interval",
        minutes=2,
        id="notification_job",
        name="Send Telegram notifications",
        replace_existing=True,
        max_instances=1
    )
    
    scheduler.start()
    app.logger.info("✅ APScheduler started - background jobs running every 2 minutes")


def _auth_error():
    missing = []
    if not GMAIL_CREDENTIALS_PATH.is_file():
        missing.append(f"credentials file: {GMAIL_CREDENTIALS_PATH}")
    if not GMAIL_TOKEN_PATH.is_file():
        missing.append(f"token file: {GMAIL_TOKEN_PATH}")
    return "Gmail authentication files are missing or inaccessible: " + ", ".join(missing)


def _run_command(command):
    process = None
    try:
        with _agent_lock:
            process = subprocess.Popen(
                command, cwd=str(BASE_DIR), stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, start_new_session=True,
                env={**os.environ, "GMAIL_CREDENTIALS_PATH": str(GMAIL_CREDENTIALS_PATH), "GMAIL_TOKEN_PATH": str(GMAIL_TOKEN_PATH)},
            )
            _agent_processes.append(process)
        output, _ = process.communicate()
        if output:
            _agent_state["last_output"] = output[-2000:]
        return process.returncode
    finally:
        with _agent_lock:
            if process in _agent_processes:
                _agent_processes.remove(process)


def _pipeline():
    commands = [
        [PYTHON, "-m", "src.gmail_email_connector"],
        [PYTHON, "src/smart_email_agent.py"],
        [PYTHON, "-m", "src.notifications"],
        [PYTHON, "src/urgent_handler.py"],
        [PYTHON, "src/gmail_reply_sender.py"],
    ]
    try:
        while not _agent_stop.is_set():
            for command in commands:
                if _agent_stop.is_set():
                    break
                result = _run_command(command)
                if result not in (0, None) and not _agent_stop.is_set():
                    _agent_state["last_error"] = f"Step {' '.join(command[1:])} exited with code {result}. See last_output for details."
            _agent_state["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
            if not _agent_stop.is_set():
                _agent_state["status"] = "Running · next check in 5 minutes"
                _agent_stop.wait(300)
    except Exception as exc:
        _agent_state["last_error"] = str(exc)
        _agent_state["status"] = "Error"
    finally:
        _agent_state["running"] = False
        if _agent_state["status"] != "Error":
            _agent_state["status"] = "Stopped"


def _start_agent():
    global _agent_thread
    with _agent_lock:
        if _agent_thread and _agent_thread.is_alive():
            return False
        _agent_stop.clear()
        _agent_state.update({"running": True, "status": "Starting agent…", "last_error": None, "last_output": None})
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
    _agent_state.update({"running": False, "status": "Stopped"})


@app.route("/")
def home(): return render_template("index.html")
@app.route("/dashboard")
def index(): return render_template("index.html")
@app.route("/intro")
def intro(): return render_template("intro.html")
@app.route("/review")
def review_dashboard(): return render_template("review.html")


@app.route("/api/agent/status")
def agent_status():
    return jsonify({**_agent_state, "credentials_path": str(GMAIL_CREDENTIALS_PATH), "token_path": str(GMAIL_TOKEN_PATH), "credentials_available": GMAIL_CREDENTIALS_PATH.is_file(), "token_available": GMAIL_TOKEN_PATH.is_file()})


@app.route("/api/agent/start", methods=["POST"])
def start_agent():
    if not GMAIL_CREDENTIALS_PATH.is_file() or not GMAIL_TOKEN_PATH.is_file():
        return jsonify({"ok": False, "error": _auth_error(), **_agent_state}), 400
    return jsonify({"ok": _start_agent(), **_agent_state})


@app.route("/api/agent/stop", methods=["POST"])
def stop_agent():
    _stop_agent()
    return jsonify({"ok": True, **_agent_state})


@app.route("/api/stats")
def get_stats():
    try:
        init_email_db()
        conn = get_connection()
        row = conn.execute("""SELECT COUNT(*) AS total, SUM(CASE WHEN decision_action IN ('auto_reply','auto_reply_sent') THEN 1 ELSE 0 END) AS auto_replied, SUM(CASE WHEN decision_action IN ('human_review','escalate','urgent_preliminary_reply') THEN 1 ELSE 0 END) AS pending, SUM(CASE WHEN decision_urgency='high' AND human_review_status='pending' THEN 1 ELSE 0 END) AS urgent FROM emails WHERE message_type='email'""").fetchone()
        conn.close()
        return jsonify({"total": row["total"] or 0, "auto_replied": row["auto_replied"] or 0, "pending": row["pending"] or 0, "urgent": row["urgent"] or 0})
    except Exception as exc:
        app.logger.exception("DB stats failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/pending-emails")
def get_pending():
    init_email_db(); conn = get_connection()
    rows = conn.execute("SELECT message_id, subject, sender, body FROM emails WHERE decision_action IN ('human_review','escalate','urgent_preliminary_reply') ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close(); return jsonify([dict(row) for row in rows])


@app.route("/api/email/<email_id>")
def get_email(email_id):
    init_email_db(); conn = get_connection()
    row = conn.execute("SELECT message_id, subject, sender, body, created_at FROM emails WHERE message_id=?", (email_id,)).fetchone()
    conn.close(); return (jsonify(dict(row)), 200) if row else (jsonify({}), 404)


@app.route("/api/email/<email_id>/approve", methods=["POST"])
def approve(email_id):
    conn = get_connection(); conn.execute("UPDATE emails SET decision_action='approved', human_review_status='approved' WHERE message_id=?", (email_id,)); conn.commit(); conn.close(); return jsonify({"ok": True})


@app.route("/api/email/<email_id>/reject", methods=["POST"])
def reject(email_id):
    conn = get_connection(); conn.execute("UPDATE emails SET decision_action='escalate', human_review_status='rejected' WHERE message_id=?", (email_id,)); conn.commit(); conn.close(); return jsonify({"ok": True})


@app.route("/api/process-emails", methods=["POST"])
def process_emails(): return start_agent()


# Initialize scheduler when app starts
with app.app_context():
    init_scheduler()


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
