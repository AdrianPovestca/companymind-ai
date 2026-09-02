from src.email_connector import MockEmailConnector
from src.email_models import Email


def make_email(message_id: str) -> Email:
    return Email(
        message_id=message_id,
        thread_id=f"thread-{message_id}",
        sender="customer@example.com",
        recipient="support@example.com",
        subject="Order issue",
        body="Where is my order?",
    )


def test_fetch_unread_emails():
    emails = [
        make_email("connector-001"),
        make_email("connector-002"),
    ]

    connector = MockEmailConnector(emails)

    unread = connector.fetch_unread_emails()

    assert len(unread) == 2
    assert unread[0].message_id == "connector-001"
    assert unread[1].message_id == "connector-002"


def test_mark_as_read_removes_email_from_unread():
    emails = [
        make_email("connector-001"),
        make_email("connector-002"),
    ]

    connector = MockEmailConnector(emails)

    connector.mark_as_read("connector-001")

    unread = connector.fetch_unread_emails()

    assert len(unread) == 1
    assert unread[0].message_id == "connector-002"


def test_mark_as_read_is_idempotent():
    email = make_email("connector-001")

    connector = MockEmailConnector([email])

    connector.mark_as_read("connector-001")
    connector.mark_as_read("connector-001")

    unread = connector.fetch_unread_emails()

    assert unread == []


def test_empty_connector_returns_no_emails():
    connector = MockEmailConnector()

    assert connector.fetch_unread_emails() == []