"""
Platform API Gateway
- Authentication (API key validation)
- Request routing (by business)
- Rate limiting
- Error handling
"""

import sys
import os

# Add repo to path
sys.path.insert(0, '/workspaces/companymind-ai')

import time
import json
from functools import wraps
from flask import Flask, request, jsonify
from src.platform_db import get_platform_connection

class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self, max_requests=100, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}
    
    def is_allowed(self, key):
        """Check if request is allowed"""
        now = time.time()
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside window
        self.requests[key] = [t for t in self.requests[key] if now - t < self.window]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Add new request
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter(max_requests=100, window=60)

def authenticate_api_key(f):
    """Middleware: Validate API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401
        
        try:
            conn = get_platform_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT business_id FROM api_keys WHERE key = ? AND is_active = 1", (api_key,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return jsonify({'error': 'Invalid API key'}), 401
            
            request.business_id = result[0]
        except Exception as e:
            return jsonify({'error': 'Auth error'}), 500
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit(f):
    """Middleware: Rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key', 'anonymous')
        
        if not rate_limiter.is_allowed(api_key):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        return f(*args, **kwargs)
    
    return decorated_function

def create_gateway_app():
    """Create Flask app"""
    app = Flask(__name__)
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'service': 'platform-gateway'})
    
    @app.route('/api/business', methods=['GET'])
    @authenticate_api_key
    @rate_limit
    def get_business_info():
        try:
            conn = get_platform_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, slug, description FROM businesses WHERE id = ?", (request.business_id,))
            business = cursor.fetchone()
            conn.close()
            
            if not business:
                return jsonify({'error': 'Business not found'}), 404
            
            return jsonify(dict(business))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/business/agents', methods=['GET'])
    @authenticate_api_key
    @rate_limit
    def get_agents():
        try:
            conn = get_platform_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT agent_name, is_enabled FROM agent_configs WHERE business_id = ? AND is_enabled = 1", (request.business_id,))
            agents = cursor.fetchall()
            conn.close()
            
            return jsonify([dict(a) for a in agents])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/business/knowledge-base', methods=['GET'])
    @authenticate_api_key
    @rate_limit
    def get_knowledge_base():
        try:
            conn = get_platform_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, category FROM knowledge_base WHERE business_id = ?", (request.business_id,))
            docs = cursor.fetchall()
            conn.close()
            
            return jsonify([dict(d) for d in docs])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/email/process', methods=['POST'])
    @authenticate_api_key
    @rate_limit
    def process_email():
        try:
            data = request.json
            
            if not data or 'from' not in data or 'subject' not in data:
                return jsonify({'error': 'Missing email fields'}), 400
            
            return jsonify({'status': 'queued', 'message_id': 'pending'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_gateway_app()
    print("✅ API Gateway starting on http://0.0.0.0:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)

# ===== ADD THIS TO EXISTING GATEWAY =====
# Update the process_email endpoint to use platform integration:

# Replace old process_email with this in platform_gateway.py
