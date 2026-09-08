"""
Platform Admin Panel
Manage businesses, users, API keys, knowledge base, agents
"""

import sys
sys.path.insert(0, '/workspaces/companymind-ai')

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
from src.platform_db import (
    get_platform_connection, create_business, create_user, 
    create_api_key, add_knowledge_base, enable_agent, 
    get_business, get_business_agents
)

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)
CORS(app)

# ===== DASHBOARD =====
@app.route('/')
def dashboard():
    """Admin dashboard"""
    return render_template('dashboard.html')

# ===== BUSINESSES =====
@app.route('/api/admin/businesses', methods=['GET'])
def list_businesses():
    """List all businesses"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, slug, description, created_at FROM businesses ORDER BY created_at DESC")
        businesses = cursor.fetchall()
        conn.close()
        return jsonify([dict(b) for b in businesses])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/businesses', methods=['POST'])
def create_business_endpoint():
    """Create new business"""
    try:
        data = request.json
        name = data.get('name')
        slug = data.get('slug')
        description = data.get('description', '')
        
        if not name or not slug:
            return jsonify({'error': 'Name and slug required'}), 400
        
        bid = create_business(name, slug, description)
        if not bid:
            return jsonify({'error': 'Business already exists'}), 400
        
        return jsonify({'id': bid, 'name': name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/businesses/<int:bid>', methods=['GET'])
def get_business_endpoint(bid):
    """Get business details"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM businesses WHERE id = ?", (bid,))
        business = cursor.fetchone()
        conn.close()
        
        if not business:
            return jsonify({'error': 'Not found'}), 404
        
        return jsonify(dict(business))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== USERS =====
@app.route('/api/admin/businesses/<int:bid>/users', methods=['GET'])
def get_users(bid):
    """Get users for business"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, role, is_active, created_at FROM users WHERE business_id = ?", (bid,))
        users = cursor.fetchall()
        conn.close()
        return jsonify([dict(u) for u in users])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/businesses/<int:bid>/users', methods=['POST'])
def create_user_endpoint(bid):
    """Create user for business"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        # TODO: Hash password
        uid = create_user(bid, email, password, role)
        if not uid:
            return jsonify({'error': 'User already exists'}), 400
        
        return jsonify({'id': uid, 'email': email})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== API KEYS =====
@app.route('/api/admin/businesses/<int:bid>/api-keys', methods=['GET'])
def get_api_keys(bid):
    """Get API keys for business"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, key, name, is_active, created_at FROM api_keys WHERE business_id = ?", (bid,))
        keys = cursor.fetchall()
        conn.close()
        return jsonify([dict(k) for k in keys])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/businesses/<int:bid>/api-keys', methods=['POST'])
def create_api_key_endpoint(bid):
    """Generate API key"""
    try:
        import secrets
        data = request.json
        name = data.get('name', 'API Key')
        
        key = f"sk-{secrets.token_hex(32)}"
        create_api_key(bid, key, name)
        
        return jsonify({'key': key, 'name': name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== KNOWLEDGE BASE =====
@app.route('/api/admin/businesses/<int:bid>/knowledge-base', methods=['GET'])
def get_kb(bid):
    """Get knowledge base"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, category, created_at FROM knowledge_base WHERE business_id = ? ORDER BY created_at DESC", (bid,))
        docs = cursor.fetchall()
        conn.close()
        return jsonify([dict(d) for d in docs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/businesses/<int:bid>/knowledge-base', methods=['POST'])
def add_kb(bid):
    """Add knowledge document"""
    try:
        data = request.json
        title = data.get('title')
        content = data.get('content')
        category = data.get('category', 'general')
        
        if not title or not content:
            return jsonify({'error': 'Title and content required'}), 400
        
        doc_id = add_knowledge_base(bid, title, content, category)
        if not doc_id:
            return jsonify({'error': 'Failed to add'}), 500
        
        return jsonify({'id': doc_id, 'title': title})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== AGENTS =====
@app.route('/api/admin/businesses/<int:bid>/agents', methods=['GET'])
def get_agents_config(bid):
    """Get agent configs"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT agent_name, is_enabled, config_json FROM agent_configs WHERE business_id = ?", (bid,))
        agents = cursor.fetchall()
        conn.close()
        return jsonify([dict(a) for a in agents])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/businesses/<int:bid>/agents/<agent_name>', methods=['POST'])
def toggle_agent(bid, agent_name):
    """Enable/disable agent"""
    try:
        data = request.json
        enabled = data.get('enabled', True)
        config = data.get('config', '{}')
        
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE agent_configs 
            SET is_enabled = ?, config_json = ?
            WHERE business_id = ? AND agent_name = ?
        """, (1 if enabled else 0, config, bid, agent_name))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== AUDIT LOG =====
@app.route('/api/admin/businesses/<int:bid>/audit-log', methods=['GET'])
def get_audit_log(bid):
    """Get audit log"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, action, resource, details, created_at
            FROM audit_log
            WHERE business_id = ?
            ORDER BY created_at DESC
            LIMIT 100
        """, (bid,))
        logs = cursor.fetchall()
        conn.close()
        return jsonify([dict(l) for l in logs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== STATS =====
@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    """Get platform statistics"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM businesses")
        businesses = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        docs = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'businesses': businesses,
            'users': users,
            'documents': docs
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("✅ Admin Panel starting on http://0.0.0.0:5002")
    app.run(debug=True, host='0.0.0.0', port=5002)
