# Email Agent 🤖

**Intelligent email processing engine for business automation.** Part of the **CompanyMind AI Platform**.

This is **Agent #2** in the platform ecosystem. It processes incoming emails, analyzes intent, makes decisions, and generates intelligent responses — all while learning business context and maintaining thread memory.

---

## 📋 What It Does

```
Incoming Email
    ↓
Parse & Extract
    ↓
Analyze Intent (support, refund, complaint, etc.)
    ↓
Determine Urgency
    ↓
Decision Engine
    ├── Auto-reply (simple cases)
    ├── Human Review (complex/sensitive)
    ├── Escalate (urgent/critical)
    └── Ignore (irrelevant)
    ↓
Database Storage + Thread Memory
    ↓
Action (Reply sent / Review queue / Escalation)
```

---

## 🏗️ Architecture

### Core Components

```
src/
├── email_models.py           # Data structures
├── email_parser.py           # Parse raw emails
├── email_analyzer.py         # Intent/urgency analysis
├── email_decision.py         # Decision logic (auto/review/escalate)
├── email_responder.py        # Generate replies
├── email_connector.py         # Provider abstraction (Gmail, Yahoo, Outlook)
├── email_database.py         # SQLite persistence
├── email_thread.py           # Thread memory
└── email_agent.py            # Main orchestrator
```

### Decision Flow

```
EmailConnector (abstract)
    ├── MockEmailConnector    (testing)
    ├── GmailEmailConnector   (todo)
    ├── YahooEmailConnector   (todo)
    └── OutlookEmailConnector (todo)
```

**Business → Email Agent → Email Provider → Reply**

---

## ⚙️ Setup

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/companymind-ai.git
cd companymind-ai
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run Tests

```bash
python -m pytest -v
```

**Expected:** 30/30 PASSED ✅

### 4. Run Agent (Local/Mock)

```bash
python -c "from src.email_agent import EmailAgent; from src.email_connector import MockEmailConnector; agent = EmailAgent(MockEmailConnector()); ..."
```

---

## 🔌 Email Providers

### Currently Supported

- **Mock** — Local testing (30/30 tests passing)

### Coming Soon

- **Gmail** — Google Workspace / Gmail API
- **Yahoo** — Yahoo Mail / IMAP
- **Outlook** — Microsoft 365 / Outlook API

### Add a New Provider

1. Create `src/providers/your_provider_connector.py`
2. Inherit `EmailConnector`
3. Implement:
   - `fetch_unread_emails()` → returns `List[Email]`
   - `mark_as_read(message_id)` → marks email as read
   - `send_reply(email_id, reply_text)` → sends response
4. Register in `src/email_provider_registry.py`
5. Add to `.env`: `EMAIL_PROVIDER=your_provider`

Example:
```python
from src.email_connector import EmailConnector

class GmailEmailConnector(EmailConnector):
    def fetch_unread_emails(self):
        # Gmail API call
        pass
    
    def mark_as_read(self, message_id):
        # Mark in Gmail
        pass
```

---

## 🧪 Testing

```bash
# All tests
python -m pytest -v

# Specific test file
python -m pytest tests/test_email_parser.py -v

# Specific test
python -m pytest tests/test_email_parser.py::test_customer_support_email -v

# With coverage
python -m pytest --cov=src tests/
```

**Current Status:** 30/30 PASSED ✅

---

## 💾 Database

SQLite database (`emails.db`) stores:

- **Emails** — Raw email data, parsed content, metadata
- **Replies** — Generated or sent responses
- **Decisions** — Decision metadata (intent, urgency, action)
- **Human Reviews** — Emails requiring owner approval
- **Threads** — Email conversation history

Auto-migration on first run.

---

## 🎯 Design Principles

1. **Provider Agnostic** — Works with any email service
2. **Modular** — Each component has one job
3. **Testable** — 100% test coverage target
4. **Safe** — Human review for sensitive cases
5. **Scalable** — Ready for platform integration

---

## 🗺️ Development Roadmap

### Phase 1 — Stabilization ✅
- [x] Core engine
- [x] 30/30 tests passing
- [x] Parser, analyzer, decision, responder
- [ ] Requirements.txt & .env
- [ ] Provider registry

### Phase 2 — Real Email Integration 🔨
- [ ] Gmail connector
- [ ] Yahoo connector
- [ ] Outlook connector
- [ ] Provider abstraction layer
- [ ] Config system per business

### Phase 3 — AI/LLM Integration
- [ ] Replace template responses with LLM
- [ ] Company knowledge base
- [ ] Context-aware replies
- [ ] Safety guardrails

### Phase 4 — Human Dashboard
- [ ] Web UI for owner review
- [ ] Approve/reject/reply interface
- [ ] Email archive & search
- [ ] Statistics & analytics

### Phase 5 — Platform Integration
- [ ] Multi-tenant support
- [ ] Shared memory/knowledge
- [ ] Business settings
- [ ] User permissions

### Phase 6 — Production
- [ ] Docker deployment
- [ ] Error recovery & retry
- [ ] Logging & monitoring
- [ ] Security & secrets management

---

## 🌍 Part of CompanyMind Platform

This Email Agent is one module in a larger AI platform:

```
                    PLATFORM
                       │
       ┌───────────────┼────────────────┐
       │               │                │
    Knowledge        Agents          Business
    Base             Control          Settings
       │               │                │
       │        ┌──────┼──────┐         │
       │        ↓      ↓      ↓         │
       │      Miri   Email  Messaging   │
       │    Support  Agent   Agent      │
       │                                │
       └────────── Memory ───────────────┘
```

**Miri AI** (Agent #1) — Customer Support chatbot ✅
**Email Agent** (Agent #2) — Email automation 🔨
**Messaging Agent** (Agent #3) — Chat/SMS handling ⏳
**Agent #4+** — Future agents ⏳

---

## 💰 SaaS Model

Customers subscribe per agent:

```
1 Agent     → €X/month
2 Agents    → €Y/month
All Agents  → €Z/month
```

No lock-in — pick what you need.

---

## 📝 License

[Your License Here]

---

## 👤 Author

Adrian — Building AI agents for business automation.

---

## 🤝 Contributing

1. Fork repo
2. Create feature branch: `git checkout -b feature/your-feature`
3. Write tests first
4. Commit & push
5. Create pull request

**Rule:** No code without tests. Aim for 100% coverage.

---

## ❓ FAQ

**Q: Can I use this with my email provider?**
A: If we have a connector (Gmail, Yahoo, Outlook), yes. Want to add one? See "Add a New Provider" above.

**Q: How do I train it on my business?**
A: Company knowledge integration coming in Phase 3. For now, it uses template responses.

**Q: What about privacy?**
A: Emails stored locally in SQLite. No data sent to external services unless you configure a provider API.

**Q: Can I integrate with other platforms?**
A: Yes — via the EmailConnector interface. We're building the platform layer to support this (Phase 5).

---

**Questions?** Open an issue or contact Adrian.
## 🚀 Current Status

**MVP COMPLETE:**
- ✅ Email parsing & analysis
- ✅ Auto-reply decision engine
- ✅ Human review for sensitive emails
- ✅ Database persistence
- ✅ Thread memory
- ✅ 30/30 tests passing
- ✅ Mock/Yahoo/Outlook connectors ready
- ✅ Provider registry for extensibility

**NEXT PHASE (Future):**
- Claude AI integration (needs API credits)
- Gmail OAuth2 completion
- Web dashboard
- Production deployment

