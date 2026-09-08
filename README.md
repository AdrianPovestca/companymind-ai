# Email Agent

Intelligent email processing engine that automatically handles customer emails, detects intent, and routes them appropriately.

## Features

- **Automatic Email Processing** — Fetch, parse, and analyze emails
- **Smart Intent Detection** — Support requests, refunds, complaints, urgent issues
- **Intelligent Routing** — Auto-reply to simple cases, escalate complex ones to humans
- **Multi-Language Support** — 25+ languages (EN, RO, ES, FR, DE, JA, ZH, KO...)
- **Thread Memory** — Maintains conversation history
- **Persistent Storage** — SQLite database for email history and decisions

## How It Works

## Supported Email Providers

- **Mock** — Testing & demos
- **Yahoo Mail** — IMAP/SMTP
- **Outlook** — Microsoft Graph API
- **Gmail** — OAuth2 (setup guide included)

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your email provider

# Process emails
python -c "from src.agent_factory import create_email_agent; from src.email_agent import process_unread_emails; connector = create_email_agent(); process_unread_emails(connector)"
```

## Languages Supported

English, Română, Español, Français, Deutsch, Italiano, Português, Nederlands, Polski, Русский, Türkçe, 日本語, 中文, 한국어, العربية, हिन्दी, Tiếng Việt, ไทย, Bahasa Indonesia, Bahasa Melayu, Filipino, Українська, Čeština, Magyar, Ελληνικά

## Architecture

- **email_parser.py** — Extract email data
- **email_analyzer.py** — Analyze intent & urgency
- **email_decision.py** — Routing logic
- **email_smart_responder.py** — Template-based replies (25+ languages)
- **email_database.py** — Persistence
- **email_connector.py** — Provider abstraction
- **email_provider_registry.py** — Extensible provider system

## Testing

```bash
python -m pytest -v
# 30/30 tests passing
```

## What's Built

✅ Email parsing & analysis
✅ Intent detection (support/refund/complaint/urgent)
✅ Decision engine (auto/review/escalate)
✅ 25+ language templates
✅ Database + thread memory
✅ 4 email connectors
✅ 100% test coverage

## What's Not Built

❌ Claude AI (code ready for integration)
❌ Web dashboard
❌ Gmail OAuth2 final setup
❌ Multi-tenant platform

## Status

**v1.0 — Production-ready MVP**

- Zero cost to operate
- Ready for customer demos & deployment
- 30/30 tests passing
- 25+ languages supported

## Part of CompanyMind Platform

Agent #2 in the AI agents ecosystem:
- Agent #1: Miri (Customer Support) ✅
- Agent #2: Email Agent ✅
- Agent #3+: Coming soon

---

Built by Adrian | 1 week | $0 cost | Production ready
