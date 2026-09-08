import src.email_database as email_database

from src.email_agent import process_email


def test_process_email_auto_reply(tmp_path, monkeypatch):
    db_path = tmp_path / "test_agent.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    raw_email = {
        "message_id": "agent-test-001",
        "thread_id": "agent-thread-001",
        "sender": "customer@example.com",
        "recipient": "support@example.com",
        "subject": "Order issue",
        "body": "Where is my order?",
        "timestamp": "2026-08-14T04:00:00",
        "attachments": [],
    }

    result = process_email(raw_email)

    assert result["action"] == "auto_reply"
    assert result["reply"] is not None
    assert "order status" in result["reply"]

    saved_email = email_database.get_email(
        "agent-test-001"
    )

    assert saved_email is not None
    assert saved_email["status"] == "auto_reply"

    replies = email_database.get_replies_for_thread(
        "agent-thread-001"
    )

    assert len(replies) == 1
    assert replies[0]["body"] == result["reply"]


def test_process_email_human_review(tmp_path, monkeypatch):
    db_path = tmp_path / "test_agent.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    raw_email = {
        "message_id": "agent-test-002",
        "thread_id": "agent-thread-002",
        "sender": "customer@example.com",
        "recipient": "support@example.com",
        "subject": "Refund request",
        "body": "I want a refund.",
        "timestamp": "2026-08-14T04:00:00",
        "attachments": [],
    }

    result = process_email(raw_email)

    assert result["action"] == "human_review"
    assert result["reply"] is None

    saved_email = email_database.get_email(
        "agent-test-002"
    )

    assert saved_email is not None
    assert saved_email["status"] == "human_review"

    replies = email_database.get_replies_for_thread(
        "agent-thread-002"
    )

    assert len(replies) == 0


def test_process_email_does_not_create_duplicate_reply(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "test_agent.db"

    monkeypatch.setattr(
        email_database,
        "DB_PATH",
        db_path,
    )

    raw_email = {
        "message_id": "agent-test-004",
        "thread_id": "agent-thread-004",
        "sender": "customer@example.com",
        "recipient": "support@example.com",
        "subject": "Order issue",
        "body": "Where is my order?",
        "timestamp": "2026-08-14T04:00:00",
        "attachments": [],
    }

    first_result = process_email(raw_email)

    assert first_result["action"] == "auto_reply"
    assert first_result["reply"] is not None

    second_result = process_email(raw_email)

    assert second_result["action"] == "auto_reply"
    assert second_result["reply"] is None

    replies = email_database.get_replies_for_thread(
        "agent-thread-004"
    )

    assert len(replies) == 1