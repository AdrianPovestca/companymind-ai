import os
import sys
sys.path.insert(0, '/workspaces/companymind-ai')

from src.dashboard.app import app

if __name__ == '__main__':
    # Codespaces requires 0.0.0.0
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)
