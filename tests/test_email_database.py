import src.email_database as email_database
from src.email_models import Email


def test_database_operations(tmp_path, monkeypatch):
    db_path = tmp_path / "test_emails.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    email = Email(
        message_id="test-db-001",
        thread_id="thread-db-001",
        sender="customer@example.com",
        recipient="support@example.com",
        subject="Order issue",
        body="Where is my order?",
    )

    email_database.save_email(email)

    saved = email_database.get_email("test-db-001")

    assert saved is not None
    assert saved["message_id"] == "test-db-001"
    assert saved["thread_id"] == "thread-db-001"
    assert saved["status"] == "new"


def test_decision_metadata(tmp_path, monkeypatch):
    db_path = tmp_path / "test_emails.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    email = Email(
        message_id="test-db-002",
        thread_id="thread-db-002",
        sender="customer@example.com",
        recipient="support@example.com",
        subject="Refund",
        body="I want a refund.",
    )

    email_database.save_email(email)

    email_database.save_decision_metadata(
        message_id="test-db-002",
        action="human_review",
        reason="Refund requires human review.",
        intent="refund",
        urgency="high",
        requires_human=True,
    )

    metadata = email_database.get_decision_metadata(
        "test-db-002"
    )

    assert metadata["decision_action"] == "human_review"
    assert metadata["decision_intent"] == "refund"
    assert metadata["decision_urgency"] == "high"
    assert metadata["requires_human"] == 1
    assert metadata["human_review_status"] == "pending"


def test_save_reply(tmp_path, monkeypatch):
    db_path = tmp_path / "test_emails.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    email_database.save_reply(
        message_id="test-db-003",
        thread_id="thread-db-003",
        recipient="customer@example.com",
        subject="Re: Order issue",
        body="We are checking your order.",
    )

    replies = email_database.get_replies_for_thread(
        "thread-db-003"
    )

    assert len(replies) == 1
    assert replies[0]["thread_id"] == "thread-db-003"
    assert replies[0]["recipient"] == "customer@example.com"
    assert replies[0]["body"] == "We are checking your order."


def test_human_review(tmp_path, monkeypatch):
    db_path = tmp_path / "test_emails.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    email = Email(
        message_id="test-db-004",
        thread_id="thread-db-004",
        sender="customer@example.com",
        recipient="support@example.com",
        subject="Refund",
        body="I want a refund.",
    )

    email_database.save_email(email)

    email_database.save_decision_metadata(
        message_id="test-db-004",
        action="human_review",
        reason="Refund requires review.",
        intent="refund",
        urgency="high",
        requires_human=True,
    )

    email_database.review_email(
        message_id="test-db-004",
        review_status="approved",
        note="Refund approved.",
    )

    metadata = email_database.get_decision_metadata(
        "test-db-004"
    )

    assert metadata["human_review_status"] == "approved"
    assert metadata["human_review_note"] == "Refund approved."
    assert metadata["reviewed_at"] is not None
