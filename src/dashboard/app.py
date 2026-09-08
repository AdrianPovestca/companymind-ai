from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys
sys.path.insert(0, '/workspaces/companymind-ai')
from src.email_database import get_connection

app = Flask(__name__)
app.template_folder = '/workspaces/companymind-ai/src/dashboard/templates'
app.static_folder = '/workspaces/companymind-ai/src/static'
app.static_url_path = '/static'
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats', methods=['GET'])
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
        return jsonify({'auto_replied': auto, 'pending': pending, 'total': total})
    except:
        return jsonify({'error': 'DB error'}), 500

@app.route('/api/pending-emails', methods=['GET'])
def get_pending():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, subject, sender, body FROM emails WHERE decision_action IN ('human_review', 'escalate') LIMIT 50")
        emails = cursor.fetchall()
        conn.close()
        return jsonify([{'id': e[0], 'subject': e[1], 'sender': e[2], 'body': e[3]} for e in emails])
    except:
        return jsonify([]), 500

@app.route('/api/email/<email_id>', methods=['GET'])
def get_email(email_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, subject, sender, body, created_at FROM emails WHERE id = ?", (email_id,))
        e = cursor.fetchone()
        conn.close()
        if not e:
            return jsonify({}), 404
        return jsonify({'id': e[0], 'subject': e[1], 'sender': e[2], 'body': e[3], 'created_at': e[4]})
    except:
        return jsonify({}), 500

@app.route('/api/email/<email_id>/approve', methods=['POST'])
def approve(email_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE emails SET decision_action = 'approved' WHERE id = ?", (email_id,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    except:
        return jsonify({'ok': False}), 500

@app.route('/api/email/<email_id>/reject', methods=['POST'])
def reject(email_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE emails SET decision_action = 'escalate' WHERE id = ?", (email_id,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    except:
        return jsonify({'ok': False}), 500

if __name__ == '__main__':
    print("✅ Dashboard running on http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
