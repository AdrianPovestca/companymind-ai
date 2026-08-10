"""
Email response generator.

Creates a safe draft response from the email, thread history,
and available knowledge base context.
"""

import logging
from typing import List, Dict

from src.email_models import Email


logger = logging.getLogger(__name__)


def build_email_context(
    email: Email,
    thread: List[Dict],
    knowledge_results: List[Dict],
) -> str:
    """Build the context that will later be sent to the AI model."""

    parts = []

    parts.append(
        f"Current email:\n"
        f"From: {email.sender}\n"
        f"Subject: {email.subject}\n"
        f"Message: {email.body}"
    )

    if thread:
        history_lines = []

        for message in thread:
            history_lines.append(
                f"{message['sender']}: {message['body']}"
            )

        parts.append(
            "Previous conversation:\n"
            + "\n".join(history_lines)
        )

    if knowledge_results:
        knowledge_lines = []

        for result in knowledge_results:
            document = result["document"]
            knowledge_lines.append(
                f"Source: {document.filename}\n"
                f"{document.content}"
            )

        parts.append(
            "Knowledge base:\n"
            + "\n\n".join(knowledge_lines)
        )

    return "\n\n".join(parts)


def generate_email_reply(
    email: Email,
    thread: List[Dict],
    knowledge_results: List[Dict],
) -> str:
    """
    Generate a safe email reply draft.

    This first version does not call an LLM.
    It creates a controlled draft so the pipeline can be tested
    before AI generation is introduced.
    """

    if not knowledge_results:
        return (
            "Hi,\n\n"
            "Thanks for reaching out. I’m sorry, but I don’t have "
            "enough information to give you an accurate answer yet. "
            "I’ll make sure this is reviewed by our support team.\n\n"
            "Best,\n"
            "Support Team"
        )

    document = knowledge_results[0]["document"]

    return (
        "Hi,\n\n"
        "Thanks for reaching out. Based on our support information:\n\n"
        f"{document.content.strip()}\n\n"
        "If you need any further help, please let us know.\n\n"
        "Best,\n"
        "Support Team"
    )