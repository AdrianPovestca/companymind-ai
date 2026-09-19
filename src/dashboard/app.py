import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request
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
    app.logger.info("APScheduler started - background jobs running every 2 minutes")


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
        _agent_state.update({"running": True, "status": "Starting agent...", "last_error": None, "last_output": None})
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
@app.route("/history")
def history_page(): return render_template("history.html")
@app.route("/campaigns")
def campaigns_page(): return render_template("campaigns.html")


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


@app.route("/api/trigger-jobs", methods=["GET", "POST"])
def trigger_jobs():
    """Trigger background jobs - called by external cron."""
    try:
        replies_sent = send_replies()
        notifications_sent = check_and_notify()
        return jsonify({
            "ok": True,
            "replies_sent": replies_sent,
            "notifications_sent": notifications_sent,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as exc:
        app.logger.error(f"Trigger jobs failed: {exc}")
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/email-history")
def get_email_history():
    """Get all emails with category and stats."""
    try:
        init_email_db()
        conn = get_connection()
        rows = conn.execute("""
            SELECT message_id, sender, subject, email_category, created_at, decision_urgency
            FROM emails
            ORDER BY created_at DESC
            LIMIT 500
        """).fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])
    except Exception as exc:
        app.logger.exception("Email history failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/spam-emails")
def get_spam_emails():
    """Get emails detected as spam - review if legitimate."""
    try:
        init_email_db()
        conn = get_connection()
        rows = conn.execute("""
            SELECT message_id, sender, subject, created_at
            FROM emails
            WHERE email_category = 'spam'
            ORDER BY created_at DESC
            LIMIT 200
        """).fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])
    except Exception as exc:
        app.logger.exception("Spam emails failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/history-stats")
def get_history_stats():
    """Get statistics on email categories."""
    try:
        init_email_db()
        conn = get_connection()
        stats = {}
        for category in ['normal', 'person', 'marketing', 'urgent', 'spam', 'promotion']:
            count = conn.execute(
                "SELECT COUNT(*) as cnt FROM emails WHERE email_category = ?",
                (category,)
            ).fetchone()['cnt']
            stats[category] = count
        
        total = conn.execute("SELECT COUNT(*) as cnt FROM emails").fetchone()['cnt']
        stats['total'] = total
        
        conn.close()
        return jsonify(stats)
    except Exception as exc:
        app.logger.exception("History stats failed")
        return jsonify({"error": str(exc)}), 500


# ===== CAMPAIGN ENDPOINTS =====

@app.route("/api/campaigns", methods=["GET"])
def get_campaigns_list():
    """Get all campaigns."""
    try:
        from src.campaign_database import get_campaigns
        campaigns = get_campaigns(limit=100)
        return jsonify(campaigns)
    except Exception as exc:
        app.logger.exception("Get campaigns failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/campaigns/<campaign_id>", methods=["GET"])
def get_campaign_detail(campaign_id):
    """Get campaign details with stats."""
    try:
        from src.campaign_database import get_campaign, get_campaign_stats
        campaign = get_campaign(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        stats = get_campaign_stats(campaign_id)
        return jsonify({**dict(campaign), **stats})
    except Exception as exc:
        app.logger.exception("Get campaign detail failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/campaigns", methods=["POST"])
def create_campaign():
    """Create new campaign."""
    try:
        from src.campaign_database import create_campaign, add_campaign_recipient
        import json
        import uuid
        
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['name', 'subject', 'body', 'sender_email', 'recipients', 'speed_setting']):
            return jsonify({"error": "Missing required fields"}), 400
        
        campaign_id = str(uuid.uuid4())
        recipients = data.get('recipients', [])
        scheduled_at = data.get('scheduled_at')
        
        # Create campaign
        create_campaign(
            campaign_id=campaign_id,
            name=data['name'],
            subject=data['subject'],
            body=data['body'],
            sender_email=data['sender_email'],
            recipient_count=len(recipients),
            speed_setting=data.get('speed_setting', 'normal'),
            scheduled_at=scheduled_at
        )
        
        # Add recipients
        for recipient in recipients:
            recipient_id = str(uuid.uuid4())
            add_campaign_recipient(
                recipient_id=recipient_id,
                campaign_id=campaign_id,
                email=recipient.get('email'),
                name=recipient.get('name'),
                personalization_data=json.dumps(recipient.get('data', {})) if recipient.get('data') else None
            )
        
        return jsonify({"ok": True, "campaign_id": campaign_id}), 201
    except Exception as exc:
        app.logger.exception("Create campaign failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/campaigns/<campaign_id>/send", methods=["POST"])
def send_campaign(campaign_id):
    """Send campaign immediately."""
    try:
        from src.campaign_database import get_campaign, update_campaign_status
        from src.campaign_sender import CampaignSender
        
        campaign = get_campaign(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        if campaign['status'] not in ['draft', 'scheduled']:
            return jsonify({"error": f"Campaign status is {campaign['status']}, cannot send"}), 400
        
        # Check Gmail credentials
        if not GMAIL_CREDENTIALS_PATH.is_file():
            return jsonify({"error": "Gmail credentials not configured"}), 400
        
        # Send campaign (in background thread to avoid timeout)
        sender = CampaignSender(str(GMAIL_CREDENTIALS_PATH))
        
        def send_background():
            try:
                stats = sender.process_campaign(campaign_id)
                app.logger.info(f"Campaign {campaign_id} sent: {stats}")
            except Exception as e:
                app.logger.exception(f"Campaign send failed: {e}")
                update_campaign_status(campaign_id, 'failed')
        
        thread = threading.Thread(target=send_background, daemon=True)
        thread.start()
        
        return jsonify({"ok": True, "status": "Campaign sending started", "campaign_id": campaign_id})
    except Exception as exc:
        app.logger.exception("Send campaign failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/campaigns/<campaign_id>/schedule", methods=["POST"])
def schedule_campaign(campaign_id):
    """Schedule campaign for later."""
    try:
        from src.campaign_database import get_campaign, update_campaign_status
        
        data = request.get_json()
        scheduled_at = data.get('scheduled_at')
        
        if not scheduled_at:
            return jsonify({"error": "scheduled_at is required"}), 400
        
        campaign = get_campaign(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        # TODO: Implement scheduler to send at scheduled_at time
        # For now, just update status to scheduled
        update_campaign_status(campaign_id, 'scheduled')
        
        return jsonify({"ok": True, "status": "Campaign scheduled", "scheduled_at": scheduled_at})
    except Exception as exc:
        app.logger.exception("Schedule campaign failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/campaigns/<campaign_id>/preview", methods=["GET"])
def preview_campaign(campaign_id):
    """Get campaign preview."""
    try:
        from src.campaign_database import get_campaign, get_campaign_recipients
        from src.campaign_sender import TemplateParser
        
        campaign = get_campaign(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        recipients = get_campaign_recipients(campaign_id, status='pending')
        
        # Get first recipient for preview
        preview_recipient = recipients[0] if recipients else {'email': 'example@test.com', 'name': 'John'}
        
        personal_data = {
            'email': preview_recipient.get('email', ''),
            'name': preview_recipient.get('name', 'there'),
        }
        
        # Personalize preview
        subject_preview = TemplateParser.parse(campaign['subject'], personal_data)
        body_preview = TemplateParser.parse(campaign['body'], personal_data)
        
        return jsonify({
            "campaign_id": campaign_id,
            "name": campaign['name'],
            "subject": subject_preview,
            "body": body_preview,
            "sender_email": campaign['sender_email'],
            "recipient_count": campaign['recipient_count'],
            "speed_setting": campaign['speed_setting']
        })
    except Exception as exc:
        app.logger.exception("Preview campaign failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/campaigns/<campaign_id>/stats", methods=["GET"])
def campaign_stats(campaign_id):
    """Get detailed campaign statistics."""
    try:
        from src.campaign_database import get_campaign, get_campaign_stats, get_campaign_recipients
        
        campaign = get_campaign(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        stats = get_campaign_stats(campaign_id)
        
        # Get failed recipients with error messages
        failed_recipients = get_campaign_recipients(campaign_id, status='failed')
        
        return jsonify({
            **stats,
            "status": campaign['status'],
            "started_at": campaign['started_at'],
            "completed_at": campaign['completed_at'],
            "failed_details": [
                {"email": r['email'], "error": r['error_message']}
                for r in failed_recipients[:20]  # Limit to 20
            ]
        })
    except Exception as exc:
        app.logger.exception("Campaign stats failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/campaigns/<campaign_id>/delete", methods=["DELETE"])
def delete_campaign(campaign_id):
    """Delete campaign (only if draft)."""
    try:
        from src.campaign_database import get_campaign, update_campaign_status
        
        campaign = get_campaign(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        if campaign['status'] != 'draft':
            return jsonify({"error": f"Cannot delete campaign with status '{campaign['status']}'"}), 400
        
        # Mark as deleted
        update_campaign_status(campaign_id, 'deleted')
        
        return jsonify({"ok": True, "message": "Campaign deleted"})
    except Exception as exc:
        app.logger.exception("Delete campaign failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/api/campaigns/<campaign_id>/recipients/import", methods=["POST"])
def import_recipients(campaign_id):
    """Import recipients from CSV or paste list."""
    try:
        from src.campaign_database import get_campaign, add_campaign_recipient
        import csv
        import io
        import uuid
        
        data = request.get_json()
        
        campaign = get_campaign(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        # Handle CSV data
        csv_text = data.get('csv_text')
        if csv_text:
            reader = csv.DictReader(io.StringIO(csv_text))
            added = 0
            errors = []
            
            for row in reader:
                email = row.get('email', '').strip()
                name = row.get('name', '').strip()
                
                if not email:
                    errors.append("Empty email in row")
                    continue
                
                recipient_id = str(uuid.uuid4())
                add_campaign_recipient(
                    recipient_id=recipient_id,
                    campaign_id=campaign_id,
                    email=email,
                    name=name
                )
                added += 1
            
            return jsonify({"ok": True, "added": added, "errors": errors})
        
        return jsonify({"error": "No CSV data provided"}), 400
    except Exception as exc:
        app.logger.exception("Import recipients failed")
        return jsonify({"error": str(exc)}), 500


# Initialize scheduler when app starts
with app.app_context():
    init_scheduler()


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
