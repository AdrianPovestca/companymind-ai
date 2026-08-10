"""
Main entry point for the AI Email Support Agent.

Current flow:
    Raw email
        ↓
    Email parser
        ↓
    Database
        ↓
    Email analysis
        ↓
    Decision engine
        ↓
    Result
"""

import logging
from typing import Dict, Any

from src.email_parser import parse_email
from src.email_database import (
    init_email_db,
    save_email,
    get_email,
    update_email_status,
)
from src.email_decision import decide_action


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def analyze_email(email) -> Any:
    """
    Analyze an email and return the analysis result.

    This function keeps the current demo analysis logic.
    The AI analysis layer can be expanded later.
    """

    body = email.body.lower()
    subject = email.subject.lower()

    combined_text = f"{subject} {body}"

    # Basic intent detection for the current demo.
    if any(
        word in combined_text
        for word in ["order", "delivery", "shipping", "package"]
    ):
        intent = "customer_support"
    elif any(
        word in combined_text
        for word in ["refund", "money back", "reimbursement"]
    ):
        intent = "customer_support"
    elif any(
        word in combined_text
        for word in ["password", "login", "account"]
    ):
        intent = "customer_support"
    else:
        intent = "customer_support"

    # Basic urgency detection.
    if any(
        word in combined_text
        for word in ["urgent", "immediately", "asap", "emergency"]
    ):
        urgency = "urgent"
    else:
        urgency = "normal"

    # Current demo rule.
    requires_human = False

    return EmailAnalysis(
        intent=intent,
        issue=email.body,
        urgency=urgency,
        language="unknown",
        requires_human=requires_human,
    )


class EmailAnalysis:
    """Stores the result of email analysis."""

    def __init__(
        self,
        intent: str,
        issue: str,
        urgency: str,
        language: str,
        requires_human: bool,
    ):
        self.intent = intent
        self.issue = issue
        self.urgency = urgency
        self.language = language
        self.requires_human = requires_human


def process_email(raw_email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process one incoming email through the complete current pipeline.

    Flow:
        raw email
        → parse
        → save
        → analyze
        → decide action
        → update status
    """

    # 1. Parse raw email.
    email = parse_email(raw_email)

    logger.info(
        f"Processing email {email.message_id} from {email.sender}"
    )

    # 2. Save email to database.
    save_email(email)

    # 3. Analyze email.
    analysis = analyze_email(email)

    logger.info(
        f"Email analyzed: intent={analysis.intent} "
        f"urgency={analysis.urgency} "
        f"human={analysis.requires_human}"
    )

    # 4. Decide what the agent should do.
    decision = decide_action(
        intent=analysis.intent,
        urgency=analysis.urgency,
        requires_human=analysis.requires_human,
    )

    logger.info(
        f"Email decision: action={decision.action} "
        f"reason={decision.reason}"
    )

    # 5. Update database status.
    update_email_status(
        email.message_id,
        decision.action,
    )

    # 6. Load thread history.
    thread = get_thread_messages(email.thread_id)

    return {
        "email": email,
        "analysis": analysis,
        "decision": decision,
        "action": decision.action,
        "thread": thread,
    }


def get_thread_messages(thread_id: str):
    """
    Return messages belonging to a thread.

    Thread memory will be expanded later when we build
    the full email memory system.
    """

    return [
        {
            "thread_id": thread_id,
        }
    ]


def main() -> None:
    """Run a demo email through the agent."""

    init_email_db()

    raw_email = {
        "message_id": "demo-002",
        "thread_id": "demo-thread-002",
        "sender": "customer@example.com",
        "recipient": "support@example.com",
        "subject": "Order issue",
        "body": (
            "Hi, I placed my order five days ago and I still "
            "haven't received it. Can you help?"
        ),
        "timestamp": "2026-08-10T09:30:00",
        "attachments": [],
    }

    result = process_email(raw_email)

    print("\n" + "=" * 60)
    print("EMAIL AGENT RESULT")
    print("=" * 60)

    print(f"\nMessage ID: {result['email'].message_id}")
    print(f"Intent: {result['analysis'].intent}")
    print(f"Urgency: {result['analysis'].urgency}")
    print(f"Language: {result['analysis'].language}")
    print(f"Requires human: {result['analysis'].requires_human}")
    print(f"Action: {result['action']}")
    print(f"Thread messages: {len(result['thread'])}")

    print("=" * 60)


if __name__ == "__main__":
    main()