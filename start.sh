#!/bin/bash
set -e

echo "🚀 Starting CompanyMind AI Platform"

cd /app

# Install dependencies
pip install -r requirements.txt

# Initialize databases
python -c "from src.email_database import init_email_db; init_email_db()"
python -c "from src.platform_db import init_platform_db; init_platform_db()"

# Start services
python -m src.dashboard.app &
python -m src.platform_gateway &
python -m src.admin.app &

wait
