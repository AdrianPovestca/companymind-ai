import src.email_database as email_database

from src.email_agent import process_unread_emails
from src.email_connector import MockEmailConnector
from src.email_models import Email


def make_email(
    message_id: str,
    subject: str,
    body: str,
) -> Email:
    return Email(
        message_id=message_id,
        thread_id=f"thread-{message_id}",
        sender="customer@example.com",
        recipient="support@example.com",
        subject=subject,
        body=body,
    )


def test_failed_email_does_not_stop_other_emails(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "runner-errors.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    emails = [
        make_email(
            "error-001",
            "Broken email",
            "This email should fail.",
        ),
        make_email(
            "error-002",
            "Order issue",
            "Where is my order?",
        ),
    ]

    connector = MockEmailConnector(emails)

    original_process_email = process_unread_emails.__globals__[
        "process_email"
    ]

    def failing_process_email(raw_email):
        if raw_email["message_id"] == "error-001":
            raise RuntimeError(
                "Simulated processing failure"
            )

        return original_process_email(raw_email)

    monkeypatch.setitem(
        process_unread_emails.__globals__,
        "process_email",
        failing_process_email,
    )

    results = process_unread_emails(connector)

    assert len(results) == 2

    assert results[0]["message_id"] == "error-001"
    assert results[0]["status"] == "error"

    assert results[1]["message_id"] == "error-002"
    assert results[1]["action"] == "auto_reply"

    unread = connector.fetch_unread_emails()

    assert len(unread) == 1
    assert unread[0].message_id == "error-001"