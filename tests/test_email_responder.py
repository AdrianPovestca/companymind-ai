from src.email_models import Email
from src.email_analyzer import EmailAnalysis
from src.email_responder import generate_reply, _extract_order_number


def make_email(subject: str, body: str) -> Email:
    return Email(
        message_id="test-001",
        thread_id="thread-001",
        sender="customer@example.com",
        recipient="support@example.com",
        subject=subject,
        body=body,
    )


def test_extract_order_number():
    assert _extract_order_number("My order number is 12345") == "12345"
    assert _extract_order_number("Order #98765") == "98765"
    assert _extract_order_number("I have order 45678") == "45678"
    assert _extract_order_number("Hello, I need help") is None


def test_customer_support_reply():
    email = make_email(
        "Order issue",
        "My order has not arrived yet.",
    )

    analysis = EmailAnalysis(
        intent="customer_support",
        urgency="normal",
        language="en",
        requires_human=False,
        reason="Normal request.",
    )

    reply = generate_reply(
        email=email,
        analysis=analysis,
        thread=[{
            "message_id": "test-001",
            "message_type": "email",
            "sender": "customer@example.com",
            "body": email.body,
        }],
    )

    assert "Thanks for reaching out" in reply
    assert "order and shipping status" in reply


def test_order_number_reply():
    email = make_email(
        "Order issue",
        "My order number is 12345. Can you check it?",
    )

    analysis = EmailAnalysis(
        intent="customer_support",
        urgency="normal",
        language="en",
        requires_human=False,
        reason="Normal request.",
    )

    reply = generate_reply(
        email=email,
        analysis=analysis,
        thread=[{
            "message_id": "test-001",
            "message_type": "email",
            "sender": "customer@example.com",
            "body": email.body,
        }],
    )

    assert "12345" in reply
    assert "order number" in reply


def test_human_review_reply():
    email = make_email(
        "Refund request",
        "I want a refund.",
    )

    analysis = EmailAnalysis(
        intent="refund",
        urgency="high",
        language="en",
        requires_human=True,
        reason="Human review required.",
    )

    reply = generate_reply(
        email=email,
        analysis=analysis,
        thread=[{
            "message_id": "test-001",
            "message_type": "email",
            "sender": "customer@example.com",
            "body": email.body,
        }],
    )

    assert "forwarded your request" in reply
    assert "support team" in reply
