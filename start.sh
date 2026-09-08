#!/bin/bash

echo "🚀 Starting CompanyMind AI Platform (Production)"
echo "=============================================="

# Initialize databases
python -c "from src.email_database import init_email_db; init_email_db()"
python -c "from src.platform_db import init_platform_db; init_platform_db()"

echo "✅ Databases initialized"

# Start services with gunicorn
echo "Starting services..."

# Email Dashboard
gunicorn -w 4 -b 0.0.0.0:5000 src.dashboard.app:app &

# Platform Gateway
gunicorn -w 4 -b 0.0.0.0:5001 src.platform_gateway:create_gateway_app() &

# Admin Panel
gunicorn -w 4 -b 0.0.0.0:5002 src.admin.app:app &

echo "✅ All services running!"
echo ""
echo "📊 Email Dashboard: http://localhost:5000"
echo "🔌 API Gateway: http://localhost:5001"
echo "⚙️  Admin Panel: http://localhost:5002"
echo ""

wait
