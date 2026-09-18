import os
from apscheduler.schedulers.background import BackgroundScheduler
from src.dashboard.app import app
from src.gmail_reply_sender import send_replies
from src.notifications import check_and_notify


def start_scheduler():
    """Start background scheduler for email processing and notifications."""
    scheduler = BackgroundScheduler()
    
    # Job 1: Send email replies every 2 minutes
    scheduler.add_job(
        func=send_replies,
        trigger="interval",
        minutes=2,
        id="email_reply_job",
        name="Send email replies",
        replace_existing=True,
        max_instances=1
    )
    
    # Job 2: Check and send Telegram notifications every 2 minutes
    scheduler.add_job(
        func=check_and_notify,
        trigger="interval",
        minutes=2,
        id="notification_job",
        name="Send Telegram notifications",
        replace_existing=True,
        max_instances=1
    )
    
    scheduler.start()
    print("✅ Background scheduler started - jobs running every 2 minutes")
    
    return scheduler


if __name__ == "__main__":
    # Start background scheduler
    scheduler = start_scheduler()
    
    try:
        app.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", "5000")),
            debug=False,
        )
    except KeyboardInterrupt:
        scheduler.shutdown()
