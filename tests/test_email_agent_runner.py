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
        timestamp="2026-08-14T04:00:00",
        attachments=[],
    )


def test_process_unread_emails_auto_reply(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "runner.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    email = make_email(
        "runner-001",
        "Order issue",
        "Where is my order?",
    )

    connector = MockEmailConnector([email])

    results = process_unread_emails(connector)

    assert len(results) == 1
    assert results[0]["action"] == "auto_reply"
    assert results[0]["reply"] is not None

    saved = email_database.get_email(
        "runner-001"
    )

    assert saved is not None
    assert saved["status"] == "auto_reply"

    assert connector.fetch_unread_emails() == []


def test_process_unread_emails_human_review(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "runner.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    email = make_email(
        "runner-002",
        "Refund request",
        "I want a refund.",
    )

    connector = MockEmailConnector([email])

    results = process_unread_emails(connector)

    assert len(results) == 1
    assert results[0]["action"] == "human_review"
    assert results[0]["reply"] is None

    saved = email_database.get_email(
        "runner-002"
    )

    assert saved is not None
    assert saved["status"] == "human_review"

    assert connector.fetch_unread_emails() == []


def test_process_unread_emails_multiple_messages(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "runner.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    emails = [
        make_email(
            "runner-003",
            "Order issue",
            "Where is my order?",
        ),
        make_email(
            "runner-004",
            "Refund request",
            "I want a refund.",
        ),
    ]

    connector = MockEmailConnector(emails)

    results = process_unread_emails(connector)

    assert len(results) == 2

    assert results[0]["action"] == "auto_reply"
    assert results[1]["action"] == "human_review"

    assert connector.fetch_unread_emails() == []