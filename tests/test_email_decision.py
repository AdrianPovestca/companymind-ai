from src.email_decision import decide_action


def test_normal_customer_support_auto_reply():
    decision = decide_action(
        "customer_support",
        "normal",
        False,
    )

    assert decision.action == "auto_reply"


def test_high_urgency_escalates():
    decision = decide_action(
        "customer_support",
        "high",
        False,
    )

    assert decision.action == "escalate"


def test_human_required_goes_to_review():
    decision = decide_action(
        "refund",
        "high",
        True,
    )

    assert decision.action == "human_review"


def test_unknown_intent_goes_to_review():
    decision = decide_action(
        "unknown",
        "normal",
        False,
    )

    assert decision.action == "human_review"


def test_irrelevant_email_is_ignored():
    decision = decide_action(
        "irrelevant",
        "normal",
        False,
    )

    assert decision.action == "ignore"
