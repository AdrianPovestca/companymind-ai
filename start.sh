#!/bin/bash
cd /app
pip install -r requirements.txt
python -m src.dashboard.app
