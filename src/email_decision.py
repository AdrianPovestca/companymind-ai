"""
Decision engine for the AI email support agent.

Takes the result of email analysis and decides what the agent
should do next.
"""

from dataclasses import dataclass


@dataclass
class EmailDecision:
    action: str
    reason: str


def decide_action(
    intent: str,
    urgency: str,
    requires_human: bool,
) -> EmailDecision:
    """
    Decide what action should be taken for an analyzed email.

    Possible actions:
    - auto_reply
    - human_review
    - escalate
    - ignore
    """

    # Urgent emails should always be reviewed by a human.
    if urgency == "urgent":
        return EmailDecision(
            action="escalate",
            reason="Email is marked as urgent.",
        )

    # The AI analyzer can explicitly require human intervention.
    if requires_human:
        return EmailDecision(
            action="human_review",
            reason="Email analysis requires human intervention.",
        )

    # Spam and irrelevant messages do not need a reply.
    if intent in ("spam", "irrelevant"):
        return EmailDecision(
            action="ignore",
            reason=f"Email intent is {intent}.",
        )

    # Normal customer support requests can be handled automatically.
    if intent == "customer_support":
        return EmailDecision(
            action="auto_reply",
            reason="Normal customer support request can be handled automatically.",
        )

    # Unknown cases should never be answered automatically.
    return EmailDecision(
        action="human_review",
        reason="Email intent is not recognized.",
    )