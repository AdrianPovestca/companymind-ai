"""
Email responder.

Generates deterministic customer-facing replies based on
email analysis and thread history.
"""

import re
from typing import Any, Dict, List, Optional

from src.email_models import Email


def _extract_order_number(text: str) -> Optional[str]:
    """
    Extract a numeric order number from an email body.

    Supported examples:
    - Order 12345
    - Order #12345
    - Order number 12345
    - Order no. 12345
    - My order number is 12345
    """
    if not text:
        return None

    patterns = (
        r"\border\s*(?:number|no\.?|#)?\s*[:#-]?\s*(\d{4,})\b",
        r"\bmy\s+order\s+number\s+is\s+(\d{4,})\b",
        r"\border\s+number\s+is\s+(\d{4,})\b",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return None


def _get_previous_messages(
    email: Email,
    thread: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Return previous thread messages while excluding
    the current incoming email.
    """
    previous_messages: List[Dict[str, Any]] = []

    for message in thread:
        if not isinstance(message, dict):
            continue

        is_current_email = (
            message.get("message_id") == email.message_id
            and message.get("message_type", "email") == "email"
            and message.get("sender") == email.sender
            and message.get("body") == email.body
        )

        if not is_current_email:
            previous_messages.append(message)

    return previous_messages


def _has_previous_reply(
    previous_messages: List[Dict[str, Any]],
) -> bool:
    """Return True when support has already replied in the thread."""
    return any(
        message.get("message_type") == "reply"
        or message.get("sender") == "support"
        for message in previous_messages
    )


def _get_language(analysis: Any) -> str:
    """Safely return the detected language."""
    language = getattr(analysis, "language", "unknown")

    if not isinstance(language, str):
        return "unknown"

    return language.lower().strip()


def _get_intent(analysis: Any) -> str:
    """Safely return the detected intent."""
    intent = getattr(analysis, "intent", "general")

    if not isinstance(intent, str):
        return "general"

    return intent.lower().strip()


def _requires_human(analysis: Any) -> bool:
    """Safely return the human-review requirement."""
    return bool(
        getattr(
            analysis,
            "requires_human",
            False,
        )
    )


def _english_human_review_reply() -> str:
    """Return the standard English human-review response."""
    return (
        "Hi,\n\n"
        "Thanks for reaching out. I've forwarded your request "
        "to our support team, and someone will get back to you "
        "as soon as possible.\n\n"
        "Best,\n"
        "Support Team"
    )


def _romanian_human_review_reply() -> str:
    """Return the standard Romanian human-review response."""
    return (
        "Bună,\n\n"
        "Mulțumesc că ne-ai contactat. Am transmis solicitarea "
        "ta către echipa noastră de suport, iar cineva va reveni "
        "către tine cât mai curând posibil.\n\n"
        "Cu bine,\n"
        "Echipa Support"
    )


def generate_reply(
    email: Email,
    analysis: Any,
    thread: List[Dict[str, Any]],
) -> str:
    """
    Generate a deterministic customer-facing reply.

    The function does not call an external LLM or network service.
    Human-review cases are handled before automatic response logic.
    """
    if email is None:
        raise ValueError("email cannot be None.")

    if analysis is None:
        raise ValueError("analysis cannot be None.")

    if thread is None:
        thread = []

    previous_messages = _get_previous_messages(
        email=email,
        thread=thread,
    )

    order_number = _extract_order_number(
        email.body or ""
    )

    has_previous_reply = _has_previous_reply(
        previous_messages
    )

    language = _get_language(analysis)
    intent = _get_intent(analysis)
    requires_human = _requires_human(analysis)

    if requires_human:
        if language == "ro":
            return _romanian_human_review_reply()

        return _english_human_review_reply()

    if language == "ro":
        if intent == "refund":
            return (
                "Bună,\n\n"
                "Mulțumesc că ne-ai contactat. Am primit solicitarea "
                "ta și vom verifica situația plății și a rambursării.\n\n"
                "Revenim cu o actualizare cât mai curând.\n\n"
                "Cu bine,\n"
                "Echipa Support"
            )

        if intent == "billing":
            return (
                "Bună,\n\n"
                "Mulțumesc că ne-ai contactat. Vom verifica situația "
                "plății și detaliile tranzacției.\n\n"
                "Revenim cu o actualizare cât mai curând.\n\n"
                "Cu bine,\n"
                "Echipa Support"
            )

        if order_number:
            return (
                "Bună,\n\n"
                f"Mulțumesc pentru numărul comenzii, {order_number}.\n"
                "Vom verifica statusul comenzii și al livrării și "
                "vom reveni cu o actualizare.\n\n"
                "Cu bine,\n"
                "Echipa Support"
            )

        if intent == "customer_support":
            if has_previous_reply:
                return (
                    "Bună,\n\n"
                    "Mulțumesc pentru informațiile suplimentare. "
                    "Le-am adăugat solicitării tale și vom continua "
                    "verificarea situației comenzii și livrării.\n\n"
                    "Revenim cu o actualizare cât mai curând.\n\n"
                    "Cu bine,\n"
                    "Echipa Support"
                )

            return (
                "Bună,\n\n"
                "Mulțumesc că ne-ai contactat. Ne pare rău pentru "
                "problema întâmpinată.\n\n"
                "Vom verifica situația și vom reveni cu o actualizare.\n\n"
                "Cu bine,\n"
                "Echipa Support"
            )

        return (
            "Bună,\n\n"
            "Mulțumim că ne-ai contactat. Am primit mesajul tău și "
            "vom reveni cu un răspuns cât mai curând.\n\n"
            "Cu bine,\n"
            "Echipa Support"
        )

    if intent == "refund":
        return (
            "Hi,\n\n"
            "Thanks for reaching out. We’ve received your refund "
            "request and will review the payment details.\n\n"
            "We’ll get back to you with an update as soon as possible.\n\n"
            "Best,\n"
            "Support Team"
        )

    if intent == "billing":
        return (
            "Hi,\n\n"
            "Thanks for reaching out. We’ll review the billing and "
            "payment details and get back to you with an update.\n\n"
            "Best,\n"
            "Support Team"
        )

    if intent == "complaint":
        return (
            "Hi,\n\n"
            "Thanks for letting us know. I’m sorry to hear about "
            "your experience.\n\n"
            "We’ll review the issue and get back to you with an update.\n\n"
            "Best,\n"
            "Support Team"
        )

    if intent == "sales":
        return (
            "Hi,\n\n"
            "Thanks for reaching out. We’ve received your question "
            "and will get back to you with more information shortly.\n\n"
            "Best,\n"
            "Support Team"
        )

    if order_number:
        return (
            "Hi,\n\n"
            f"Thanks for providing your order number, {order_number}.\n"
            "We’ll check the order and shipping status and get back "
            "to you with an update.\n\n"
            "Best,\n"
            "Support Team"
        )

    if intent == "customer_support":
        if has_previous_reply:
            return (
                "Hi,\n\n"
                "Thanks for the additional information. We’ve added "
                "it to your request and will continue checking the "
                "order and shipping status.\n\n"
                "We’ll get back to you with an update as soon as possible.\n\n"
                "Best,\n"
                "Support Team"
            )

        return (
            "Hi,\n\n"
            "Thanks for reaching out. I’m sorry to hear that your "
            "order hasn’t arrived yet.\n\n"
            "We’ll check the order and shipping status and get back "
            "to you with an update.\n\n"
            "Best,\n"
            "Support Team"
        )

    return (
        "Hi,\n\n"
        "Thanks for reaching out. We’ve received your message and "
        "will get back to you shortly.\n\n"
        "Best,\n"
        "Support Team"
    )