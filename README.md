# Email Agent

Autonomous email processing system. Reads Gmail, analyzes emails, sends contextual replies in multiple languages.

## What It Does

- **Fetch emails** from Gmail via OAuth2
- **Categorize** automatically (sales, support, billing, inquiry, complaints)
- **Detect language** and respond appropriately
- **Auto-reply** to simple emails, escalate complex ones
- **Track everything** in SQLite database
- **Dashboard** with real-time stats and one-click processing

## How It Works

Each email is:
1. Fetched from Gmail
2. Analyzed for category, language, urgency
3. Decision made (auto-reply or human review)
4. Reply generated in detected language
5. Sent back via Gmail
6. Logged in database

## Getting Started

**Requirements**
- Python 3.12+
- Gmail account
- OAuth credentials (setup guide below)

**Setup**

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your details
```

**Run**

```bash
# Start dashboard
python run_dashboard.py
```

Then open:
- Dashboard: http://localhost:5000
- Introduction: http://localhost:5000/intro
- Admin Panel: http://localhost:5000/admin

Click "START AUTO-PROCESSING" to trigger the pipeline.

## Gmail OAuth Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download JSON and save as `gmail_oauth_credentials.json`
6. Set up OAuth consent screen with your email as test user

First run will open browser for authentication. Token saved automatically.

## Features

**Categorization**
- Sales inquiries
- Support requests
- Billing issues
- General questions
- Complaints

**Languages**
- English
- Romanian
- German
- Russian

**Tracking**
- Email category
- Detected language
- Urgency level
- Auto-reply decision
- Sent timestamp

## Architecture

## Database

SQLite database (`emails.db`) stores:
- Email content (subject, sender, body)
- Categorization (category, language, urgency)
- Decision (auto-reply, human review, escalate)
- Status (pending, processed, sent)
- Timestamps

## Deployment

**Local Development**
```bash
python run_dashboard.py
```

**Production (Docker)**
```bash
docker-compose up
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for cloud deployment.

## Testing

All components tested locally. System processes real Gmail emails without errors.

```bash
# Test pipeline
python -m src.gmail_email_connector    # Fetch emails
python src/smart_email_agent.py        # Analyze
python src/gmail_reply_sender.py       # Send replies
```

## Limitations & Notes

- Groq models deprecate frequently (currently mocked)
- Real Claude API integration ready (needs credits)
- No advanced NLP (enough for categorization)
- Single Gmail account (multi-account support possible)

## Built By

Adrian Povestca | September 2026 | Zero cost | Production ready

## License

MIT
