"""
Main entry point for the AI Email Support Agent.

Flow:
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
Decision metadata
↓
Thread memory
↓
Email responder
↓
Reply storage
↓
Result

Connector flow:
EmailConnector
↓
fetch unread emails
↓
process_email()
↓
mark as read
"""

import logging
from typing import Any, Dict

from src.email_analyzer import analyze_email
from src.email_connector import EmailConnector
from src.email_database import (
    get_replies_for_thread,
    init_email_db,
    save_decision_metadata,
    save_email,
    save_reply,
    update_email_status,
)
from src.email_decision import decide_action
from src.email_models import Email
from src.email_parser import parse_email
from src.email_responder import generate_reply
from src.email_thread import get_thread


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def _has_reply_for_email(
    message_id: str,
    thread_id: str,
) -> bool:
    """
    Check whether the agent has already created a reply
    for the specified incoming email.
    """
    replies = get_replies_for_thread(thread_id)
    reply_prefix = f"reply-{message_id}"

    return any(
        str(reply.get("message_id", "")).startswith(reply_prefix)
        for reply in replies
    )


def process_email(
    raw_email: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Process one incoming email through the complete pipeline.

    Flow:
        raw email
        → parse
        → save
        → analyze
        → decide action
        → save decision metadata
        → load thread
        → generate reply if allowed
        → save reply
    """

    # 1. Parse incoming email
    email: Email = parse_email(raw_email)

    logger.info(
        "Processing email %s from %s",
        email.message_id,
        email.sender,
    )

    # 2. Save incoming email
    save_email(email)

    # 3. Analyze email
    analysis = analyze_email(email)

    logger.info(
        "Email analyzed: intent=%s urgency=%s human=%s",
        analysis.intent,
        analysis.urgency,
        analysis.requires_human,
    )

    # 4. Decide action
    decision = decide_action(
        intent=analysis.intent,
        urgency=analysis.urgency,
        requires_human=analysis.requires_human,
    )

    logger.info(
        "Email decision: action=%s reason=%s",
        decision.action,
        decision.reason,
    )

    # 5. Save decision metadata
    save_decision_metadata(
        message_id=email.message_id,
        action=decision.action,
        reason=decision.reason,
        intent=analysis.intent,
        urgency=analysis.urgency,
        requires_human=analysis.requires_human,
    )

    # 6. Load complete thread history
    thread = get_thread(email.thread_id)

    logger.info(
        "Thread history available: %d messages",
        len(thread),
    )

    reply = None

    # 7. Generate and save automatic reply
    if decision.action == "auto_reply":
        if _has_reply_for_email(
            message_id=email.message_id,
            thread_id=email.thread_id,
        ):
            logger.info(
                "Reply already exists for %s. Skipping duplicate reply.",
                email.message_id,
            )

            update_email_status(
                email.message_id,
                "auto_reply",
            )

        else:
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

            update_email_status(
                email.message_id,
                "auto_reply",
            )

            logger.info(
                "Email reply generated and saved successfully"
            )

    # 8. Human review or escalation
    elif decision.action in (
        "human_review",
        "escalate",
    ):
        update_email_status(
            email.message_id,
            decision.action,
        )

        logger.warning(
            "Email requires human intervention: %s",
            decision.reason,
        )

    # 9. Ignore
    elif decision.action == "ignore":
        update_email_status(
            email.message_id,
            "ignored",
        )

        logger.info(
            "Email ignored: %s",
            decision.reason,
        )

    return {
        "email": email,
        "analysis": analysis,
        "decision": decision,
        "action": decision.action,
        "thread": thread,
        "reply": reply,
    }


def process_unread_emails(
    connector: EmailConnector,
) -> list[Dict[str, Any]]:
    """
    Fetch unread emails from an email connector,
    process them through the agent, and mark successful
    emails as read.

    If one email fails, the error is recorded and the
    remaining emails continue processing.

    Failed emails are NOT marked as read so they can be
    retried later.
    """

    results: list[Dict[str, Any]] = []

    emails = connector.fetch_unread_emails()

    logger.info(
        "Found %d unread email(s)",
        len(emails),
    )

    for email in emails:
        raw_email = {
            "message_id": email.message_id,
            "thread_id": email.thread_id,
            "sender": email.sender,
            "recipient": email.recipient,
            "subject": email.subject,
            "body": email.body,
            "timestamp": email.timestamp,
            "attachments": email.attachments,
        }

        try:
            result = process_email(raw_email)

            result["message_id"] = email.message_id
            result["status"] = result["action"]

            results.append(result)

            connector.mark_as_read(
                email.message_id
            )

            logger.info(
                "Finished processing email %s",
                email.message_id,
            )

        except Exception as exc:
            logger.exception(
                "Failed to process email %s",
                email.message_id,
            )

            results.append(
                {
                    "message_id": email.message_id,
                    "status": "error",
                    "error": str(exc),
                }
            )

            # Do not mark failed emails as read.
            # They remain unread so they can be retried later.

            continue

    return results


def main() -> None:
    """Run a demo email through the agent."""

    init_email_db()

    raw_email = {
        "message_id": "demo-011",
        "thread_id": "demo-thread-011",
        "sender": "customer@example.com",
        "recipient": "support@example.com",
        "subject": "Order issue",
        "body": (
            "Hi, I placed my order five days ago "
            "and I still haven't received it. Can you help?"
        ),
        "timestamp": "2026-08-12T04:00:00",
        "attachments": [],
    }

    result = process_email(raw_email)

    print("\n" + "=" * 60)
    print("EMAIL AGENT RESULT")
    print("=" * 60)

    print(
        f"\nMessage ID: "
        f"{result['email'].message_id}"
    )

    print(
        f"Intent: "
        f"{result['analysis'].intent}"
    )

    print(
        f"Urgency: "
        f"{result['analysis'].urgency}"
    )

    print(
        f"Language: "
        f"{result['analysis'].language}"
    )

    print(
        f"Requires human: "
        f"{result['analysis'].requires_human}"
    )

    print(
        f"Action: "
        f"{result['action']}"
    )

    print(
        f"Thread messages: "
        f"{len(result['thread'])}"
    )

    if result["reply"]:
        print("\nReply:")
        print(result["reply"])

    print("=" * 60)


if __name__ == "__main__":
    main()