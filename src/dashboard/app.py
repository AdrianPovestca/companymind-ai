from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from pathlib import Path
import sys
sys.path.insert(0, '/workspaces/companymind-ai')
from src.email_database import get_connection

app = Flask(__name__)
app.template_folder = str(Path(__file__).resolve().parent / 'templates')
app.static_folder = str(Path(__file__).resolve().parent.parent / 'static')
app.static_url_path = '/static'
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')

@app.route('/review')
def review_dashboard():
    return render_template('review.html')

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM emails WHERE decision_urgency = 'high'")
        pending = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM emails WHERE status = 'sent_reply_sent'")
        auto_replied = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM emails")
        total = cursor.fetchone()[0]
        conn.close()
        return jsonify({'pending': pending, 'auto_replied': auto_replied, 'total': total})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-emails', methods=['POST'])
def process_emails():
    try:
        import subprocess
        subprocess.run(['python', 'src/smart_email_agent.py'], capture_output=True)
        subprocess.run(['python', 'src/gmail_reply_sender.py'], capture_output=True)
        return jsonify({'message': 'Processing complete'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/human-review-queue')
def human_review_queue():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, sender, subject, body 
            FROM emails 
            WHERE decision_urgency = 'high'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        emails = cursor.fetchall()
        conn.close()
        return jsonify({'emails': [{'message_id': e[0], 'sender': e[1], 'subject': e[2], 'body': e[3]} for e in emails]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/email/<msg_id>/resolve', methods=['POST'])
def resolve_email(msg_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE emails SET status = 'human_resolved' WHERE message_id = ?", (msg_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
