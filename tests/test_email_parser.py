from src.email_analyzer import analyze_email
from src.email_models import Email


def make_email(subject: str, body: str) -> Email:
    return Email(
        message_id="test-001",
        thread_id="thread-001",
        sender="customer@example.com",
        recipient="support@example.com",
        subject=subject,
        body=body,
    )


def test_customer_support_email():
    email = make_email(
        "Order issue",
        "Where is my order?",
    )

    analysis = analyze_email(email)

    assert analysis.intent == "customer_support"
    assert analysis.urgency == "normal"
    assert analysis.requires_human is False


def test_refund_requires_human():
    email = make_email(
        "Refund request",
        "I want a refund for my order.",
    )

    analysis = analyze_email(email)

    assert analysis.intent == "refund"
    assert analysis.urgency == "high"
    assert analysis.requires_human is True


def test_urgent_email():
    email = make_email(
        "URGENT order problem",
        "I need help immediately.",
    )

    analysis = analyze_email(email)

    assert analysis.intent == "customer_support"
    assert analysis.urgency == "high"
    