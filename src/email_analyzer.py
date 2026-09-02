"""
Email analyzer.

Classifies incoming emails before an AI response is generated.
This first version uses deterministic rules so the decision logic
can be tested independently from an LLM.
"""

from dataclasses import dataclass
import re

from src.email_models import Email


@dataclass
class EmailAnalysis:
    intent: str
    urgency: str
    language: str
    requires_human: bool
    reason: str


URGENT_WORDS = {
    "urgent",
    "immediately",
    "emergency",
    "critical",
    "asap",
}

HUMAN_REQUIRED_WORDS = {
    "refund",
    "chargeback",
    "legal",
    "lawyer",
    "fraud",
    "stolen",
    "account hacked",
}


def detect_language(text: str) -> str:
    """Basic language detection for the first version."""

    text_lower = text.lower()

    romanian_words = {
        "și",
        "sunt",
        "vreau",
        "comandă",
        "comanda",
        "refund",
        "unde",
        "când",
        "cand",
    }

    english_words = {
        "the",
        "is",
        "are",
        "where",
        "when",
        "order",
        "help",
        "please",
    }

    words = set(re.findall(r"\b\w+\b", text_lower))

    ro_score = len(words.intersection(romanian_words))
    en_score = len(words.intersection(english_words))

    if ro_score > en_score:
        return "ro"

    if en_score > ro_score:
        return "en"

    return "unknown"


def detect_intent(subject: str, body: str) -> str:
    """Determine the main reason for the email."""

    text = f"{subject} {body}".lower()

    if any(
        word in text
        for word in ("refund", "money back", "return")
    ):
        return "refund"

    if any(
        word in text
        for word in ("payment", "charged", "billing", "invoice")
    ):
        return "billing"

    if any(
        word in text
        for word in (
            "order",
            "delivery",
            "shipping",
            "package",
        )
    ):
        return "customer_support"

    if any(
        word in text
        for word in (
            "complaint",
            "unhappy",
            "terrible",
            "disappointed",
        )
    ):
        return "complaint"

    if any(
        word in text
        for word in (
            "price",
            "pricing",
            "buy",
            "purchase",
        )
    ):
        return "sales"

    return "general"


def analyze_email(email: Email) -> EmailAnalysis:
    """Analyze an incoming email."""

    text = f"{email.subject} {email.body}".lower()

    intent = detect_intent(
        email.subject,
        email.body,
    )

    language = detect_language(email.body)

    is_urgent = any(
        word in text
        for word in URGENT_WORDS
    )

    requires_human = any(
        word in text
        for word in HUMAN_REQUIRED_WORDS
    )

    if requires_human:
        urgency = "high"
        reason = (
            "The email contains an issue that should "
            "be reviewed by a human."
        )

    elif is_urgent:
        urgency = "high"
        reason = (
            "The customer explicitly indicates urgency."
        )

    else:
        urgency = "normal"
        reason = (
            "The email can initially be handled automatically."
        )

    return EmailAnalysis(
        intent=intent,
        urgency=urgency,
        language=language,
        requires_human=requires_human,
        reason=reason,
    )