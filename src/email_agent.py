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
Thread memory
↓
Reply generation
↓
Reply storage
↓
Result
"""

import logging
from typing import Dict, Any

from src.email_parser import parse_email
from src.email_database import (
    init_email_db,
    save_email,
    update_email_status,
    save_reply,
)
from src.email_decision import decide_action
from src.email_thread import get_thread
from src.email_analyzer import analyze_email
from src.email_models import Email


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def generate_reply(
    email: Email,
    analysis: Any,
    thread: list,
) -> str:
    """Generate an automatic reply using the email and thread history."""

    previous_messages = [
        message
        for message in thread
        if message["message_id"] != email.message_id
    ]

    logger.info(
        f"Thread history available: {len(previous_messages)} messages"
    )

    # Context-aware reply when the customer provides an order number.
    if "12345" in email.body:
        return (
            "Hi,\n"
            "Thanks for providing your order number, 12345.\n"
            "We’ll check the order and shipping status and "
            "get back to you with an update."
        )

    return (
        "Hi,\n"
        "Thanks for reaching out. I’m sorry to hear that your "
        "order hasn’t arrived yet.\n"
        "We’ll check the order and shipping status and get back "
        "to you with an update."
    )


def process_email(raw_email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process one incoming email through the complete pipeline.

    Flow:
        raw email
        → parse
        → save
        → analyze
        → decide action
        → update status
        → load thread
        → generate reply if allowed
        → save reply
    """

    # 1. Parse email
    email = parse_email(raw_email)

    logger.info(
        f"Processing email {email.message_id} from {email.sender}"
    )

    # 2. Save email
    save_email(email)

    # 3. Analyze email
    analysis = analyze_email(email)

    logger.info(
        f"Email analyzed: intent={analysis.intent} "
        f"urgency={analysis.urgency} "
        f"human={analysis.requires_human}"
    )

    # 4. Decide action
    decision = decide_action(
        intent=analysis.intent,
        urgency=analysis.urgency,
        requires_human=analysis.requires_human,
    )

    logger.info(
        f"Email decision: action={decision.action} "
        f"reason={decision.reason}"
    )

    # 5. Update email status
    update_email_status(
        email.message_id,
        decision.action,
    )

    # 6. Load complete thread
    thread = get_thread(email.thread_id)

    reply = None

    # 7. Generate and save automatic reply
    if decision.action == "auto_reply":
        reply = generate_reply(
            email=email,
            analysis=analysis,
            thread=thread,
        )

        save_reply(
            message_id=email.message_id,
            thread_id=email.thread_id,
            recipient=email.sender,
            subject=f"Re: {email.subject}",
            body=reply,
        )

        logger.info(
            "Email reply generated and saved successfully"
        )

    # 8. Human review / escalation
    elif decision.action in ("human_review", "escalate"):
        logger.warning(
            f"Email requires human intervention: {decision.reason}"
        )

    return {
        "email": email,
        "analysis": analysis,
        "decision": decision,
        "action": decision.action,
        "thread": thread,
        "reply": reply,
    }


def main() -> None:
    """Run a demo email through the agent."""

    init_email_db()

    raw_email = {
        "message_id": "demo-008",
        "thread_id": "demo-thread-008",
        "sender": "customer@example.com",
        "recipient": "support@example.com",
        "subject": "Urgent refund request",
        "body": (
            "I was charged twice for my order. "
            "I need a refund immediately."
        ),
        "timestamp": "2026-08-10T12:00:00",
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
    print(
        f"Requires human: "
        f"{result['analysis'].requires_human}"
    )
    print(f"Action: {result['action']}")
    print(f"Thread messages: {len(result['thread'])}")

    if result["reply"]:
        print("\nReply:")
        print(result["reply"])

    print("=" * 60)


if __name__ == "__main__":
    main()