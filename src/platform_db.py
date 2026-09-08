"""
Platform Layer Database Schema
Multi-tenant support for all agents
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv('PLATFORM_DB_PATH', 'platform.db')

def get_platform_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_platform_db():
    """Initialize platform database schema"""
    conn = get_platform_connection()
    cursor = conn.cursor()
    
    # 1. BUSINESSES TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            email_provider TEXT,
            email_config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(business_id) REFERENCES businesses(id)
        )
    """)
    
    # 3. API KEYS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            key TEXT UNIQUE NOT NULL,
            name TEXT,
            last_used TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(business_id) REFERENCES businesses(id)
        )
    """)
    
    # 4. KNOWLEDGE BASE TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(business_id) REFERENCES businesses(id)
        )
    """)
    
    # 5. AGENT CONFIGS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            is_enabled BOOLEAN DEFAULT 1,
            config_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(business_id) REFERENCES businesses(id),
            UNIQUE(business_id, agent_name)
        )
    """)
    
    # 6. AUDIT LOG TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(business_id) REFERENCES businesses(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Platform database initialized")

def create_business(name, slug, description=""):
    """Create a new business"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO businesses (name, slug, description)
            VALUES (?, ?, ?)
        """, (name, slug, description))
        conn.commit()
        business_id = cursor.lastrowid
        conn.close()
        print(f"✅ Business created: {name} (ID: {business_id})")
        return business_id
    except sqlite3.IntegrityError:
        print(f"❌ Business '{name}' already exists")
        return None

def create_user(business_id, email, password_hash, role="user"):
    """Create a new user"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (business_id, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, (business_id, email, password_hash, role))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        print(f"✅ User created: {email} (ID: {user_id})")
        return user_id
    except sqlite3.IntegrityError:
        print(f"❌ User '{email}' already exists")
        return None

def create_api_key(business_id, key, name=""):
    """Create API key for business"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO api_keys (business_id, key, name)
            VALUES (?, ?, ?)
        """, (business_id, key, name))
        conn.commit()
        conn.close()
        print(f"✅ API key created for business {business_id}")
        return True
    except sqlite3.IntegrityError:
        print(f"❌ API key already exists")
        return False

def add_knowledge_base(business_id, title, content, category="general"):
    """Add knowledge base document"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO knowledge_base (business_id, title, content, category)
            VALUES (?, ?, ?, ?)
        """, (business_id, title, content, category))
        conn.commit()
        doc_id = cursor.lastrowid
        conn.close()
        print(f"✅ Knowledge base document added (ID: {doc_id})")
        return doc_id
    except Exception as e:
        print(f"❌ Error adding document: {e}")
        return None

def enable_agent(business_id, agent_name, config_json="{}"):
    """Enable agent for business"""
    try:
        conn = get_platform_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agent_configs (business_id, agent_name, is_enabled, config_json)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(business_id, agent_name) DO UPDATE SET is_enabled = 1
        """, (business_id, agent_name, config_json))
        conn.commit()
        conn.close()
        print(f"✅ Agent '{agent_name}' enabled for business {business_id}")
        return True
    except Exception as e:
        print(f"❌ Error enabling agent: {e}")
        return False

def get_business(business_id):
    """Get business details"""
    conn = get_platform_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))
    business = cursor.fetchone()
    conn.close()
    return dict(business) if business else None

def get_business_by_slug(slug):
    """Get business by slug"""
    conn = get_platform_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM businesses WHERE slug = ?", (slug,))
    business = cursor.fetchone()
    conn.close()
    return dict(business) if business else None

def get_business_agents(business_id):
    """Get all agents for business"""
    conn = get_platform_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT agent_name, is_enabled, config_json
        FROM agent_configs
        WHERE business_id = ?
    """, (business_id,))
    agents = cursor.fetchall()
    conn.close()
    return [dict(a) for a in agents]

if __name__ == '__main__':
    # Test the schema
    init_platform_db()
    
    # Create test business
    bid = create_business("Acme Corp", "acme-corp", "Test e-commerce business")
    
    if bid:
        # Create test user
        create_user(bid, "admin@acme.com", "hashed_password", "admin")
        
        # Create API key
        create_api_key(bid, "sk-test-12345", "Test Key")
        
        # Add knowledge base
        add_knowledge_base(bid, "Return Policy", "30-day money back guarantee", "policies")
        
        # Enable agents
        enable_agent(bid, "email-agent", '{"provider": "gmail"}')
        enable_agent(bid, "miri-support", '{"model": "gpt-4"}')
        
        # Verify
        business = get_business(bid)
        agents = get_business_agents(bid)
        
        print("\n✅ Test business created:")
        print(f"   Name: {business['name']}")
        print(f"   Agents: {len(agents)}")
        for agent in agents:
            print(f"     - {agent['agent_name']}: {'enabled' if agent['is_enabled'] else 'disabled'}")
