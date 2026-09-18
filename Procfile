web: gunicorn --bind 0.0.0.0:$PORT run_dashboard:app
worker: python -m src.gmail_reply_sender
notify: while true; do python -m src.notifications; sleep 120; done
